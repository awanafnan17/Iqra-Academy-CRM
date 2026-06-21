"""
Accounts admin - CustomUser and UserProfile.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom user admin extending Django UserAdmin.

    Adds a CRM Fields fieldset for academy-specific fields.
    """

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = UserAdmin.fieldsets + (
        (
            "CRM Fields",
            {
                "fields": (
                    "phone",
                    "cnic",
                    "profile_photo",
                    "status",
                    "failed_login_attempts",
                    "lockout_until",
                    "last_login_ip",
                ),
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin with read-only timestamps."""

    list_display = (
        "user",
        "specialization",
        "joining_date",
        "emergency_contact",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "specialization",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("user",)
