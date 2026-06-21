"""
Principal panel URL configuration.

Accessible by Principal role.
Panel-level access enforced by PanelAccessMiddleware.
"""

from django.urls import path
from apps.dashboard import views as dashboard_views

app_name = "principal_panel"

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_views.principal_dashboard, name="dashboard"),
]
