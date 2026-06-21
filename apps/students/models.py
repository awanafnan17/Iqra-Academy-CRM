"""
Students models - Student, Lead, Enrollment, StudentDocument, Guardian.

Student lifecycle: Active -> Inactive/Completed/Alumni
Lead lifecycle: New -> Contacted -> Interested -> Converted/Lost
Enrollment links Student to Session with per-student fee overrides.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.abstract_models import AuditMixin, SoftDeleteMixin, TimestampMixin


# ---------------------------------------------------------------
#  Upload path helpers
# ---------------------------------------------------------------

def student_document_path(instance, filename):
    """Upload student documents into per-student directories."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "file"
    return f"student_documents/{instance.student_id}/{instance.document_type}.{ext}"


# ---------------------------------------------------------------
#  Student
# ---------------------------------------------------------------

class Student(TimestampMixin, SoftDeleteMixin, AuditMixin, models.Model):
    """A student enrolled at the academy.

    Uses full_name as a single field to match Pakistani naming
    conventions and the existing data pattern from the old CRM.
    SoftDeleteMixin prevents accidental permanent deletion of
    students with financial history.
    """

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Completed", "Completed"),
        ("Alumni", "Alumni"),
    ]
    INACTIVE_REASON_CHOICES = [
        ("", "None"),
        ("Freeze", "Freeze"),
        ("Left", "Left"),
        ("Expelled", "Expelled"),
    ]
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    profile_photo = models.ImageField(
        upload_to="students/photos/",
        null=True,
        blank=True,
        verbose_name="Profile Photo",
    )

    roll_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="Unique roll number, generated on first enrollment. Uniqueness enforced in clean().",
    )
    full_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Student full name.",
    )
    father_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Father or guardian name.",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Student email address. Uniqueness enforced in clean() for non-null values.",
    )
    cnic = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Student or parent CNIC number.",
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Primary contact number.",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Date of birth for age calculation.",
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="Student gender.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="Active",
        db_index=True,
        help_text="Current lifecycle status.",
    )
    inactive_reason = models.CharField(
        max_length=15,
        choices=INACTIVE_REASON_CHOICES,
        default="",
        blank=True,
        help_text="Reason for inactive status.",
    )
    last_degree = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Last educational qualification.",
    )
    last_institution = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Name of last institution attended.",
    )
    address_temporary = models.TextField(
        null=True,
        blank=True,
        help_text="Current residential address.",
    )
    address_permanent = models.TextField(
        null=True,
        blank=True,
        help_text="Permanent home address.",
    )
    admission_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Date of first admission to the academy.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Internal notes about this student.",
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_students",
        help_text="Staff member who registered this student.",
    )
    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_record",
        help_text="Linked user account for student portal access.",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
        help_text="User account associated with this student.",
    )
    has_low_attendance = models.BooleanField(
        default=False,
        help_text="Flagged if student attendance falls below 70%.",
    )
    is_selected = models.BooleanField(
        default=False,
        help_text="Flagged if student matches a PDF comparison job.",
    )

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="idx_student_status_created",
            ),
        ]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def clean(self):
        super().clean()
        if self.roll_number:
            qs = Student.all_objects.filter(roll_number=self.roll_number)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "roll_number": f"Roll number '{self.roll_number}' is already assigned."
                })
        if self.email:
            qs = Student.all_objects.filter(email=self.email)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "email": f"Email '{self.email}' is already in use."
                })

    def __str__(self):
        return f"{self.full_name} ({self.roll_number or 'No Roll#'})"


# ---------------------------------------------------------------
#  Lead
# ---------------------------------------------------------------

class Lead(TimestampMixin, AuditMixin, models.Model):
    """A prospective student inquiry.

    Lead is intentionally separate from Student. It is a
    lightweight inquiry record that may never convert.
    Email is not unique because the same person may inquire
    about different sessions over time.
    """

    INQUIRY_SOURCE_CHOICES = [
        ("Call", "Phone Call"),
        ("Message", "Message"),
        ("PhysicalVisit", "Physical Visit"),
        ("Online", "Online"),
        ("Referral", "Referral"),
        ("SocialMedia", "Social Media"),
    ]
    STATUS_CHOICES = [
        ("New", "New"),
        ("Contacted", "Contacted"),
        ("Interested", "Interested"),
        ("Converted", "Converted"),
        ("Lost", "Lost"),
    ]

    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the person inquiring.",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Contact email. Not unique - same person may inquire multiple times.",
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Contact phone number.",
    )
    area_of_residence = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Location for demographic tracking.",
    )
    interested_session = models.ForeignKey(
        "academics.Session",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        help_text="Session they inquired about.",
    )
    inquiry_date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="When the inquiry came in.",
    )
    inquiry_source = models.CharField(
        max_length=20,
        choices=INQUIRY_SOURCE_CHOICES,
        default="Call",
        help_text="How the lead reached us.",
    )
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Next scheduled follow-up date.",
    )
    follow_up_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notes from follow-up conversations.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="New",
        db_index=True,
        help_text="Current lead pipeline status.",
    )
    converted_student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_lead",
        help_text="Links to Student record after conversion.",
    )
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_leads",
        help_text="Staff member handling this lead.",
    )
    loss_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Why this lead was marked as lost.",
    )

    class Meta:
        ordering = ["-inquiry_date"]
        indexes = [
            models.Index(
                fields=["status", "follow_up_date"],
                name="idx_lead_status_followup",
            ),
        ]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


# ---------------------------------------------------------------
#  Enrollment
# ---------------------------------------------------------------

class Enrollment(TimestampMixin, SoftDeleteMixin, AuditMixin, models.Model):
    """A student's enrollment in a session.

    Replaces the old StudentSession model with a more descriptive
    name. Fee and registration_fee are nullable overrides - when
    null, the system reads from the parent Session record.
    This avoids data duplication while allowing per-student
    customization.
    """

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Frozen", "Frozen"),
        ("Completed", "Completed"),
        ("Withdrawn", "Withdrawn"),
        ("Transferred", "Transferred"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
        help_text="The enrolled student.",
    )
    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.PROTECT,
        related_name="enrollments",
        help_text="The session enrolled in. PROTECT prevents cascade conflict with Payment.",
    )
    registration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of enrollment.",
    )
    registration_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Override of session registration fee. Null uses session default.",
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Override of session fee. Null uses session default.",
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount amount applied to this enrollment.",
    )
    discount_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Scholarship or discount justification.",
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date for time-period sessions.",
    )
    next_monthly_due = models.DateField(
        null=True,
        blank=True,
        help_text="Next monthly due date for monthly sessions.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="Active",
        db_index=True,
        help_text="Current enrollment status.",
    )
    freeze_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when enrollment was frozen.",
    )
    freeze_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason for freezing enrollment.",
    )
    transferred_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transferred_to",
        help_text="Source enrollment if this is a transfer.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Internal notes about this enrollment.",
    )
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments_created",
        help_text="Staff who enrolled this student.",
    )
    is_fee_waived = models.BooleanField(
        default=False,
        help_text="Full fee waiver flag.",
    )

    class Meta:
        unique_together = [("student", "session")]
        ordering = ["-registration_date"]
        indexes = [
            models.Index(
                fields=["session", "status"],
                name="idx_enroll_session_status",
            ),
            models.Index(
                fields=["student", "status"],
                name="idx_enroll_student_status",
            ),
            models.Index(
                fields=["due_date"],
                name="idx_enroll_due_date",
            ),
            models.Index(
                fields=["next_monthly_due"],
                name="idx_enroll_monthly_due",
            ),
        ]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def clean(self):
        """Validate only one active enrollment per student at a time."""
        super().clean()
        if self.status == "Active":
            existing_active = Enrollment.objects.filter(
                student=self.student,
                status="Active",
            ).exclude(pk=self.pk)
            if existing_active.exists():
                active_session = existing_active.first().session.name
                raise ValidationError(
                    f"Student {self.student.full_name} is already enrolled "
                    f"in active session: {active_session}. Complete or "
                    f"withdraw before enrolling in a new session."
                )

    @property
    def effective_fee(self):
        """Fee for this enrollment, falling back to session default."""
        if self.fee is not None:
            return self.fee
        return self.session.fee or Decimal("0.00")

    @property
    def effective_registration_fee(self):
        """Registration fee, falling back to session default."""
        if self.registration_fee is not None:
            return self.registration_fee
        return self.session.registration_fee or Decimal("0.00")

    def __str__(self):
        return f"{self.student.full_name} - {self.session.name} ({self.status})"


# ---------------------------------------------------------------
#  StudentDocument
# ---------------------------------------------------------------

class StudentDocument(TimestampMixin, models.Model):
    """Document storage for students.

    Replaces the old pattern of separate ImageField columns
    (profile_photo, cnic_photo, degree_photo) on Student.
    A document table supports unlimited document types, tracks
    upload metadata, and centralizes file management.
    """

    DOCUMENT_TYPE_CHOICES = [
        ("profile_photo", "Profile Photo"),
        ("cnic_front", "CNIC Front"),
        ("cnic_back", "CNIC Back"),
        ("degree", "Degree Certificate"),
        ("certificate", "Other Certificate"),
        ("other", "Other Document"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="The student this document belongs to.",
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Category of this document.",
    )
    title = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Display name for this document.",
    )
    file = models.FileField(
        upload_to=student_document_path,
        help_text="The uploaded file.",
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes, set on upload.",
    )
    mime_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Detected MIME type of the file.",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_student_documents",
        help_text="Staff who uploaded this document.",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["student", "document_type"],
                name="idx_stdoc_student_type",
            ),
        ]
        verbose_name = "Student Document"
        verbose_name_plural = "Student Documents"

    def __str__(self):
        return f"{self.student.full_name} - {self.get_document_type_display()}"


# ---------------------------------------------------------------
#  Guardian
# ---------------------------------------------------------------

class Guardian(TimestampMixin, models.Model):
    """Parent or guardian linked to a student.

    Separate from Student because:
    - A student can have multiple guardians.
    - Each guardian needs independent portal access.
    - Guardian data should not pollute the student record.

    One parent with multiple children will have separate Guardian
    records per child. The parent portal queries by email across
    Guardian records to find all children.
    """

    RELATIONSHIP_CHOICES = [
        ("Father", "Father"),
        ("Mother", "Mother"),
        ("Guardian", "Guardian"),
        ("Sibling", "Sibling"),
        ("Other", "Other"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="guardians",
        help_text="The student this guardian is linked to.",
    )
    full_name = models.CharField(
        max_length=100,
        help_text="Guardian full name.",
    )
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default="Father",
        help_text="Relationship to the student.",
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Guardian contact number.",
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Guardian email address.",
    )
    cnic = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Guardian CNIC number.",
    )
    is_primary = models.BooleanField(
        default=True,
        help_text="Whether this is the primary contact for the student.",
    )
    is_emergency_contact = models.BooleanField(
        default=False,
        help_text="Whether this guardian is an emergency contact.",
    )
    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="guardian_record",
        help_text="Linked user account for parent portal access.",
    )
    occupation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Guardian occupation.",
    )
    address = models.TextField(
        null=True,
        blank=True,
        help_text="Guardian residential address.",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["student", "is_primary"],
                name="idx_guard_student_primary",
            ),
        ]
        verbose_name = "Guardian"
        verbose_name_plural = "Guardians"

    def __str__(self):
        return f"{self.full_name} ({self.get_relationship_display()}) - {self.student.full_name}"


class StudentAchievement(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    title = models.CharField(max_length=200)
    award_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-award_date"]
        verbose_name = "Student Achievement"
        verbose_name_plural = "Student Achievements"

    def __str__(self):
        return f"{self.student.full_name} - {self.title}"

