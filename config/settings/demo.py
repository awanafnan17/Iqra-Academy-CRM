from config.settings.base import *

# 1. Host and CSRF Configuration for ngrok and localtunnel
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".ngrok-free.app",
    ".ngrok.io",
    ".loca.lt",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
    "https://*.loca.lt",
    "http://127.0.0.1:8010",
]

# 2. Database Isolation: Force localized SQLite to prevent MySQL data access/leakage
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_demo.sqlite3",
    }
}

# 3. Environment settings to support local HTTP and HTTPS tunneling via ngrok
DEBUG = True
SECRET_KEY = "demo-only-insecure-key-for-external-testing-csrf-hosts-8010"

# Disable SSL redirects and HSTS for local development and ngrok HTTP-to-HTTPS translation compatibility
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# 4. Use console email backend to avoid SMTP calls
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
