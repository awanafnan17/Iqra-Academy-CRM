"""
Shared fixtures and configuration for Iqra Academy CRM QA tests.

Uses Django's StaticLiveServerTestCase via pytest-django for isolated
browser testing against a temporary SQLite database.

Settings are configured in config.settings.test (set by pytest.ini).
"""

import os
import sys

# Add project root to path so Django settings are importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Django settings — pointed to test module by pytest.ini
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

# Allow synchronous ORM calls from Playwright's event loop
# This is required because Playwright runs an async event loop
# and Django's ORM is synchronous.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django  # noqa: E402
django.setup()

# Force single-threaded WSGI server for LiveServerTestCase to prevent concurrent database accesses on SQLite connection
from django.test.testcases import LiveServerThread
from django.core.servers.basehttp import WSGIServer
from django.db import connections

class SingleThreadedWSGIServer(WSGIServer):
    def __init__(self, *args, connections_override=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections_override = connections_override

    def process_request(self, request, client_address):
        if self.connections_override:
            for alias, conn in self.connections_override.items():
                connections[alias] = conn
        super().process_request(request, client_address)

    def _close_connections(self):
        connections.close_all()

    def close_request(self, request):
        self._close_connections()
        super().close_request(request)

LiveServerThread.server_class = SingleThreadedWSGIServer
