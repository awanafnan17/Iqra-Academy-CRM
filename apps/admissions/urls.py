from django.urls import path
from apps.admissions import views

app_name = "admissions"

urlpatterns = [
    path("", views.AdmissionListView.as_view(), name="admission_list"),
    path("<int:pk>/", views.AdmissionDetailView.as_view(), name="admission_detail"),
    path("<int:pk>/review/", views.AdmissionReviewView.as_view(), name="admission_review"),
    path("<int:pk>/approve/", views.AdmissionApproveView.as_view(), name="admission_approve"),
    path("<int:pk>/reject/", views.AdmissionRejectView.as_view(), name="admission_reject"),
    path("<int:pk>/convert/", views.AdmissionConvertView.as_view(), name="admission_convert"),
    path("summary/", views.AdmissionSummaryView.as_view(), name="admission_summary"),
    path("export/", views.AdmissionExportCSVView.as_view(), name="admission_export"),
]
