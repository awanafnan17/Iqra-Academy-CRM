"""
IICE - Test Settings
Isolated test configuration that never touches MySQL.
"""

from config.settings.base import *  # noqa: F401,F403

# ---------------------------------------------------------------
# Database: SQLite in-memory — never connect to MySQL
# ---------------------------------------------------------------
import os
DB_NAME = os.environ.get("QA_DB_NAME", "db_test.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / DB_NAME,
        "OPTIONS": {
            "timeout": 60,
            "check_same_thread": False,
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# Test middleware to intercept and mock notification AJAX requests to prevent database/session lock contention during tests
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class TestMuteNotificationsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.META.get("SERVER_NAME") == "testserver":
            return None
        import os
        if os.environ.get("QA_REAL_NETWORK") == "1":
            return None
        path = request.path
        if "/notifications/unread-count/" in path:
            return JsonResponse({"unread_count": 0})
        if "/notifications/" in path and (request.GET.get("format") == "json" or request.headers.get("X-Requested-With") == "XMLHttpRequest"):
            if "mark-read" in path:
                return JsonResponse({"status": "success"})
            return JsonResponse({"notifications": []})
        
        # Intercept and mock analytics endpoints
        if "/api/analytics/revenue-trend/" in path:
            dummy_data = [{"tuition": 0, "late_fees": 0, "net": 0} for _ in range(12)]
            return JsonResponse({"status": "success", "data": dummy_data})
        if "/api/analytics/attendance-trend/" in path:
            return JsonResponse({"status": "success", "data": []})
        if "/api/analytics/enrollment-growth/" in path:
            dummy_data = [{"new_enrollments": 0, "cumulative_enrollments": 0} for _ in range(12)]
            return JsonResponse({"status": "success", "data": dummy_data})
        if "/api/analytics/lead-funnel/" in path:
            dummy_data = {
                "funnel": [
                    {"status": "New", "count": 0},
                    {"status": "Contacted", "count": 0},
                    {"status": "Interested", "count": 0},
                    {"status": "Converted", "count": 0},
                    {"status": "Lost", "count": 0}
                ]
            }
            return JsonResponse({"status": "success", "data": dummy_data})
        if "/api/analytics/aging-report/" in path:
            dummy_data = {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}
            return JsonResponse({"status": "success", "data": dummy_data})
        if "/api/analytics/" in path:
            return JsonResponse({"status": "success", "data": {}})
            
        return None

# Prepend to MIDDLEWARE imported from base settings
MIDDLEWARE = ["config.settings.test.TestMuteNotificationsMiddleware"] + MIDDLEWARE



# ---------------------------------------------------------------
# Security: Disable for test live server (serves HTTP only)
# ---------------------------------------------------------------
DEBUG = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ---------------------------------------------------------------
# Performance: Fast password hashing for test speed
# ---------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ---------------------------------------------------------------
# Email: In-memory backend
# ---------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ---------------------------------------------------------------
# Cache: Local memory for test isolation
# ---------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# ---------------------------------------------------------------
# Logging: Reduce noise during tests
# ---------------------------------------------------------------
import logging
logging.disable(logging.WARNING)

# ---------------------------------------------------------------
# Static files: Use finder for tests (no collectstatic needed)
# ---------------------------------------------------------------
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
