"""
User management service layer - handles user updates, lock controls, role assignments, password resets, and teacher assignments.
All write operations run inside transaction.atomic() with model-level validation and audit logging.
"""

import logging
from datetime import timedelta
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from apps.core.services import (
    BaseService,
    transactional_service,
    NotFoundError,
    BusinessRuleViolation,
)
from apps.accounts.models import CustomUser
from apps.academics.models import Session, TeacherAssignment, Subject

logger = logging.getLogger("crm.accounts")


class UserService(BaseService):
    """Orchestrates CustomUser state modifications, security controls, and teacher assignments."""

    @classmethod
    @transactional_service
    def toggle_user_activation(cls, user_id, active, admin_user, ip_address=None, user_agent=None):
        """Activates or deactivates a user account."""
        user = CustomUser.objects.filter(pk=user_id).first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")

        if user.pk == admin_user.pk:
            raise BusinessRuleViolation("You cannot activate or deactivate your own account.")

        old_active = user.is_active
        old_status = user.status

        new_active = bool(active)
        new_status = "Active" if new_active else "Inactive"

        if old_active == new_active and old_status == new_status:
            return user

        user.is_active = new_active
        user.status = new_status
        cls.validate_instance(user)
        user.save(update_fields=["is_active", "status"])

        cls.audit_on_commit(
            user=admin_user,
            action="update",
            model_name="accounts.CustomUser",
            object_id=user.pk,
            changes={
                "is_active": {"old": old_active, "new": new_active},
                "status": {"old": old_status, "new": new_status},
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        cls.log_structured(
            logging.INFO, "toggle_user_activation", "SUCCESS",
            f"Toggled activation for user {user.email} to {new_status}",
            f"user_id={user.pk}"
        )
        return user

    @classmethod
    @transactional_service
    def toggle_user_lock(cls, user_id, lock, admin_user, ip_address=None, user_agent=None):
        """Locks or unlocks a user account."""
        user = CustomUser.objects.filter(pk=user_id).first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")

        if user.pk == admin_user.pk:
            raise BusinessRuleViolation("You cannot lock or unlock your own account.")

        old_attempts = user.failed_login_attempts
        old_lockout = user.lockout_until

        if lock:
            # Lockout the user for 24 hours
            user.failed_login_attempts = 5
            user.lockout_until = timezone.now() + timedelta(days=1)
        else:
            # Unlock the user
            user.failed_login_attempts = 0
            user.lockout_until = None

        cls.validate_instance(user)
        user.save(update_fields=["failed_login_attempts", "lockout_until"])

        cls.audit_on_commit(
            user=admin_user,
            action="update",
            model_name="accounts.CustomUser",
            object_id=user.pk,
            changes={
                "failed_login_attempts": {"old": old_attempts, "new": user.failed_login_attempts},
                "lockout_until": {"old": str(old_lockout) if old_lockout else None, "new": str(user.lockout_until) if user.lockout_until else None},
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        state = "LOCKED" if lock else "UNLOCKED"
        cls.log_structured(
            logging.INFO, "toggle_user_lock", "SUCCESS",
            f"Toggled lock status for user {user.email} to {state}",
            f"user_id={user.pk}"
        )
        return user

    @classmethod
    @transactional_service
    def reset_user_password(cls, user_id, new_password, admin_user, ip_address=None, user_agent=None):
        """Resets the password for a user account."""
        if not new_password or len(new_password) < 6:
            raise BusinessRuleViolation("Password must be at least 6 characters long.")

        user = CustomUser.objects.filter(pk=user_id).first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")

        user.set_password(new_password)
        # Clearing failed attempts upon password reset is good practice
        user.failed_login_attempts = 0
        user.lockout_until = None
        user.save()

        cls.audit_on_commit(
            user=admin_user,
            action="password_change",
            model_name="accounts.CustomUser",
            object_id=user.pk,
            changes={"password_reset": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        cls.log_structured(
            logging.INFO, "reset_user_password", "SUCCESS",
            f"Reset password for user {user.email}",
            f"user_id={user.pk}"
        )
        return user

    @classmethod
    @transactional_service
    def assign_user_role(cls, user_id, role_name, admin_user, ip_address=None, user_agent=None):
        """Assigns a selected Django Group / Role to a user."""
        user = CustomUser.objects.filter(pk=user_id).first()
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found.")

        if user.pk == admin_user.pk:
            raise BusinessRuleViolation("You cannot change your own role.")

        # Validate that group exists
        group = Group.objects.filter(name=role_name).first()
        if not group:
            raise NotFoundError(f"Role '{role_name}' does not exist.")

        old_roles = list(user.groups.values_list("name", flat=True))
        if len(old_roles) == 1 and old_roles[0] == role_name:
            return user  # No change

        # Atomically update groups
        user.groups.clear()
        user.groups.add(group)

        cls.audit_on_commit(
            user=admin_user,
            action="update",
            model_name="accounts.CustomUser",
            object_id=user.pk,
            changes={"roles": {"old": old_roles, "new": [role_name]}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        cls.log_structured(
            logging.INFO, "assign_user_role", "SUCCESS",
            f"Assigned role {role_name} to user {user.email}",
            f"user_id={user.pk}"
        )
        return user

    @classmethod
    @transactional_service
    def assign_teacher_session(cls, teacher_id, session_id, subject_id=None, admin_user=None, ip_address=None, user_agent=None):
        """Links a teacher to a session (and optionally a subject)."""
        teacher = CustomUser.objects.filter(pk=teacher_id).first()
        if not teacher:
            raise NotFoundError(f"Teacher with ID {teacher_id} not found.")

        # Verify teacher role
        if not teacher.groups.filter(name="Teacher").exists():
            raise BusinessRuleViolation(f"User {teacher.email} is not a Teacher.")

        session = Session.objects.filter(pk=session_id).first()
        if not session:
            raise NotFoundError(f"Session with ID {session_id} not found.")

        subject = None
        if subject_id:
            subject = Subject.objects.filter(pk=subject_id).first()
            if not subject:
                raise NotFoundError(f"Subject with ID {subject_id} not found.")

        # Retrieve or create TeacherAssignment
        assignment, created = TeacherAssignment.objects.get_or_create(
            teacher=teacher,
            session=session,
            subject=subject,
            defaults={"is_active": True},
        )

        if not created and not assignment.is_active:
            assignment.is_active = True
            cls.validate_instance(assignment)
            assignment.save(update_fields=["is_active"])

        cls.audit_on_commit(
            user=admin_user,
            action="create" if created else "update",
            model_name="academics.TeacherAssignment",
            object_id=assignment.pk,
            changes={
                "teacher_id": teacher.pk,
                "session_id": session.pk,
                "subject_id": subject.pk if subject else None,
                "is_active": True,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        cls.log_structured(
            logging.INFO, "assign_teacher_session", "SUCCESS",
            f"Assigned teacher {teacher.email} to session {session.name}",
            f"assignment_id={assignment.pk}"
        )
        return assignment
