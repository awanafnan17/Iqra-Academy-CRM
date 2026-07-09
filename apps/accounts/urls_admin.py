"""
Administrative user management URL patterns.
Included by config or master urls_admin.py with namespace 'users'.
"""

from django.urls import path
from apps.accounts import views_admin

app_name = "users"

urlpatterns = [
    path("", views_admin.user_list, name="user_list"),
    path("create/", views_admin.user_create, name="user_create"),
    path("<int:pk>/edit/", views_admin.user_edit, name="user_edit"),
    path("<int:pk>/toggle-activation/", views_admin.user_toggle_activation, name="user_toggle_activation"),
    path("<int:pk>/toggle-lock/", views_admin.user_toggle_lock, name="user_toggle_lock"),
    path("<int:pk>/reset-password/", views_admin.user_reset_password, name="user_reset_password"),
    path("<int:pk>/assign-role/", views_admin.user_assign_role, name="user_assign_role"),
    path("<int:pk>/assign-session/", views_admin.user_assign_session, name="user_assign_session"),
]
