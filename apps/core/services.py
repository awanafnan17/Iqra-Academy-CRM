"""
Core service utilities including BaseService and standard exception hierarchy.

Provides structural helper methods for transaction control, validation,
and commits without any application-specific logic.
"""

import functools
import json
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone
from apps.core.models import AuditLog

logger = logging.getLogger("crm.services")


# -----------------------------------------------------------------------------
# Exception Hierarchy
# -----------------------------------------------------------------------------

class BaseDomainError(Exception):
    """Base exception for all system-wide domain failures."""
    pass


class DomainValidationError(BaseDomainError):
    """Raised when parameters fail model or business rule validation checks."""
    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


class NotFoundError(BaseDomainError):
    """Raised when a queried entity does not exist in the database."""
    pass


class BusinessRuleViolation(BaseDomainError):
    """Raised when a requested action violates CRM business rules."""
    pass


class DatabaseConflictError(BaseDomainError):
    """Raised when a database unique constraint or foreign key fails."""
    pass


# -----------------------------------------------------------------------------
# Transaction wrapper decorator
# -----------------------------------------------------------------------------

def transactional_service(func):
    """Decorator to wrap service functions in a transaction block.

    Intercepts ONLY:
    - Django ValidationError (model validation failures)
    - IntegrityError (unique constraint, FK violations)

    All other exceptions propagate unmodified.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except DjangoValidationError as e:
            errors = e.message_dict if hasattr(e, "message_dict") else e.messages
            raise DomainValidationError(errors)
        except IntegrityError:
            raise DatabaseConflictError(
                "A database constraint was violated. "
                "The record may already exist or a referenced record is missing."
            )
    return wrapper


# -----------------------------------------------------------------------------
# BaseService
# -----------------------------------------------------------------------------

class BaseService:
    """Foundational base service providing transaction, validation, and audit helpers."""

    @staticmethod
    def now():
        """Returns the current local datetime, timezone-aware."""
        return timezone.localtime()

    @staticmethod
    def today():
        """Returns the current local date."""
        return timezone.localdate()

    @staticmethod
    def validate_instance(instance):
        """Validates a Django model instance before it is saved."""
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            errors = e.message_dict if hasattr(e, "message_dict") else e.messages
            raise DomainValidationError(errors)

    @staticmethod
    def audit_on_commit(user, action, model_name, object_id, changes=None, ip_address=None, user_agent=None):
        """Queues an audit entry to be saved after the transaction commits successfully.

        Uses transaction.on_commit to ensure audit records are only
        written when the parent transaction succeeds.
        """
        def record_audit():
            changes_str = None
            if changes is not None:
                if isinstance(changes, (dict, list)):
                    changes_str = json.dumps(changes)
                else:
                    changes_str = str(changes)

            AuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=str(object_id) if object_id is not None else None,
                changes=changes_str,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=timezone.now(),
            )

        if transaction.get_connection().in_atomic_block:
            transaction.on_commit(record_audit)
        else:
            record_audit()

    @classmethod
    def log_structured(cls, level, method, status, message, context=None):
        """Logs a standardized service event."""
        log_message = f"[{cls.__name__}][{method}][{status}] {message}"
        if context:
            log_message += f" | Context: {context}"
        logger.log(level, log_message)
