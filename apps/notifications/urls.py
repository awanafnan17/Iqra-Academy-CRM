from django.urls import path
from apps.core.decorators import role_required
from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    # Notification core endpoints
    path("", views.NotificationListView.as_view(), name="notification_list"),
    path("<int:pk>/", views.NotificationDetailView.as_view(), name="notification_detail"),
    path("mark-read/", views.NotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("unread-count/", views.UnreadCountAPIView.as_view(), name="unread_count_api"),
    path("bulk-send/", views.NotificationBulkSendView.as_view(), name="notification_bulk_send"),

    # Templates (Admin only)
    path("templates/", role_required("Admin")(views.template_list), name="template_list"),
    path("templates/create/", role_required("Admin")(views.template_create), name="template_create"),
    path("templates/<int:pk>/edit/", role_required("Admin")(views.template_edit), name="template_edit"),

    # Email logs (Admin only, read-only)
    path("email-logs/", role_required("Admin")(views.email_log_list), name="email_log_list"),
]
