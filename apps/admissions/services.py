import datetime
import logging
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.http import Http404
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from apps.core.services import BaseService, transactional_service, BusinessRuleViolation
from apps.admissions.models import AdmissionApplication, AdmissionDocument
from apps.students.models import Student
from apps.students.services import EnrollmentService
from apps.notifications.models import EmailLog

logger = logging.getLogger("crm.admissions")

def check_is_admin(user):
    """Raise Http404 if the user is not Admin or superuser."""
    if not user or not user.is_authenticated:
        raise Http404("Not authorized.")
    if user.is_superuser:
        return True
    if user.groups.filter(name="Admin").exists():
        return True
    raise Http404("Not authorized.")

def check_is_admin_or_registrar(user):
    """Raise Http404 if the user is not Admin, Registrar, or superuser."""
    if not user or not user.is_authenticated:
        raise Http404("Not authorized.")
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=["Admin", "Registrar"]).exists():
        return True
    raise Http404("Not authorized.")


def send_and_log_email(recipient_email, subject, body, template_name, context, user=None):
    """Helper to send EmailMultiAlternatives and save to EmailLog."""
    status = "sent"
    error_message = ""
    try:
        html_content = render_to_string(template_name, context)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "IICE ERP <notifications@yourdomain.com>"),
            to=[recipient_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        status = "failed"
        error_message = str(e)
        logger.error(f"Email send failed to {recipient_email}: {error_message}")

    with transaction.atomic():
        log = EmailLog(
            recipient_email=recipient_email,
            subject=subject,
            body_preview=body[:500],
            status=status,
            error_message=error_message,
            sent_by=user,
        )
        log.full_clean()
        log.save()
    return log


class AdmissionService(BaseService):
    """Orchestrates application submission, review workflow, and student registration conversion."""

    @classmethod
    @transactional_service
    def submit_application(
        cls,
        full_name,
        father_name,
        email,
        phone,
        date_of_birth,
        desired_session,
        exam_type,
        cnic="",
        address="",
        documents=None,
        user=None
    ):
        """Submit a public or staff-entered admission application.
        
        Validates duplicates within the last 30 days on email + desired_session.
        """
        # Resolve desired_session object
        from apps.academics.models import Session
        if isinstance(desired_session, (int, str)):
            session_obj = Session.objects.get(pk=desired_session)
        else:
            session_obj = desired_session

        # 30-day duplicate check
        thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
        duplicate_exists = AdmissionApplication.objects.filter(
            email=email,
            desired_session=session_obj,
            applied_at__gte=thirty_days_ago
        ).exists()
        if duplicate_exists:
            raise ValidationError({
                "email": "An application for this email and session has already been submitted within the last 30 days."
            })

        # Create AdmissionApplication
        application = AdmissionApplication(
            full_name=full_name,
            father_name=father_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            desired_session=session_obj,
            exam_type=exam_type,
            cnic=cnic,
            address=address,
            status="pending",
            created_by=user if (user and user.is_authenticated) else None
        )
        cls.validate_instance(application)
        application.save()

        # Handle uploaded documents
        if documents:
            for doc_type, doc_file in documents:
                doc = AdmissionDocument(
                    application=application,
                    document_type=doc_type,
                    file=doc_file
                )
                cls.validate_instance(doc)
                doc.save()

        # Audit log creation
        cls.audit_on_commit(
            user=user if (user and user.is_authenticated) else None,
            action="create",
            model_name="admissions.AdmissionApplication",
            object_id=application.pk,
            changes={
                "full_name": full_name,
                "email": email,
                "desired_session_id": session_obj.pk,
                "exam_type": exam_type,
            }
        )

        return application

    @classmethod
    @transactional_service
    def review_application(cls, application_id, user, remarks=None, ip_address=None):
        """Verifies user permission and transitions status to under_review."""
        check_is_admin_or_registrar(user)

        application = AdmissionApplication.objects.select_for_update().get(pk=application_id)
        old_status = application.status

        # Update status and reviewer details
        application.status = "under_review"
        application.reviewed_by = user
        application.reviewed_at = timezone.now()
        if remarks is not None:
            application.remarks = remarks

        cls.validate_instance(application)
        application.save(update_fields=["status", "reviewed_by", "reviewed_at", "remarks"])

        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="admissions.AdmissionApplication",
            object_id=application.pk,
            changes={"status": {"old": old_status, "new": "under_review"}},
            ip_address=ip_address
        )
        return application

    @classmethod
    @transactional_service
    def approve_application(cls, application_id, user, remarks=None, ip_address=None):
        """Verifies user is Admin and transitions status to approved."""
        check_is_admin(user)

        application = AdmissionApplication.objects.select_for_update().get(pk=application_id)
        old_status = application.status

        application.status = "approved"
        application.reviewed_by = user
        application.reviewed_at = timezone.now()
        if remarks is not None:
            application.remarks = remarks

        cls.validate_instance(application)
        application.save(update_fields=["status", "reviewed_by", "reviewed_at", "remarks"])

        # Audit log
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="admissions.AdmissionApplication",
            object_id=application.pk,
            changes={"status": {"old": old_status, "new": "approved"}},
            ip_address=ip_address
        )

        # Dispatch approval email
        context = {
            "applicant_name": application.full_name,
            "session_name": application.desired_session.name if application.desired_session else "N/A",
            "exam_type": application.get_exam_type_display(),
            "portal_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8001/"),
        }
        send_and_log_email(
            recipient_email=application.email,
            subject="Admission Application Approved",
            body=f"Dear {application.full_name}, your application for {context['session_name']} has been approved.",
            template_name="emails/admission_approved.html",
            context=context,
            user=user
        )

        return application

    @classmethod
    @transactional_service
    def reject_application(cls, application_id, user, remarks=None, ip_address=None):
        """Verifies user is Admin and transitions status to rejected."""
        check_is_admin(user)

        application = AdmissionApplication.objects.select_for_update().get(pk=application_id)
        old_status = application.status

        application.status = "rejected"
        application.reviewed_by = user
        application.reviewed_at = timezone.now()
        if remarks is not None:
            application.remarks = remarks

        cls.validate_instance(application)
        application.save(update_fields=["status", "reviewed_by", "reviewed_at", "remarks"])

        # Audit log
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="admissions.AdmissionApplication",
            object_id=application.pk,
            changes={"status": {"old": old_status, "new": "rejected"}},
            ip_address=ip_address
        )

        # Dispatch rejection email
        context = {
            "applicant_name": application.full_name,
            "session_name": application.desired_session.name if application.desired_session else "N/A",
            "remarks": application.remarks,
        }
        send_and_log_email(
            recipient_email=application.email,
            subject="Admission Application Status Update",
            body=f"Dear {application.full_name}, your application for {context['session_name']} was rejected.",
            template_name="emails/admission_rejected.html",
            context=context,
            user=user
        )

        return application

    @classmethod
    @transactional_service
    def convert_to_student(cls, application_id, user, ip_address=None):
        """Verifies user is Admin, creates Student, links Enrollment, updates status to withdrawn."""
        check_is_admin(user)

        application = AdmissionApplication.objects.select_for_update().select_related("desired_session").get(pk=application_id)
        if application.status != "approved":
            raise BusinessRuleViolation("Only approved applications can be converted to registered students.")

        # Truncate strings to match constraints on Student model
        safe_full_name = application.full_name[:100]
        safe_father_name = application.father_name[:100] if application.father_name else ""
        safe_phone = application.phone[:15] if application.phone else ""
        safe_cnic = application.cnic[:15] if application.cnic else ""

        # Create Student profile
        student = Student(
            full_name=safe_full_name,
            father_name=safe_father_name,
            email=application.email,
            phone=safe_phone,
            cnic=safe_cnic,
            date_of_birth=application.date_of_birth,
            address_temporary=application.address,
            status="Active",
            added_by=user,
            admission_date=timezone.localdate()
        )
        cls.validate_instance(student)
        student.save()

        # Audit Student creation
        cls.audit_on_commit(
            user=user,
            action="create",
            model_name="students.Student",
            object_id=student.pk,
            changes={
                "full_name": student.full_name,
                "email": student.email,
            },
            ip_address=ip_address
        )

        # Create Enrollment (which generates roll number automatically)
        enrollment = EnrollmentService.create_enrollment(
            student_id=student.pk,
            session_id=application.desired_session_id,
            user=user,
            ip_address=ip_address
        )

        # Fetch updated student to get the generated roll number
        student.refresh_from_db()

        # Update application status to withdrawn (conversion complete)
        old_status = application.status
        application.status = "withdrawn"
        application.converted_student = student
        application.save(update_fields=["status", "converted_student"])

        # Audit log for application status update
        cls.audit_on_commit(
            user=user,
            action="update",
            model_name="admissions.AdmissionApplication",
            object_id=application.pk,
            changes={"status": {"old": old_status, "new": "withdrawn"}},
            ip_address=ip_address
        )

        # Dispatch welcome email
        context = {
            "applicant_name": student.full_name,
            "roll_number": student.roll_number,
            "session_name": application.desired_session.name if application.desired_session else "N/A",
            "portal_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8001/"),
        }
        send_and_log_email(
            recipient_email=student.email,
            subject="Welcome to IICE Academy!",
            body=f"Welcome {student.full_name}! Your roll number is {student.roll_number}.",
            template_name="emails/admission_welcome.html",
            context=context,
            user=user
        )

        return student

    @classmethod
    def get_pending_applications(cls):
        """Optimization: Returns pending/under_review applications using select_related."""
        return AdmissionApplication.objects.filter(
            status__in=["pending", "under_review"]
        ).select_related("desired_session", "reviewed_by", "converted_student").order_by("-applied_at")

    @classmethod
    def get_application_summary(cls):
        """Computes aggregate metrics in a single pass."""
        aggregates = AdmissionApplication.objects.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            under_review=Count("id", filter=Q(status="under_review")),
            approved=Count("id", filter=Q(status="approved")),
            rejected=Count("id", filter=Q(status="rejected")),
            converted=Count("id", filter=Q(status="withdrawn", converted_student__isnull=False))
        )
        
        total = aggregates["total"] or 0
        converted = aggregates["converted"] or 0
        conversion_rate = round((converted / total * 100.0), 2) if total > 0 else 0.0

        return {
            "total_applications": total,
            "pending_applications": (aggregates["pending"] or 0) + (aggregates["under_review"] or 0),
            "approved_applications": aggregates["approved"] or 0,
            "rejected_applications": aggregates["rejected"] or 0,
            "converted_applications": converted,
            "conversion_rate": conversion_rate,
        }
