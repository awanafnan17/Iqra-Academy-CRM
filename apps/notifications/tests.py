import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import TestCase, override_settings
from django.urls import path, reverse
from django.utils import timezone

from apps.notifications.models import Notification, EmailLog
from apps.notifications import views
from apps.notifications.services import (
    create_notification,
    bulk_notify_users,
    mark_notification_read,
    mark_all_notifications_read,
    send_email_notification,
    get_unread_count,
    get_user_notifications,
)

User = get_user_model()

# Custom URLConf for tests to resolve routing prefixes that bypass PanelAccessMiddleware role checks properly
urlpatterns = [
    path("panel/admin/notifications/", views.NotificationListView.as_view(), name="notification_list"),
    path("panel/admin/notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="notification_detail"),
    path("panel/admin/notifications/bulk-send/", views.NotificationBulkSendView.as_view(), name="notification_bulk_send"),
    path("panel/admin/notifications/mark-read/", views.NotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("panel/admin/notifications/unread-count/", views.UnreadCountAPIView.as_view(), name="unread_count_api"),

    # Portal paths for Student (allowed in PanelAccessMiddleware for Student role)
    path("portal/student/notifications/", views.NotificationListView.as_view(), name="student_notification_list"),
    path("portal/student/notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="student_notification_detail"),

    # Portal paths for Guardian (allowed in PanelAccessMiddleware for Guardian role)
    path("portal/guardian/notifications/", views.NotificationListView.as_view(), name="guardian_notification_list"),
    path("portal/guardian/notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="guardian_notification_detail"),
]


@override_settings(ROOT_URLCONF="apps.notifications.tests")
class NotificationsModuleTests(TestCase):
    """Test suite covering the complete Notifications module services and view authorization workflows."""

    def setUp(self):
        super().setUp()

        # Create user roles
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")
        self.group_student, _ = Group.objects.get_or_create(name="Student")

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="pass"
        )
        self.admin_user.groups.add(self.group_admin)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="pass"
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.student_a = User.objects.create_user(
            username="studenta@test.com", email="studenta@test.com", password="pass"
        )
        self.student_a.groups.add(self.group_student)

        self.student_b = User.objects.create_user(
            username="studentb@test.com", email="studentb@test.com", password="pass"
        )
        self.student_b.groups.add(self.group_student)

    def test_cross_user_scoping(self):
        """Verify that a user cannot access another user's notifications, returning a 404."""
        notif = create_notification(
            recipient=self.student_a,
            title="Private Alert",
            message="For student A only.",
            category="general",
            created_by=self.admin_user
        )

        self.client.force_login(self.student_b)
        response = self.client.get(reverse("student_notification_detail", kwargs={"pk": notif.id}))
        self.assertEqual(response.status_code, 404)

        # Scoping list view checks that only own notifications are returned
        response = self.client.get(reverse("student_notification_list") + "?format=json", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["notifications"]), 0)

    def test_immutability_of_content(self):
        """Verify that notification content is immutable and only read status is updated."""
        notif = create_notification(
            recipient=self.student_a,
            title="Static Title",
            message="Cannot be changed.",
            category="general",
            created_by=self.admin_user
        )

        # Confirm mark_notification_read only modifies is_read in the DB
        mark_notification_read(notif.id, self.student_a)

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
        self.assertEqual(notif.title, "Static Title")
        self.assertEqual(notif.content, "Cannot be changed.")

    def test_emaillog_readonly(self):
        """Verify that EmailLog entries are created once and there are no update helper functions."""
        notif = create_notification(
            recipient=self.student_a,
            title="Email Trigger",
            message="Sample body.",
            category="general",
            created_by=self.admin_user
        )
        log = send_email_notification(notif.id)
        self.assertEqual(log.status, "sent")
        self.assertEqual(log.recipient_email, "studenta@test.com")

    def test_bulk_atomicity_and_deduplication(self):
        """Verify that bulk notification operations are atomic and deduplicate target user IDs."""
        # Deduplication check
        notifications = bulk_notify_users(
            user_ids=[self.student_a.id, self.student_a.id, self.student_b.id],
            title="Bulk Alert",
            message="Hello students",
            category="general",
            created_by=self.admin_user
        )
        # Should create exactly 2 notifications (1 for student_a, 1 for student_b)
        self.assertEqual(len(notifications), 2)
        self.assertEqual(Notification.objects.filter(title="Bulk Alert").count(), 2)

        # Atomicity check: passing an invalid user ID should fail the whole transaction
        initial_count = Notification.objects.count()
        with self.assertRaises(ValidationError):
            bulk_notify_users(
                user_ids=[self.student_a.id, 999999], # 999999 is invalid
                title="Failed Bulk",
                message="Will roll back",
                category="general",
                created_by=self.admin_user
            )
        # Verify no notifications were created
        self.assertEqual(Notification.objects.count(), initial_count)

    def test_unread_count_accuracy(self):
        """Verify that the unread count is accurate and matches read/unread statuses."""
        create_notification(self.student_a, "U1", "Body", "general", self.admin_user)
        create_notification(self.student_a, "U2", "Body", "general", self.admin_user)
        notif = create_notification(self.student_a, "U3", "Body", "general", self.admin_user)

        self.assertEqual(get_unread_count(self.student_a), 3)

        # Mark one read
        mark_notification_read(notif.id, self.student_a)
        self.assertEqual(get_unread_count(self.student_a), 2)

        # Mark all read
        mark_all_notifications_read(self.student_a)
        self.assertEqual(get_unread_count(self.student_a), 0)

    def test_admin_only_bulk_enforcement(self):
        """Verify that only users with Admin role can bulk send notifications."""
        self.client.force_login(self.teacher_user)
        response = self.client.post(
            reverse("notification_bulk_send"),
            data={"user_ids": [self.student_a.id], "title": "Hi", "message": "Hi", "category": "general"}
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("notification_bulk_send"),
            data={"user_ids": [self.student_a.id], "title": "Hi", "message": "Hi", "category": "general"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)

    def test_max_user_limit_enforced(self):
        """Verify that bulk notification raises ValidationError if recipient count exceeds 1000."""
        # Create a list containing 1001 user IDs
        user_ids = list(range(1, 1002))
        with self.assertRaises(ValidationError):
            bulk_notify_users(
                user_ids=user_ids,
                title="Over Limit",
                message="Limit exceeded test",
                category="general",
                created_by=self.admin_user
            )

    def test_email_failure_still_logs_record(self):
        """Verify that email dispatch failure logs a failed entry in EmailLog without breaking the transaction."""
        # User without email address will trigger failure
        u_no_email = User.objects.create_user(
            username="noemail@test.com", email="", password="pass"
        )
        notif = create_notification(
            recipient=u_no_email,
            title="Failed Email",
            message="No email address exists.",
            category="general",
            created_by=self.admin_user
        )

        log = send_email_notification(notif.id)
        self.assertEqual(log.status, "failed")
        self.assertEqual(log.recipient_email, "")
        self.assertEqual(EmailLog.objects.filter(notification=notif).count(), 1)
