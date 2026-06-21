"""
IICE - Base Settings
Shared settings for all environments.
"""

import os
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=lambda v: str(v).lower() in ("true", "1", "yes"))
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.academics",
    "apps.students",
    "apps.finance",
    "apps.attendance",
    "apps.exams",
    "apps.notifications",
    "apps.documents",
    "apps.ai_engine",
    "apps.dashboard",
    "apps.portals",
    "apps.analytics",
    "apps.automation",
    "apps.staff",
    "apps.reports",
    "apps.admissions",
    "apps.achievements",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.PanelAccessMiddleware",
    "apps.core.middleware.SessionTimeoutMiddleware",
    "apps.core.middleware.SecurityHardeningMiddleware",
]

ROOT_URLCONF = "config.urls"
AUTH_USER_MODEL = "accounts.CustomUser"

# Authentication redirects
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/post-login/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------
# Database
# SQLite :memory: for tests — MySQL for dev / production.
# ---------------------------------------------------------------
import sys as _sys

if 'test' in _sys.argv:
    # Force SQLite in-memory so tests NEVER touch MySQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='iqra_academy'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
    # Only install pymysql shim when we actually need MySQL
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass


# Password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Session and cookie security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Strict"

# Security headers
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
if DEBUG:
    SECURE_SSL_REDIRECT = False
else:
    SECURE_SSL_REDIRECT = True

# HSTS
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "crm.log",
            "formatter": "verbose",
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "security.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "crm": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "crm.security": {
            "handlers": ["console", "file", "security_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email Configuration
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND") or config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST") or config("EMAIL_HOST", default="localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or config("EMAIL_PORT", default=587))
EMAIL_USE_TLS = (os.getenv("EMAIL_USE_TLS") or config("EMAIL_USE_TLS", default="True")) == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER") or config("EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") or config("EMAIL_HOST_PASSWORD", default=None)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL") or config("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

