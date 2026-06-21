"""
Enrollment service layer - handles enrollment lifecycle, capacity checks, and safety.

All operations execute inside database transactions and execute validation prior to save.
"""

import datetime
import logging
from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.services import (
    BaseService,
    transactional_service,
    NotFoundError,
    BusinessRuleViolation,
    DomainValidationError,
)
from apps.students.models import Enrollment, Student
from apps.academics.models import Session

logger = logging.getLogger("crm.students")


class EnrollmentService(BaseService):
    """Orchestrates student enrollment creation, transfers, suspension, and validation."""

    @classmethod
    @transactional_service
    def create_enrollment(
        cls,
        student_id,
        session_id,
        user,
        registration_fee=None,
        fee=None,
        discount=None,
        discount_reason=None,
        due_date=None,
        next_monthly_due=None,
        notes=None,
        ip_address=None,
    ):
        """Enrolls a student in a session.

        Checks for soft-deleted matching records first to restore them.
        Otherwise, validates capacity and creates a new enrollment.
        """
        student = Student.objects.filter(pk=student_id).first()
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")

        # Lock session row to ensure capacity check is race-condition safe
        session = Session.objects.select_for_update().filter(pk=session_id).first()
        if not session:
            raise NotFoundError(f"Session with ID {session_id} not found.")

        if session.status != "Active":
            raise BusinessRuleViolation(f"Cannot enroll in non-active session '{session.name}'.")

        # 1. Soft-delete restoration check (satisfying unique_together constraints)
        existing_soft_deleted = Enrollment.all_objects.filter(
            student_id=student_id,
            session_id=session_id,
            is_deleted=True,
        ).first()

        if existing_soft_deleted:
            cls.log_structured(
                logging.INFO, "create_enrollment", "RESTORE",
                f"Restoring soft-deleted enrollment for student {student.full_name} in {session.name}",
                f"student_id={student_id}, session_id={session_id}"
            )
            # Restore and configure properties
            existing_soft_deleted.is_deleted = False
            existing_soft_deleted.deleted_at = None
            existing_soft_deleted.deleted_by = None
            existing_soft_deleted.status = "Active"

            # Check if there is an active enrollment elsewhere
            existing_active = Enrollment.objects.filter(
                student_id=student_id,
                status="Active",
            ).exclude(pk=existing_soft_deleted.pk)
            if existing_active.exists():
                active_session = existing_active.first().session.name
                raise BusinessRuleViolation(
                    f"Student is already enrolled in active session: {active_session}."
                )

            if fee is not None:
                existing_soft_deleted.fee = fee
            if registration_fee is not None:
                existing_soft_deleted.registration_fee = registration_fee
            if discount is not None:
                existing_soft_deleted.discount = discount
            if discount_reason is not None:
                existing_soft_deleted.discount_reason = discount_reason
            if due_date is not None:
                existing_soft_deleted.due_date = due_date
            if next_monthly_due is not None:
                existing_soft_deleted.next_monthly_due = next_monthly_due
            if notes is not None:
                existing_soft_deleted.notes = notes

            cls.validate_instance(existing_soft_deleted)
            existing_soft_deleted.save()

            cls.audit_on_commit(
                user=user,
                action="update",
                model_name="students.Enrollment",
                object_id=existing_soft_deleted.pk,
                changes={
                    "is_deleted": {"old": True, "new": False},
                    "status": {"old": "Withdrawn", "new": "Active"},
                },
                ip_address=ip_address,
            )
            return existing_soft_deleted

        # 2. Check duplicate non-deleted enrollment
        existing_enrollment = Enrollment.objects.filter(
            student_id=student_id,
            session_id=session_id,
        ).first()
        if existing_enrollment:
            raise BusinessRuleViolation(
                f"Student already enrolled in session '{session.name}' with status '{existing_enrollment.status}'."
            )

        # 3. Check for active enrollment elsewhere
        existing_active = Enrollment.objects.filter(
            student_id=student_id,
            status="Active",
        )
        if existing_active.exists():
            active_session = existing_active.first().session.name
            raise BusinessRuleViolation(
                f"Student is already enrolled in active session: {active_session}."
            )

        # 4. Capacity check
        if session.max_students is not None:
            active_count = Enrollment.objects.filter(session=session, status="Active").count()
            if active_count >= session.max_students:
                raise BusinessRuleViolation(
                    f"Session '{session.name}' has reached its maximum capacity of {session.max_students} students."
                )

        # 5. Populate roll number if needed
        if not student.roll_number:
            prefix = session.roll_prefix or session.code or "STUD"
            count = Enrollment.all_objects.filter(session=session).count()
            student.roll_number = f"{prefix}-{count + 1:02d}"
            cls.validate_instance(student)
            student.save(update_fields=["roll_number", "updated_at"])

            cls.audit_on_commit(
                user=user,
                action="update",
                model_name="students.Student",
                object_id=student.pk,
                changes={"roll_number": {"old": None, "new": student.roll_number}},
                ip_address=ip_address,
            )

        # 6. Instantiate and save enrollment
        enrollment = Enrollment(
            student=student,
            session=session,
            registration_date=timezone.localdate(),
            registration_fee=registration_fee,
            fee=fee,
            discount=discount or Decimal("0.00"),
            discount_reason=discount_reason,
            due_date=due_date,
            next_monthly_due=next_monthly_due,
            status="Active",
            notes=notes,
            enrolled_by=user,
        )
        cls.validate_instance(enrollment)
        enrollment.save()

        cls.audit_on_commit(
            user=user,
            action="create",
            model_name="students.Enrollment",
            object_id=enrollment.pk,
            changes={
                "student_id": student_id,
                "session_id": session_id,
                "status": "Active",
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "create_enrollment", "SUCCESS",
            f"Enrolled student {student.full_name} in session {session.name}",
            f"enrollment_id={enrollment.pk}"
        )
        return enrollment

    @classmethod
    @transactional_service
    def soft_delete_enrollment(cls, enrollment_id, user, reason, ip_address=None):
        """Soft-deletes an enrollment record, marking status as Withdrawn."""
        enrollment = Enrollment.objects.select_for_update().filter(pk=enrollment_id).first()
        if not enrollment:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found.")

        old_status = enrollment.status
        enrollment.status = "Withdrawn"
        enrollment.notes = f"{enrollment.notes or ''}\nWithdrawal Reason: {reason}"
        cls.validate_instance(enrollment)
        enrollment.save(update_fields=["status", "notes", "updated_at"])

        # Triggers SoftDeleteMixin soft_delete method
        enrollment.soft_delete(user=user)

        cls.audit_on_commit(
            user=user,
            action="delete",
            model_name="students.Enrollment",
            object_id=enrollment.pk,
            changes={
                "status": {"old": old_status, "new": "Withdrawn"},
                "is_deleted": {"old": False, "new": True},
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "soft_delete_enrollment", "SUCCESS",
            f"Soft-deleted enrollment ID {enrollment_id}",
            f"user={user}"
        )

    @classmethod
    @transactional_service
    def restore_enrollment(cls, enrollment_id, user, ip_address=None):
        """Restores a soft-deleted enrollment record."""
        enrollment = Enrollment.all_objects.filter(pk=enrollment_id).first()
        if not enrollment:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found.")

        if not enrollment.is_deleted:
            return enrollment

        # Ensure no other active enrollment exists before restoring
        existing_active = Enrollment.objects.filter(
            student_id=enrollment.student_id,
            status="Active",
        )
        if existing_active.exists():
            active_session = existing_active.first().session.name
            raise BusinessRuleViolation(
                f"Cannot restore. Student is already enrolled in active session: {active_session}."
            )

        enrollment.status = "Active"
        cls.validate_instance(enrollment)
        enrollment.restore()

        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Enrollment",
            object_id=enrollment.pk,
            changes={
                "status": {"old": "Withdrawn", "new": "Active"},
                "is_deleted": {"old": True, "new": False},
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "restore_enrollment", "SUCCESS",
            f"Restored enrollment ID {enrollment_id}",
            f"user={user}"
        )
        return enrollment

    @classmethod
    @transactional_service
    def transfer_student(cls, student_id, source_session_id, target_session_id, user, ip_address=None):
        """Transfers a student from a source session to a target session atomically."""
        student = Student.objects.filter(pk=student_id).first()
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")

        # Lock source enrollment to prevent concurrent transfers
        source_enrollment = (
            Enrollment.objects
            .select_for_update()
            .filter(
                student_id=student_id,
                session_id=source_session_id,
                status="Active",
            )
            .first()
        )

        if not source_enrollment:
            raise BusinessRuleViolation(
                f"No active enrollment found for student {student.full_name} in source session."
            )

        # Lock target session to ensure capacity check is concurrent-safe
        target_session = Session.objects.select_for_update().filter(pk=target_session_id).first()
        if not target_session:
            raise NotFoundError(f"Target session with ID {target_session_id} not found.")

        if target_session.status != "Active":
            raise BusinessRuleViolation(f"Target session '{target_session.name}' is not Active.")

        # Capacity check on target session
        if target_session.max_students is not None:
            active_count = Enrollment.objects.filter(session=target_session, status="Active").count()
            if active_count >= target_session.max_students:
                raise BusinessRuleViolation(
                    f"Target session '{target_session.name}' has reached its maximum capacity of {target_session.max_students} students."
                )

        # Check if enrollment already exists in target session
        target_enrollment = Enrollment.all_objects.filter(
            student_id=student_id,
            session_id=target_session_id,
        ).first()

        # Step 1: Deactivate and soft delete source enrollment
        source_enrollment.status = "Transferred"
        cls.validate_instance(source_enrollment)
        source_enrollment.save(update_fields=["status", "updated_at"])
        source_enrollment.soft_delete(user=user)

        # Deactivate any active installment plans on the source enrollment
        from apps.finance.models import InstallmentPlan
        active_plan = InstallmentPlan.objects.filter(
            enrollment=source_enrollment,
            is_active=True,
        ).first()
        if active_plan:
            active_plan.is_active = False
            active_plan.save(update_fields=["is_active", "updated_at"])

        # Step 2: Establish target enrollment (restore if soft-deleted, else create new)
        if target_enrollment and target_enrollment.is_deleted:
            target_enrollment.is_deleted = False
            target_enrollment.deleted_at = None
            target_enrollment.deleted_by = None
            target_enrollment.status = "Active"
            target_enrollment.transferred_from = source_enrollment
            cls.validate_instance(target_enrollment)
            target_enrollment.save()
            new_enrollment = target_enrollment
        elif target_enrollment:
            raise BusinessRuleViolation(
                f"Student already has an enrollment in target session with status '{target_enrollment.status}'."
            )
        else:
            new_enrollment = Enrollment(
                student=student,
                session=target_session,
                registration_date=timezone.localdate(),
                status="Active",
                transferred_from=source_enrollment,
                enrolled_by=user,
            )
            cls.validate_instance(new_enrollment)
            new_enrollment.save()

        # Step 3: Write audit logs
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Enrollment",
            object_id=source_enrollment.pk,
            changes={"status": {"old": "Active", "new": "Transferred"}, "is_deleted": {"old": False, "new": True}},
            ip_address=ip_address,
        )

        cls.audit_on_commit(
            user=user,
            action="create" if not (target_enrollment and target_enrollment.is_deleted) else "update",
            model_name="students.Enrollment",
            object_id=new_enrollment.pk,
            changes={
                "student_id": student_id,
                "session_id": target_session_id,
                "status": "Active",
                "transferred_from_id": source_enrollment.pk,
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "transfer_student", "SUCCESS",
            f"Transferred student {student.full_name} from session ID {source_session_id} to {target_session_id}",
            f"new_enrollment_id={new_enrollment.pk}"
        )
        return new_enrollment

    @classmethod
    @transactional_service
    def freeze_enrollment(cls, enrollment_id, reason, user, freeze_date=None, ip_address=None):
        """Freezes an active enrollment record."""
        enrollment = Enrollment.objects.select_for_update().filter(pk=enrollment_id).first()
        if not enrollment:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found.")

        if enrollment.status != "Active":
            raise BusinessRuleViolation(
                f"Only Active enrollments can be frozen. Current status: '{enrollment.status}'."
            )

        f_date = freeze_date or timezone.localdate()
        enrollment.status = "Frozen"
        enrollment.freeze_date = f_date
        enrollment.freeze_reason = reason
        cls.validate_instance(enrollment)
        enrollment.save(update_fields=["status", "freeze_date", "freeze_reason", "updated_at"])

        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Enrollment",
            object_id=enrollment.pk,
            changes={
                "status": {"old": "Active", "new": "Frozen"},
                "freeze_date": {"old": None, "new": str(f_date)},
                "freeze_reason": {"old": None, "new": reason},
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "freeze_enrollment", "SUCCESS",
            f"Frozen enrollment ID {enrollment_id}",
            f"freeze_date={f_date}"
        )
        return enrollment

    @classmethod
    @transactional_service
    def unfreeze_enrollment(cls, enrollment_id, user, ip_address=None):
        """Unfreezes a frozen enrollment record, shifting next due date by frozen duration."""
        enrollment = Enrollment.objects.filter(pk=enrollment_id).first()
        if not enrollment:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found.")

        if enrollment.status != "Frozen":
            raise BusinessRuleViolation(
                f"Only Frozen enrollments can be unfrozen. Current status: '{enrollment.status}'."
            )

        today = timezone.localdate()
        freeze_date = enrollment.freeze_date or today
        days_frozen = (today - freeze_date).days
        if days_frozen < 0:
            days_frozen = 0

        old_due = enrollment.next_monthly_due
        if enrollment.next_monthly_due:
            enrollment.next_monthly_due = enrollment.next_monthly_due + datetime.timedelta(days=days_frozen)

        enrollment.status = "Active"
        enrollment.freeze_date = None
        enrollment.freeze_reason = ""
        cls.validate_instance(enrollment)
        enrollment.save(update_fields=["status", "freeze_date", "freeze_reason", "next_monthly_due", "updated_at"])

        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Enrollment",
            object_id=enrollment.pk,
            changes={
                "status": {"old": "Frozen", "new": "Active"},
                "freeze_date": {"old": str(freeze_date), "new": None},
                "next_monthly_due": {"old": str(old_due) if old_due else None, "new": str(enrollment.next_monthly_due) if enrollment.next_monthly_due else None},
            },
            ip_address=ip_address,
        )

        cls.log_structured(
            logging.INFO, "unfreeze_enrollment", "SUCCESS",
            f"Unfrozen enrollment ID {enrollment_id}",
            f"days_frozen={days_frozen}"
        )
        return enrollment

    @classmethod
    def calculate_academic_score(cls, student_id, session_id):
        """Calculates the weighted academic performance score for a student in a session.

        Attendance: 30% weight
        Exams: 50% weight
        Fee compliance: 20% weight

        Defaults to 100.00 for components with no data to avoid initial penalties.
        """
        enrollment = Enrollment.all_objects.filter(student_id=student_id, session_id=session_id).first()
        if not enrollment:
            return Decimal("100.00")

        # Check if no attendance, no exams, and no payments exist
        from apps.attendance.models import AttendanceRecord
        from apps.exams.models import ExamResult
        from apps.finance.models import Payment

        has_attendance = AttendanceRecord.objects.filter(student_id=student_id, session_id=session_id).exists()
        has_exams = ExamResult.objects.filter(student_id=student_id, exam__session_id=session_id).exists()
        has_payments = Payment.objects.filter(enrollment_id=enrollment.id).exists()

        if not has_attendance and not has_exams and not has_payments:
            return Decimal("100.00")

        # 1. Attendance (30% weight)
        from apps.attendance.services import AttendanceService
        attendance_percentage = AttendanceService.calculate_attendance_percentage(student_id, session_id)
        if attendance_percentage is None:
            attendance_score = Decimal("100.00")
        else:
            attendance_score = Decimal(attendance_percentage)

        # 2. Exams (50% weight)
        from apps.exams.models import ExamResult
        results = ExamResult.objects.filter(student_id=student_id, exam__session_id=session_id)
        if not results.exists():
            exam_score = Decimal("100.00")
        else:
            total_pct = Decimal("0.00")
            count = 0
            for r in results:
                if r.percentage is not None:
                    total_pct += Decimal(r.percentage)
                    count += 1
            if count > 0:
                exam_score = total_pct / Decimal(count)
            else:
                exam_score = Decimal("100.00")

        # 3. Fee compliance (20% weight)
        from apps.finance.services import calculate_student_ledger
        try:
            ledger = calculate_student_ledger(enrollment.id)
            total_paid = Decimal(ledger.get("total_paid") or "0.00")
            total_payable = Decimal(ledger.get("total_payable") or "0.00")
            is_fee_waived = ledger.get("is_fee_waived", False)

            if is_fee_waived or total_payable <= 0:
                fee_compliance_score = Decimal("100.00")
            else:
                ratio = total_paid / total_payable
                if ratio > 1:
                    ratio = Decimal("1.00")
                elif ratio < 0:
                    ratio = Decimal("0.00")
                fee_compliance_score = ratio * Decimal("100.00")
        except Exception:
            fee_compliance_score = Decimal("100.00")

        # Calculate final score
        final_score = (attendance_score * Decimal("0.30")) + (exam_score * Decimal("0.50")) + (fee_compliance_score * Decimal("0.20"))
        return final_score.quantize(Decimal("0.01"))

    @classmethod
    def get_average_academic_score_for_enrollments(cls, enrollments):
        """Performs bulk fetch for attendance, exams, and ledgers in 3 database queries to prevent N+1 queries.

        Returns a dictionary mapping enrollment.id to their computed academic score.
        Also returns the overall average score for the provided enrollments.
        """
        if not enrollments:
            return {}, Decimal("100.00")

        # Extract student, session, and enrollment IDs
        student_ids = [e.student_id for e in enrollments]
        session_ids = list(set([e.session_id for e in enrollments]))
        enrollment_ids = [e.id for e in enrollments]

        # Query 1: Attendance records in bulk
        from apps.attendance.models import AttendanceRecord
        attendance_map = {}
        att_qs = AttendanceRecord.objects.filter(
            student_id__in=student_ids,
            session_id__in=session_ids
        ).values('student_id', 'session_id', 'status')

        for r in att_qs:
            key = (r['student_id'], r['session_id'])
            if key not in attendance_map:
                attendance_map[key] = {'attended': 0, 'total': 0}
            if r['status'] in ['Present', 'Late']:
                attendance_map[key]['attended'] += 1
            if r['status'] in ['Present', 'Absent', 'Late']:
                attendance_map[key]['total'] += 1

        # Query 2: Exam results in bulk
        from apps.exams.models import ExamResult
        exam_map = {}
        exam_qs = ExamResult.objects.filter(
            student_id__in=student_ids,
            exam__session_id__in=session_ids
        ).values('student_id', 'exam__session_id', 'percentage')

        for r in exam_qs:
            key = (r['student_id'], r['exam__session_id'])
            if key not in exam_map:
                exam_map[key] = {'total_pct': Decimal("0.00"), 'count': 0}
            if r['percentage'] is not None:
                exam_map[key]['total_pct'] += Decimal(r['percentage'])
                exam_map[key]['count'] += 1

        # Query 3: Tuition payments in bulk
        from apps.finance.models import Payment
        payment_map = {}
        pay_qs = Payment.objects.filter(
            enrollment_id__in=enrollment_ids,
            payment_status="confirmed",
            is_late_fee_payment=False
        ).values('enrollment_id', 'amount')

        for p in pay_qs:
            eid = p['enrollment_id']
            if eid not in payment_map:
                payment_map[eid] = Decimal("0.00")
            payment_map[eid] += Decimal(p['amount'])

        # Now compute scores for each enrollment in Python memory
        scores_by_enrollment = {}
        total_score_sum = Decimal("0.00")
        enrollment_count = 0

        for enrollment in enrollments:
            student_id = enrollment.student_id
            session_id = enrollment.session_id
            key = (student_id, session_id)

            # 1. Attendance Score (30%)
            att_info = attendance_map.get(key, {'attended': 0, 'total': 0})
            if att_info['total'] == 0:
                attendance_score = Decimal("100.00")
            else:
                attendance_score = (Decimal(att_info['attended']) / Decimal(att_info['total'])) * Decimal("100.00")

            # 2. Exams Score (50%)
            ex_info = exam_map.get(key, {'total_pct': Decimal("0.00"), 'count': 0})
            if ex_info['count'] == 0:
                exam_score = Decimal("100.00")
            else:
                exam_score = ex_info['total_pct'] / Decimal(ex_info['count'])

            # 3. Fee Compliance Score (20%)
            fee = enrollment.fee if enrollment.fee is not None else (enrollment.session.fee or Decimal("0.00"))
            reg_fee = enrollment.registration_fee if enrollment.registration_fee is not None else (enrollment.session.registration_fee or Decimal("0.00"))
            discount = enrollment.discount or Decimal("0.00")
            total_payable = fee + reg_fee - discount

            total_paid = payment_map.get(enrollment.id, Decimal("0.00"))

            if enrollment.is_fee_waived or total_payable <= 0:
                fee_compliance_score = Decimal("100.00")
            else:
                ratio = total_paid / total_payable
                if ratio > 1:
                    ratio = Decimal("1.00")
                elif ratio < 0:
                    ratio = Decimal("0.00")
                fee_compliance_score = ratio * Decimal("100.00")

            # Final weighted score
            score = (attendance_score * Decimal("0.30")) + (exam_score * Decimal("0.50")) + (fee_compliance_score * Decimal("0.20"))
            score = score.quantize(Decimal("0.01"))

            scores_by_enrollment[enrollment.id] = score
            total_score_sum += score
            enrollment_count += 1

        overall_average = Decimal("100.00")
        if enrollment_count > 0:
            overall_average = (total_score_sum / Decimal(enrollment_count)).quantize(Decimal("0.01"))

        return scores_by_enrollment, overall_average

    @classmethod
    @transactional_service
    def transfer_student_to_session(cls, student_id, new_session_id, user, ip_address=None):
        """Transfers a student to a new session by finding their active enrollment."""
        student = Student.objects.select_for_update().filter(pk=student_id).first()
        if not student:
            raise NotFoundError(f"Student with ID {student_id} not found.")

        # Lock source enrollment to prevent concurrent transfers
        active_enrollment = (
            Enrollment.objects
            .select_for_update()
            .filter(
                student_id=student_id,
                status="Active",
            )
            .first()
        )

        if not active_enrollment:
            raise BusinessRuleViolation(
                f"No active enrollment found for student {student.full_name}."
            )

        source_session_id = active_enrollment.session_id

        # Lock target session to ensure capacity check is concurrent-safe
        target_session = Session.objects.select_for_update().filter(pk=new_session_id).first()
        if not target_session:
            raise NotFoundError(f"Target session with ID {new_session_id} not found.")

        if target_session.status != "Active":
            raise BusinessRuleViolation(f"Target session '{target_session.name}' is not Active.")

        # Capacity check on target session
        if target_session.max_capacity is not None:
            active_count = Enrollment.objects.filter(session=target_session, status="Active").count()
            if active_count >= target_session.max_capacity:
                raise BusinessRuleViolation(
                    f"Target session '{target_session.name}' has reached its maximum capacity of {target_session.max_capacity} students."
                )

        # Check if enrollment already exists in target session
        target_enrollment = Enrollment.all_objects.filter(
            student_id=student_id,
            session_id=new_session_id,
        ).first()

        # Step 1: Ensure old enrollment has status = "Transferred" and save it
        active_enrollment.status = "Transferred"
        active_enrollment.save(update_fields=["status"])
        active_enrollment.soft_delete(user=user)

        # Deactivate any active installment plans on the source enrollment
        from apps.finance.models import InstallmentPlan
        active_plan = InstallmentPlan.objects.filter(
            enrollment=active_enrollment,
            is_active=True,
        ).first()
        if active_plan:
            active_plan.is_active = False
            active_plan.save(update_fields=["is_active", "updated_at"])

        # Step 2: Establish target enrollment (restore if soft-deleted, else create new)
        if target_enrollment and target_enrollment.is_deleted:
            target_enrollment.is_deleted = False
            target_enrollment.deleted_at = None
            target_enrollment.deleted_by = None
            target_enrollment.status = "Active"
            target_enrollment.transferred_from = active_enrollment
            cls.validate_instance(target_enrollment)
            target_enrollment.save()
            new_enrollment = target_enrollment
        elif target_enrollment:
            raise BusinessRuleViolation(
                f"Student already has an enrollment in target session with status '{target_enrollment.status}'."
            )
        else:
            new_enrollment = Enrollment(
                student=student,
                session=target_session,
                registration_date=timezone.localdate(),
                status="Active",
                transferred_from=active_enrollment,
            )
            cls.validate_instance(new_enrollment)
            new_enrollment.save()

        # Log to AuditLog for target enrollment
        cls.audit_on_commit(
            user=user,
            action="create",
            model_name="students.Enrollment",
            object_id=new_enrollment.pk,
            changes={"status": {"old": None, "new": "Active"}},
            ip_address=ip_address,
        )

        # Regenerate roll number using new session's prefix
        prefix = target_session.roll_prefix or target_session.code or "STUD"
        count = Enrollment.all_objects.filter(session=target_session).exclude(student=student).count()
        old_roll = student.roll_number
        student.roll_number = f"{prefix}-{count + 1:02d}"
        cls.validate_instance(student)
        student.save(update_fields=["roll_number", "updated_at"])

        # Log to AuditLog for student roll number change
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Student",
            object_id=student.pk,
            changes={"roll_number": {"old": old_roll, "new": student.roll_number}},
            ip_address=ip_address,
        )

        return new_enrollment


class StudentService(BaseService):
    """Orchestrates general student management operations."""

    @classmethod
    @transactional_service
    def update_student_profile(cls, student_id, user, phone, address, email):
        """Allows a student to update their own contact information.

        Validates email uniqueness across student and user models,
        logs the changes to AuditLog, and saves inside transaction.atomic.
        """
        from apps.students.models import Student
        from apps.core.services import BusinessRuleViolation, NotFoundError
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            raise NotFoundError("Student not found.")

        # Check permissions: Student can only update their own profile
        is_student = user.groups.filter(name="Student").exists()
        if is_student and student.portal_user != user:
            raise BusinessRuleViolation("You are not authorized to update this profile.")

        # Validate email uniqueness in Student model
        if Student.objects.filter(email=email).exclude(pk=student_id).exists():
            raise ValidationError({"email": "This email is already in use by another student."})

        # Validate email uniqueness in User model
        User = get_user_model()
        if student.portal_user:
            if User.objects.filter(email=email).exclude(pk=student.portal_user.pk).exists():
                raise ValidationError({"email": "This email is already in use by another user account."})
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError({"email": "This email is already in use by another user account."})

        # Track changes for AuditLog
        old_phone = student.phone
        old_address = student.address_temporary
        old_email = student.email

        # Update student record
        student.phone = phone
        student.address_temporary = address
        student.email = email
        cls.validate_instance(student)
        student.save()

        # Update user account if linked
        if student.portal_user:
            portal_user = student.portal_user
            portal_user.email = email
            portal_user.username = email
            portal_user.full_clean()
            portal_user.save()

        # Log to AuditLog
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="students.Student",
            object_id=student.pk,
            changes={
                "phone": {"old": old_phone, "new": phone},
                "address": {"old": old_address, "new": address},
                "email": {"old": old_email, "new": email},
            }
        )
        return student

    @classmethod
    def _create_portal_user(cls, email, full_name):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        User = get_user_model()
        password = User.objects.make_random_password(length=10)
        portal_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name.split()[0] if full_name else "",
            last_name=" ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else "",
        )
        student_group, _ = Group.objects.get_or_create(name="Student")
        portal_user.groups.add(student_group)
        return portal_user, password

    @classmethod
    @transactional_service
    def create_student(
        cls,
        full_name,
        father_name="",
        email="",
        phone="",
        date_of_birth=None,
        cnic="",
        address="",
        gender="",
        created_by=None,
    ):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        portal_user = None
        password = None
        if email and not User.objects.filter(email=email).exists():
            portal_user, password = cls._create_portal_user(email, full_name)

        student = Student(
            full_name=full_name,
            father_name=father_name,
            email=email or "",
            phone=(phone or "")[:15],
            cnic=cnic or "",
            address_temporary=address or "",
            gender=gender or "",
            portal_user=portal_user,
            user=portal_user,
        )
        if date_of_birth:
            student.date_of_birth = date_of_birth

        cls.validate_instance(student)
        student.save()

        if portal_user:
            student._portal_username = portal_user.username
            if password:
                student._portal_password = password

        try:
            from apps.core.services import audit_on_commit
            audit_on_commit(
                action="CREATE",
                model_name="Student",
                object_id=student.pk,
                object_repr=str(student),
                user=created_by,
                details={"full_name": full_name},
            )
        except Exception:
            pass

        return student
