"""
Custom middleware for the Academy CRM.

PanelAccessMiddleware - enforces role-based panel access at the URL prefix level.
SessionTimeoutMiddleware - enforces idle session timeout per role category.
"""

import logging
import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("crm.security")

# Login URL for redirects
_LOGIN_URL = getattr(settings, "LOGIN_URL", "/accounts/login/")


class PanelAccessMiddleware(MiddlewareMixin):
    """Enforces role-based access at the URL prefix level.

    Each panel prefix maps to a tuple of allowed Django Group
    names. Unauthenticated users are redirected to login.
    Unauthorized users receive Http404 (hiding route existence).
    Superusers bypass all checks.

    This middleware provides panel-level access control. For
    view-level restrictions within a panel (e.g., Admin-only
    views inside admin_panel), use @role_required decorator.
    """
    PANEL_ROLES = {
        "/panel/admin/": ("Admin", "Principal"),
        "/panel/principal/": ("Principal", "Admin"),
        "/panel/teacher/": ("Teacher",),
        "/panel/accounts/": ("Accountant",),
        "/panel/registrar/": ("Registrar",),
        "/portal/student/": ("Student",),
        "/portal/guardian/": ("Guardian",),
    }


    def process_request(self, request):
        path = request.path

        for prefix, allowed_roles in self.PANEL_ROLES.items():
            if not path.startswith(prefix):
                continue

            # Unauthenticated: redirect to login
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(
                    path,
                    login_url=_LOGIN_URL,
                )

            # Superuser bypasses role checks
            if request.user.is_superuser:
                return None

            # Check group membership
            roles = allowed_roles
            normalized_path = path if path.endswith("/") else (path + "/")
            if normalized_path.startswith("/panel/admin/pdf-comparison/"):
                roles = allowed_roles + ("Registrar",)
            elif normalized_path.startswith("/panel/admin/academics/sessions/") and normalized_path.endswith("/enrollments/"):
                roles = allowed_roles + ("Registrar", "Teacher")
            elif normalized_path.startswith("/panel/admin/reports/student/") and normalized_path.endswith("/transcript/pdf/"):
                roles = allowed_roles + ("Registrar",)

            if not request.user.groups.filter(
                name__in=roles
            ).exists():
                logger.warning(
                    "Panel access denied: user=%s path=%s "
                    "allowed_roles=%s",
                    request.user.pk,
                    path,
                    roles,
                )
                raise Http404

            # Access granted
            return None

        # Path does not match any panel prefix; let it through
        return None


class SessionTimeoutMiddleware(MiddlewareMixin):
    """Enforces idle session timeout.

    Tracks ``_last_activity`` timestamp in session data. If the
    user has been idle longer than the threshold, the session is
    flushed and the user is redirected to login.

    Timeout thresholds:
    - Staff panels (Admin, Principal, Accountant, Registrar, Teacher): 30 minutes
    - Portal users (Student, Guardian): 15 minutes

    AJAX requests receive a JSON response with redirect URL
    and 401 status instead of an HTML redirect.
    """

    STAFF_TIMEOUT = 30 * 60   # 30 minutes in seconds
    PORTAL_TIMEOUT = 15 * 60  # 15 minutes in seconds

    # Paths that should skip timeout checks
    EXEMPT_PATHS = (
        _LOGIN_URL,
        "/accounts/logout/",
        "/admin/",
    )

    PORTAL_PREFIXES = (
        "/portal/student/",
        "/portal/guardian/",
    )

    def process_request(self, request):
        # Skip for unauthenticated users and exempt paths
        if not request.user.is_authenticated:
            return None

        for exempt in self.EXEMPT_PATHS:
            if request.path.startswith(exempt):
                return None

        now = time.time()
        last_activity = request.session.get("_last_activity")

        if last_activity is not None:
            idle_seconds = now - last_activity
            timeout = self._get_timeout(request.path)

            if idle_seconds > timeout:
                logger.info(
                    "Session timeout: user=%s idle=%ds threshold=%ds",
                    request.user.pk,
                    int(idle_seconds),
                    timeout,
                )
                logout(request)

                # AJAX requests get JSON response
                if self._is_ajax(request):
                    return JsonResponse(
                        {
                            "redirect": _LOGIN_URL,
                            "reason": "timeout",
                        },
                        status=401,
                    )

                return redirect(f"{_LOGIN_URL}?timeout=1&next={request.path}")

        # Update last activity timestamp
        request.session["_last_activity"] = now
        return None

    def _get_timeout(self, path):
        """Return timeout threshold based on URL path."""
        for prefix in self.PORTAL_PREFIXES:
            if path.startswith(prefix):
                return self.PORTAL_TIMEOUT
        return self.STAFF_TIMEOUT

    @staticmethod
    def _is_ajax(request):
        """Check if the request is an AJAX call."""
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"


class SecurityHardeningMiddleware(MiddlewareMixin):
    """Appends security headers (CSP, Referrer-Policy, X-Frame-Options) to all HTTP responses."""

    def process_response(self, request, response):
        # 1. Content Security Policy
        csp_policy = getattr(
            settings,
            "CONTENT_SECURITY_POLICY",
            (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https://images.unsplash.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "frame-src 'none'; "
                "connect-src 'self';"
            )
        )
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = csp_policy

        # 2. Referrer Policy
        referrer_policy = getattr(settings, "SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
        if "Referrer-Policy" not in response:
            response["Referrer-Policy"] = referrer_policy

        # 3. X-Frame-Options
        x_frame_options = getattr(settings, "X_FRAME_OPTIONS", "DENY")
        if "X-Frame-Options" not in response:
            response["X-Frame-Options"] = x_frame_options

        return response

