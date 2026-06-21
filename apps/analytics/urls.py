from django.urls import path
from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("revenue-trend/", views.api_revenue_trend, name="api_revenue_trend"),
    path("attendance-trend/", views.api_attendance_trend, name="api_attendance_trend"),
    path("enrollment-growth/", views.api_enrollment_growth, name="api_enrollment_growth"),
    path("lead-funnel/", views.api_lead_funnel, name="api_lead_funnel"),
    path("aging-report/", views.api_aging_report, name="api_aging_report"),
]
