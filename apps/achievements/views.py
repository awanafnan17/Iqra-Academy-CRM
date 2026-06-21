from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import RoleRequiredMixin
from apps.achievements.services import get_success_metrics
from apps.achievements.models import Achievement

class SuccessDashboardView(RoleRequiredMixin, View):
    """Admin success dashboard showing selections metrics, trends, and details."""
    required_roles = ["Admin", "Principal"]
    template_name = "dashboard/success_dashboard.html"

    def get(self, request, *args, **kwargs):
        metrics = get_success_metrics()
        context = {
            "metrics": metrics,
            "role": "Admin",
        }
        return render(request, self.template_name, context)


class PublicSuccessStoriesView(View):
    """Public page for displaying verified student selections with filter controls."""
    template_name = "public/success_stories.html"

    def get(self, request, *args, **kwargs):
        achievements = Achievement.objects.filter(is_public=True).select_related("student").order_by("-year", "exam_type")

        # Get distinct values for filter controls
        exam_types = Achievement.objects.filter(is_public=True).values_list("exam_type", flat=True).distinct().order_by("exam_type")
        years = Achievement.objects.filter(is_public=True).values_list("year", flat=True).distinct().order_by("-year")

        selected_exam_type = request.GET.get("exam_type")
        selected_year = request.GET.get("year")

        if selected_exam_type:
            achievements = achievements.filter(exam_type=selected_exam_type)
        if selected_year:
            try:
                achievements = achievements.filter(year=int(selected_year))
            except ValueError:
                pass

        # Prefetch enrollment session to avoid N+1 query overhead
        from apps.students.models import Enrollment
        achievements_data = []
        for ach in achievements:
            enrollment = Enrollment.objects.filter(student=ach.student, status="Active").select_related("session").first()
            session_name = enrollment.session.name if enrollment else "No Active Session"
            achievements_data.append({
                "achievement": ach,
                "session_name": session_name,
            })

        context = {
            "achievements_data": achievements_data,
            "exam_types": exam_types,
            "years": years,
            "selected_exam_type": selected_exam_type,
            "selected_year": selected_year,
        }
        return render(request, self.template_name, context)
