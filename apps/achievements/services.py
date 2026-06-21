import datetime
from django.db.models import Count
from django.utils import timezone
from apps.achievements.models import Achievement
from apps.academics.models import Session
from apps.students.models import Enrollment

def get_success_metrics():
    now = timezone.now()
    current_year = now.year

    total_selections = Achievement.objects.count()
    selections_this_year = Achievement.objects.filter(year=current_year).count()

    # Success rate per session
    sessions_metrics = []
    active_sessions = list(Session.objects.filter(status="Active"))
    active_session_ids = [s.id for s in active_sessions]

    # Fetch all active enrollments for active sessions
    enrollments = Enrollment.objects.filter(session_id__in=active_session_ids).values('session_id', 'student_id')
    from collections import defaultdict
    session_students = defaultdict(set)
    for e in enrollments:
        session_students[e['session_id']].add(e['student_id'])

    # Get achievements for students in active sessions
    all_student_ids = {e['student_id'] for e in enrollments}
    achieved_student_ids = set(
        Achievement.objects.filter(student_id__in=all_student_ids).values_list('student_id', flat=True).distinct()
    )

    for session in active_sessions:
        student_ids = session_students[session.id]
        total_students = len(student_ids)
        if total_students > 0:
            success_count = len(student_ids.intersection(achieved_student_ids))
            success_rate = (success_count / total_students) * 100
        else:
            success_count = 0
            success_rate = 0.0

        sessions_metrics.append({
            'session_id': session.id,
            'session_name': session.name,
            'total_students': total_students,
            'success_count': success_count,
            'success_rate': round(success_rate, 2)
        })

    # Success rate per exam_type (distribution)
    exam_type_counts = Achievement.objects.values('exam_type').annotate(count=Count('id')).order_by('-count')
    exam_metrics = []
    for item in exam_type_counts:
        pct = (item['count'] / total_selections * 100) if total_selections > 0 else 0
        exam_metrics.append({
            'exam_type': item['exam_type'],
            'count': item['count'],
            'percentage': round(pct, 2)
        })

    # Top 5 students (recent selections)
    recent_selections = []
    recent_achievements = list(Achievement.objects.select_related('student').order_by('-created_at')[:5])
    recent_student_ids = [ach.student_id for ach in recent_achievements]

    # Bulk fetch active enrollments for these top students
    active_enrollments = {
        e.student_id: e
        for e in Enrollment.objects.filter(student_id__in=recent_student_ids, status="Active").select_related('session')
    }

    for ach in recent_achievements:
        enrollment = active_enrollments.get(ach.student_id)
        session_name = enrollment.session.name if enrollment else "No Active Session"
        recent_selections.append({
            'student_name': ach.student.full_name,
            'roll_number': ach.student.roll_number or "No Roll#",
            'session_name': session_name,
            'exam_type': ach.exam_type,
            'year': ach.year,
            'rank': ach.rank,
            'created_at': ach.created_at,
        })

    # Selections by year (for line chart)
    selections_by_year = list(Achievement.objects.values('year').annotate(count=Count('id')).order_by('year'))

    return {
        'total_selections': total_selections,
        'selections_this_year': selections_this_year,
        'sessions_metrics': sessions_metrics,
        'exam_metrics': exam_metrics,
        'recent_selections': recent_selections,
        'selections_by_year': selections_by_year,
    }
