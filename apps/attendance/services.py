"""
Attendance service layer - handles marking daily attendance, lock control, and analytics.

All write operations run inside transaction.atomic() with model-level validation checking.
"""

import datetime
import logging
from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q, Case, When, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from apps.core.services import (
    BaseService,
    transactional_service,
    NotFoundError,
    BusinessRuleViolation,
)
from apps.attendance.models import AttendanceRecord, AttendanceLock
from apps.students.models import Enrollment
from apps.academics.models import Session

logger = logging.getLogger("crm.attendance")


class AttendanceService(BaseService):
    """Orchestrates daily attendance marking, retroactive change locks, and student percentages."""

    @classmethod
    def is_date_locked(cls, session_id, date):
        """Checks if attendance has been locked for the given session and date."""
        return AttendanceLock.objects.filter(session_id=session_id, date=date).exists()

    @classmethod
    def _verify_attendance_rules(cls, session_id, date):
        """Helper to check future dates, 30-day deadlines, and active locks."""
        today = timezone.localdate()

        # Rule 1: No future dates
        if date > today:
            raise BusinessRuleViolation("Cannot record or modify attendance for future dates.")

        # Rule 2: No attendance older than 30 days
        limit_date = today - datetime.timedelta(days=30)
        if date < limit_date:
            raise BusinessRuleViolation("Cannot record or modify attendance older than 30 days.")

        # Rule 3: Must not be locked
        if cls.is_date_locked(session_id, date):
            raise BusinessRuleViolation(
                f"Attendance for session ID {session_id} on {date} has been locked and cannot be edited."
            )

    @classmethod
    @transactional_service
    def mark_attendance(cls, session_id, student_id, date, status, user, remarks=None, ip_address=None):
        """Marks daily attendance for a student, validating lock constraints."""
        cls._verify_attendance_rules(session_id, date)

        # Enforce that the student must have an active enrollment in this session
        is_active_enrollment = Enrollment.objects.filter(
            student_id=student_id,
            session_id=session_id,
            status="Active",
        ).exists()

        if not is_active_enrollment:
            raise BusinessRuleViolation(
                f"Cannot mark attendance. Student ID {student_id} is not actively enrolled in session ID {session_id}."
            )

        # Retrieve or instantiate duplicate safe record
        record, created = AttendanceRecord.objects.get_or_create(
            session_id=session_id,
            student_id=student_id,
            date=date,
            defaults={"status": status, "marked_by": user, "remarks": remarks},
        )

        if not created:
            # Update existing status
            old_status = record.status
            record.status = status
            record.marked_by = user
            record.remarks = remarks
            cls.validate_instance(record)
            record.save()

            cls.audit_on_commit(
                user=user,
                action="update",
                model_name="attendance.AttendanceRecord",
                object_id=record.pk,
                changes={"status": {"old": old_status, "new": status}},
                ip_address=ip_address,
            )
        else:
            cls.validate_instance(record)
            cls.audit_on_commit(
                user=user,
                action="create",
                model_name="attendance.AttendanceRecord",
                object_id=record.pk,
                changes={"status": status},
                ip_address=ip_address,
            )

        cls.log_structured(
            logging.INFO, "mark_attendance", "SUCCESS",
            f"Marked student {student_id} as {status} on {date}",
            f"record_id={record.pk}"
        )
        return record

    @classmethod
    @transactional_service
    def edit_attendance(cls, record_id, status, user, remarks=None, ip_address=None):
        """Modifies an existing attendance record status if lock boundaries allow."""
        record = AttendanceRecord.objects.filter(pk=record_id).first()
        if not record:
            raise NotFoundError(f"Attendance record with ID {record_id} not found.")

        cls._verify_attendance_rules(record.session_id, record.date)

        old_status = record.status
        record.status = status
        record.remarks = remarks
        record.marked_by = user
        cls.validate_instance(record)
        record.save()

        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="attendance.AttendanceRecord",
            object_id=record.pk,
            changes={"status": {"old": old_status, "new": status}},
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "edit_attendance", "SUCCESS",
            f"Updated attendance record ID {record_id} to status {status}",
            f"user={user}"
        )
        return record

    @classmethod
    @transactional_service
    def lock_attendance_for_date(cls, session_id, date, user, reason=None, ip_address=None):
        """Locks attendance modifications for a specific session date."""
        session = Session.objects.filter(pk=session_id).first()
        if not session:
            raise NotFoundError(f"Session with ID {session_id} not found.")

        # Ensure no future lock
        today = timezone.localdate()
        if date > today:
            raise BusinessRuleViolation("Cannot lock attendance for future dates.")

        lock, created = AttendanceLock.objects.get_or_create(
            session=session,
            date=date,
            defaults={"locked_by": user, "reason": reason},
        )

        if not created:
            raise BusinessRuleViolation(f"Attendance for session ID {session_id} on {date} is already locked.")

        cls.validate_instance(lock)
        cls.audit_on_commit(
            user=user,
            action="create",
            model_name="attendance.AttendanceLock",
            object_id=lock.pk,
            changes={"session_id": session_id, "date": str(date)},
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "lock_attendance_for_date", "SUCCESS",
            f"Locked attendance for session {session_id} on {date}",
            f"lock_id={lock.pk}"
        )
        return lock

    @classmethod
    @transactional_service
    def unlock_attendance_for_date(cls, session_id, date, user, ip_address=None):
        """Unlocks attendance modifications for a specific session date."""
        lock = AttendanceLock.objects.filter(session_id=session_id, date=date).first()
        if not lock:
            raise NotFoundError(f"No attendance lock found for session ID {session_id} on date {date}.")

        lock_id = lock.pk
        lock.delete()

        cls.audit_on_commit(
            user=user,
            action="delete",
            model_name="attendance.AttendanceLock",
            object_id=lock_id,
            changes={"session_id": session_id, "date": str(date)},
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "unlock_attendance_for_date", "SUCCESS",
            f"Unlocked attendance for session {session_id} on {date}",
            f"deleted_lock_id={lock_id}"
        )

    @classmethod
    def calculate_attendance_percentage(cls, student_id, session_id):
        """Calculates attendance percentage for a student in a session.

        Late or Present count as attended. Excused is excluded from metrics.
        """
        records = AttendanceRecord.objects.filter(student_id=student_id, session_id=session_id)

        # Aggregate counts at DB level
        aggregation = records.aggregate(
            attended=Count(
                "id",
                filter=Q(status__in=["Present", "Late"]),
            ),
            total_eligible=Count(
                "id",
                filter=Q(status__in=["Present", "Absent", "Late"]),
            ),
        )

        attended = aggregation["attended"] or 0
        total = aggregation["total_eligible"] or 0

        if total == 0:
            return Decimal("100.00")

        percentage = (Decimal(attended) / Decimal(total)) * Decimal("100.00")
        return percentage.quantize(Decimal("0.01"))

    @classmethod
    def get_attendance_analytics(cls, session_id, start_date=None, end_date=None):
        """Generates statistical attendance data metrics for a specific session."""
        records = AttendanceRecord.objects.filter(session_id=session_id)
        if start_date:
            records = records.filter(date__gte=start_date)
        if end_date:
            records = records.filter(date__lte=end_date)

        # Retrieve count of Present, Absent, Late, Excused across records
        counts = records.aggregate(
            present=Count("id", filter=Q(status="Present")),
            absent=Count("id", filter=Q(status="Absent")),
            late=Count("id", filter=Q(status="Late")),
            excused=Count("id", filter=Q(status="Excused")),
            total=Count("id"),
        )

        total_records = counts["total"] or 0
        if total_records == 0:
            return {
                "present_rate": Decimal("0.00"),
                "absent_rate": Decimal("0.00"),
                "late_rate": Decimal("0.00"),
                "excused_rate": Decimal("0.00"),
                "total_records": 0,
            }

        def _calc_rate(count):
            rate = (Decimal(count) / Decimal(total_records)) * Decimal("100.00")
            return rate.quantize(Decimal("0.01"))

        return {
            "present_rate": _calc_rate(counts["present"]),
            "absent_rate": _calc_rate(counts["absent"]),
            "late_rate": _calc_rate(counts["late"]),
            "excused_rate": _calc_rate(counts["excused"]),
            "total_records": total_records,
        }

    @classmethod
    def get_low_attendance_students(cls, session_id, threshold=Decimal("75.00")):
        """Lists students in a session who have an attendance rate below the threshold."""
        # Find all student IDs active in this session
        enrollments = Enrollment.objects.filter(session_id=session_id, status="Active")
        low_attendance_list = []

        for enrollment in enrollments:
            percentage = cls.calculate_attendance_percentage(enrollment.student_id, session_id)
            if percentage < threshold:
                low_attendance_list.append({
                    "student_id": enrollment.student_id,
                    "student_name": enrollment.student.full_name,
                    "attendance_percentage": percentage,
                })

        return low_attendance_list
