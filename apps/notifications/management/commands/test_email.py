from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.notifications.services import send_email_notification

class Command(BaseCommand):
    help = "Sends a real SMTP test email to verify domain mail settings and HTML rendering."

    def add_arguments(self, parser):
        parser.add_argument("recipient", type=str, help="Email address of the recipient")

    def handle(self, *args, **options):
        recipient_email = options["recipient"]
        User = get_user_model()

        # Retrieve or create a test recipient user in the DB
        user, created = User.objects.get_or_create(
            username="test_email_recipient_user",
            defaults={
                "email": recipient_email,
                "first_name": "Test",
                "last_name": "Recipient",
            }
        )
        if not created and user.email != recipient_email:
            user.email = recipient_email
            user.save(update_fields=["email"])

        # Create a mock test notification
        notif = Notification.objects.create(
            recipient=user,
            category="general",
            title="IICE ERP SMTP Verification Email",
            content="Congratulations! The real domain-based SMTP email system is fully functional and correctly configured. HTML rendering is active and operational.",
        )

        self.stdout.write(f"Sending test email notification to {recipient_email}...")
        log = send_email_notification(notif.id)

        if log.status == "sent":
            self.stdout.write(self.style.SUCCESS(f"Successfully sent test email! Log ID: {log.id}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to send email. Error: {log.error_message}"))

        # Clean up database entries created for the test
        notif.delete()
        if created:
            user.delete()
