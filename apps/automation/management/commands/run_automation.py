from django.core.management.base import BaseCommand
from apps.automation.services import (
    run_fee_reminders,
    check_low_attendance,
    run_upcoming_exam_alerts,
)


class Command(BaseCommand):
    help = "Run all automated reminder and alert routines"

    def handle(self, *args, **options):
        self.stdout.write("Running automation alerts...")

        reminders_sent = run_fee_reminders()
        self.stdout.write(self.style.SUCCESS(f"Fee reminders dispatched: {reminders_sent}"))

        flagged_count = check_low_attendance()
        self.stdout.write(self.style.SUCCESS(f"Low attendance updates/flags: {flagged_count}"))

        exams_notified = run_upcoming_exam_alerts()
        self.stdout.write(self.style.SUCCESS(f"Upcoming exam notifications dispatched: {exams_notified}"))

        self.stdout.write(self.style.SUCCESS("SMART ALERT SYSTEM ACTIVE"))
