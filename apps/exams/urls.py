from django.urls import path
from apps.core.decorators import role_required
from apps.exams import views

app_name = "exams"

urlpatterns = [
    # Exam paths
    path("", views.ExamListView.as_view(), name="exam_list"),
    path("create/", views.ExamCreateView.as_view(), name="exam_create"),
    path("<int:pk>/", views.ExamDetailView.as_view(), name="exam_detail"),
    path("<int:pk>/edit/", views.ExamEditView.as_view(), name="exam_edit"),
    path("<int:pk>/review/", views.ExamReviewView.as_view(), name="exam_review"),
    path("<int:pk>/publish/", views.ExamPublishView.as_view(), name="exam_publish"),
    path("<int:pk>/results/entry/", views.ExamResultEntryView.as_view(), name="exam_results_entry"),
    path("<int:pk>/results/bulk-entry/", views.ExamBulkResultEntryView.as_view(), name="exam_results_bulk_entry"),
    path("<int:pk>/statistics/", views.ExamStatisticsView.as_view(), name="exam_statistics"),

    # Grade config (Admin & Principal)
    path("grade-config/", views.grade_config_list, name="grade_config_list"),
    path("grade-config/create/", views.grade_config_create, name="grade_config_create"),
    path("grade-config/<int:pk>/edit/", views.grade_config_edit, name="grade_config_edit"),
]
