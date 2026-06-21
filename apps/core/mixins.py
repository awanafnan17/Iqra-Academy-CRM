"""
Class-based view mixins for the Academy CRM.

Provides RoleRequiredMixin and PostRequiredMixin for
enforcing RBAC and HTTP method restrictions on CBVs.
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

logger = logging.getLogger("crm.security")


class RoleRequiredMixin(LoginRequiredMixin):
    """Mixin that enforces Django Group membership on class-based views.

    Subclasses must set ``required_roles`` to a list of allowed
    Django Group names. Superusers bypass the check. Returns
    Http404 on unauthorized access to hide route existence.

    Usage::

        class MyView(RoleRequiredMixin, View):
            required_roles = ["Admin", "Principal"]
    """

    required_roles = []
    raise_exception = False  # Never raise 403; redirect to login

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles unauthenticated users
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Superuser bypasses role check
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.groups.filter(
            name__in=self.required_roles
        ).exists():
            logger.warning(
                "CBV access denied: user=%s path=%s required=%s",
                request.user.pk,
                request.path,
                self.required_roles,
            )
            raise Http404

        return super().dispatch(request, *args, **kwargs)


class PostRequiredMixin:
    """Mixin that rejects non-POST requests with Http404.

    Place before View in MRO but after RoleRequiredMixin
    so that auth is checked before the method check.

    Usage::

        class PaymentCreateView(RoleRequiredMixin, PostRequiredMixin, View):
            required_roles = ["Accountant"]
    """

    def dispatch(self, request, *args, **kwargs):
        if request.method != "POST":
            raise Http404
        return super().dispatch(request, *args, **kwargs)
