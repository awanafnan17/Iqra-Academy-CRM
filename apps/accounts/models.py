"""
Accounts models - CustomUser and UserProfile.

CustomUser extends AbstractUser and uses email as the login identifier.
Django Groups are used for RBAC with 7 roles:
Admin, AcademicManager, Teacher, AccountsOfficer,
Receptionist, StudentPortal, ParentPortal.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.abstract_models import TimestampMixin


# ---------------------------------------------------------------
#  Upload path helpers
# ---------------------------------------------------------------

def user_profile_photo_path(instance, filename):
    """Generate safe upload path for user profile photos."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    safe_name = slugify(f"{instance.first_name}_{instance.last_name}_{instance.pk}")
    return f"user_profiles/{safe_name}.{ext}"


def user_cnic_photo_path(instance, filename):
    """Generate safe upload path for user CNIC photos."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    safe_name = slugify(f"{instance.user.pk}_cnic")
    return f"user_cnic/{safe_name}.{ext}"


def user_degree_photo_path(instance, filename):
    """Generate safe upload path for user degree photos."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    safe_name = slugify(f"{instance.user.pk}_degree")
    return f"user_degrees/{safe_name}.{ext}"


# ---------------------------------------------------------------
#  CustomUser
# ---------------------------------------------------------------

class CustomUser(AbstractUser):
    """Custom user model with email-based login.

    Extends Django's AbstractUser to get full auth, permission,
    and group system. Replaces the old custom User model that
    used integer usertype and manual password hashing.

    USERNAME_FIELD is email. The inherited username field is kept
    but auto-populated from email prefix to satisfy AbstractUser.
    """

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Used as login identifier. Must be unique.",
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Mobile phone number.",
    )
    cnic = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="National ID card number.",
    )
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path,
        null=True,
        blank=True,
        help_text="User profile photograph.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Active",
        db_index=True,
        help_text="Account status. Inactive users cannot log in.",
    )

    # Brute force protection
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts.",
    )
    lockout_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account locked until this time due to failed attempts.",
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of last successful login.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "is_active"],
                name="idx_user_status_active",
            ),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        """Return first_name + last_name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self):
        """Canonical display name for all user-facing identity surfaces.

        Returns the user's full name (first + last). Falls back to
        username only when both first_name and last_name are blank.
        Templates and context helpers should use this property instead
        of accessing first_name, last_name, or username directly.
        Normalizes whitespace so padded names render cleanly.
        """
        full = self.get_full_name().strip()
        if full:
            # Collapse multiple spaces (e.g. "  Ahmed     Khan  " → "Ahmed Khan")
            return " ".join(full.split())
        return self.username

    @property
    def is_locked_out(self):
        """Check if account is currently locked."""
        if self.lockout_until and self.lockout_until > timezone.now():
            return True
        return False

    @property
    def lockout_remaining_seconds(self):
        """Seconds remaining in lockout period. 0 if not locked."""
        if self.is_locked_out:
            delta = self.lockout_until - timezone.now()
            return max(0, int(delta.total_seconds()))
        return 0

    def record_failed_login(self):
        """Record a failed login attempt. Lock after 5 failures."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            multiplier = min(self.failed_login_attempts - 4, 6)
            lockout_minutes = 5 * (2 ** (multiplier - 1))
            self.lockout_until = timezone.now() + timezone.timedelta(
                minutes=lockout_minutes
            )
        self.save(update_fields=["failed_login_attempts", "lockout_until"])

    def record_successful_login(self, ip_address=None):
        """Reset failed attempts and record login metadata."""
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.last_login = timezone.now()
        update_fields = ["failed_login_attempts", "lockout_until", "last_login"]
        if ip_address:
            self.last_login_ip = ip_address
            update_fields.append("last_login_ip")
        self.save(update_fields=update_fields)

    def save(self, *args, **kwargs):
        """Auto-populate username from email with collision safety."""
        if not self.username and self.email:
            base = self.email.split("@")[0][:140]
            candidate = base
            counter = 1
            qs = CustomUser.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(username=candidate).exists():
                candidate = f"{base}_{counter}"
                counter += 1
            self.username = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"


# ---------------------------------------------------------------
#  UserProfile
# ---------------------------------------------------------------

class UserProfile(TimestampMixin, models.Model):
    """Extended profile data for users.

    Separates identity (CustomUser) from profile data.
    Keeps CustomUser lean for auth operations. Profile fields
    vary by role but are stored in one table to avoid unnecessary
    complexity.
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="The user this profile belongs to.",
    )
    cnic_photo = models.ImageField(
        upload_to=user_cnic_photo_path,
        null=True,
        blank=True,
        help_text="Scan of national ID card.",
    )
    degree_photo = models.ImageField(
        upload_to=user_degree_photo_path,
        null=True,
        blank=True,
        help_text="Scan of highest degree.",
    )
    address = models.TextField(
        null=True,
        blank=True,
        help_text="Residential address.",
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Employment start date.",
    )
    specialization = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Subject expertise (primarily for teachers).",
    )
    bio = models.TextField(
        null=True,
        blank=True,
        help_text="Short biography.",
    )
    emergency_contact = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Emergency contact phone number.",
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile: {self.user.full_name}"
