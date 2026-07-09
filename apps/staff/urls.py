from django.urls import path
from apps.staff import views

app_name = "staff"

urlpatterns = [
    path("", views.FacultyListView.as_view(), name="faculty_list"),
    path("create/", views.FacultyCreateView.as_view(), name="faculty_create"),
    path("<int:pk>/assign/", views.FacultyAssignSessionView.as_view(), name="faculty_assign"),
    path("<int:pk>/edit/", views.FacultyUpdateView.as_view(), name="faculty_edit"),
]
