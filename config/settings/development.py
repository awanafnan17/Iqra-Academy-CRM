"""
Development settings - DEBUG enabled, verbose logging.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

LOGGING["loggers"]["crm"]["level"] = "DEBUG"  # noqa: F405

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Weaker password hashing for faster tests in development
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
