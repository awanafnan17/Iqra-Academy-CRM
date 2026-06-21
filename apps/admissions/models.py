from django.db import models
from django.conf import settings
from apps.academics.models import Session
from apps.students.models import Student

class AdmissionApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    full_name = models.CharField(max_length=200, help_text="Applicant full name.")
    father_name = models.CharField(max_length=200, help_text="Father's full name.")
    email = models.EmailField(help_text="Contact email address.")
    phone = models.CharField(max_length=20, help_text="Contact phone number.")
    date_of_birth = models.DateField(help_text="Applicant date of birth.")
    cnic = models.CharField(max_length=15, blank=True, help_text="Applicant CNIC/B-Form.")
    address = models.TextField(blank=True, help_text="Postal address.")
    desired_session = models.ForeignKey(
        Session,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Target academic session."
    )
    exam_type = models.CharField(
        max_length=20,
        choices=Session.SESSION_CATEGORY_CHOICES,
        help_text="Exam category classification."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Current status of the admission application."
    )
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_applications",
        help_text="Staff user who reviewed this application."
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, help_text="Internal staff remarks.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_applications",
        help_text="User who submitted this application."
    )
    converted_student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Linked student record post-conversion."
    )

    class Meta:
        ordering = ["-applied_at"]

    def clean(self):
        super().clean()
        # Custom clean validation if needed

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.exam_type}) — {self.status}"


class AdmissionDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ("cnic", "CNIC / B-Form"),
        ("photo", "Profile Photograph"),
        ("academic_certificate", "Academic Certificate"),
        ("other", "Other Document"),
    ]

    application = models.ForeignKey(
        AdmissionApplication,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="The linked admission application."
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Category of the document."
    )
    file = models.FileField(upload_to="admission_documents/", help_text="Uploaded document file.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application.full_name} — {self.get_document_type_display()}"
