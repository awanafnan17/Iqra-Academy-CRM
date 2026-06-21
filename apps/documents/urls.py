from django.urls import path
from django.views.generic import RedirectView
from apps.documents import views

app_name = "documents"

urlpatterns = [
    path("", RedirectView.as_view(url="jobs/", permanent=False)),
    path("jobs/", views.pdf_comparison, name="comparison_job_list"),
    path("jobs/create/", views.pdf_comparison, name="comparison_job_create"),
    path("jobs/<int:pk>/", views.pdf_comparison, name="comparison_job_detail"),
    path("jobs/<int:pk>/results/", views.pdf_comparison, name="comparison_results"),
    path("preview/export/", views.export_preview_csv, name="export_preview_csv"),
]
