"""
Core RBAC decorators for the Academy CRM.

Provides role_required, post_required, and throttle decorators
for view-level access control, HTTP method enforcement, and
rate limiting.
"""

import functools
import logging
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import Http404, JsonResponse

logger = logging.getLogger("crm.security")


def role_required(*group_names):
    """Decorator that enforces Django Group membership.

    Wraps login_required internally. Checks if the authenticated
    user belongs to at least one of the specified groups. Superusers
    bypass the group check. Returns Http404 on failure to hide
    route existence.

    Usage:
        @role_required("Admin")
        @role_required("Admin", "Principal")
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Superuser bypasses all group checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not request.user.groups.filter(
                name__in=group_names
            ).exists():
                logger.warning(
                    "Access denied: user=%s path=%s ip=%s required=%s",
                    request.user.pk,
                    request.path,
                    _get_client_ip(request),
                    group_names,
                )
                raise Http404
            return view_func(request, *args, **kwargs)

        # Wrap with login_required so unauthenticated users
        # are redirected to the login page automatically.
        return login_required(wrapper)

    return decorator


def post_required(view_func):
    """Decorator that rejects non-POST requests with Http404.

    Prevents state-mutating endpoints from responding to GET
    requests. Must be applied INSIDE role_required so that
    auth is checked before the method check.

    Usage:
        @role_required("Accountant")
        @post_required
        def create_payment(request): ...
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != "POST":
            raise Http404
        return view_func(request, *args, **kwargs)
    return wrapper


def throttle(max_calls, period_seconds):
    """Decorator for database-backed rate limiting.

    Uses Django cache framework (LocMemCache for dev,
    DatabaseCache for production). No Redis required.

    Args:
        max_calls: Maximum number of calls allowed in the period.
        period_seconds: Time window in seconds.

    Returns 429 Too Many Requests if the limit is exceeded.
    AJAX requests receive JSON. Regular requests receive plain text.

    Usage:
        @throttle(max_calls=10, period_seconds=60)
        def sensitive_view(request): ...
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Build a cache key from user ID and view name
            user_id = request.user.pk if request.user.is_authenticated else "anon"
            ip = _get_client_ip(request)
            key = f"throttle:{user_id}:{ip}:{view_func.__name__}"

            # Retrieve current request timestamps from cache
            timestamps = cache.get(key, [])
            now = time.time()

            # Remove expired timestamps
            cutoff = now - period_seconds
            timestamps = [ts for ts in timestamps if ts > cutoff]

            if len(timestamps) >= max_calls:
                logger.warning(
                    "Rate limit exceeded: user=%s ip=%s view=%s",
                    user_id, ip, view_func.__name__,
                )
                retry_after = int(timestamps[0] - cutoff) + 1
                if _is_ajax(request):
                    response = JsonResponse(
                        {"status": "error", "message": "Too many requests."},
                        status=429,
                    )
                else:
                    from django.http import HttpResponse
                    response = HttpResponse(
                        "Too many requests. Please try again later.",
                        status=429,
                        content_type="text/plain",
                    )
                response["Retry-After"] = str(retry_after)
                return response

            timestamps.append(now)
            cache.set(key, timestamps, timeout=period_seconds + 10)
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def permission_required(module, action):
    """Enforce granular module-level action permissions.

    Wraps login_required internally. Checks if the authenticated
    user has permission for the specified module and action.
    Returns Http404 on failure to keep endpoints secure.

    Usage:
        @permission_required("finance", "create")
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from apps.core.permission_service import has_permission
            if not has_permission(request.user, module, action):
                logger.warning(
                    "Permission denied: user=%s path=%s ip=%s module=%s action=%s",
                    request.user.pk if request.user else "anon",
                    request.path,
                    _get_client_ip(request),
                    module,
                    action,
                )
                raise Http404
            return view_func(request, *args, **kwargs)

        # Wrap with login_required to ensure user is logged in
        return login_required(wrapper)

    return decorator


# -------------------------------------------------------------------
#  Internal helpers
# -------------------------------------------------------------------


def _get_client_ip(request):
    """Extract client IP from request headers."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _is_ajax(request):
    """Check if the request is an AJAX call."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"
