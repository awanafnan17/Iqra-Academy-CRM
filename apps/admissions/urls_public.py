from django.urls import path
from apps.admissions import views

app_name = "admissions_public"

urlpatterns = [
    path("", views.PublicAdmissionFormView.as_view(), name="apply"),
    path("success/", views.PublicSuccessView.as_view(), name="success"),
]
