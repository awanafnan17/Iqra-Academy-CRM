# Gunicorn configuration file for IICE ERP production deployment.
import multiprocessing
import os

# Bind address and port
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")

# Number of worker processes (2 * CPU cores + 1)
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Thread count per worker process for thread pool
threads = int(os.getenv("GUNICORN_THREADS", 2))

# Worker class - gthread handles concurrent requests efficiently
worker_class = "gthread"

# Request timeout limit in seconds
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))

# Keep alive connection timeout
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# Prevent memory leaks by restarting workers after a max number of requests
max_requests = 1000
max_requests_jitter = 50

# WSGI application path
wsgi_app = "config.wsgi:application"

# Daemon mode (disabled by default so container/process manager can control it)
daemon = False

# Logging settings
loglevel = "info"
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"

# Capture stdout/stderr in error log
capture_output = True

# Process name tag
proc_name = "iice_erp_production"
