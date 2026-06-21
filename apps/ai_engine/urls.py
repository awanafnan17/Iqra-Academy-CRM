"""
AI engine app URL patterns.

Included by admin_panel under prefix 'ai/'.
"""

from django.urls import path

from apps.ai_engine import views

app_name = "ai_engine"

urlpatterns = [
    path("predictions/", views.prediction_list, name="prediction_list"),
    path("predictions/<int:pk>/", views.prediction_detail, name="prediction_detail"),
    path("predictions/<int:pk>/acknowledge/", views.prediction_acknowledge, name="prediction_acknowledge"),
    path("models/", views.model_version_list, name="model_version_list"),
    path("dropout-risk/", views.dropout_risk_dashboard, name="dropout_risk_dashboard"),
]
