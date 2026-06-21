from django.core.management.base import BaseCommand
from django.db import models
from apps.students.models import Student, Enrollment

class Command(BaseCommand):
    help = "Assign roll numbers to students missing roll numbers sequentially based on session prefix."

    def handle(self, *args, **options):
        students = Student.objects.filter(
            models.Q(roll_number__isnull=True) | models.Q(roll_number="")
        )
        count_updated = 0

        for student in students:
            # Get earliest enrollment
            enrollment = student.enrollments.order_by("registration_date", "id").first()
            if enrollment:
                session = enrollment.session
                prefix = session.roll_prefix or session.code or "STUD"

                # Count existing enrollments in the same session prior to this one
                count = Enrollment.all_objects.filter(session=session, id__lt=enrollment.id).count()
                student.roll_number = f"{prefix}-{count + 1:02d}"
                student.save(update_fields=["roll_number"])
                count_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned roll number {student.roll_number} to {student.full_name}"
                    )
                )
            else:
                # Fallback for students with no enrollments
                student.roll_number = f"STUD-{student.id:02d}"
                student.save(update_fields=["roll_number"])
                count_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned fallback roll number {student.roll_number} to {student.full_name}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {count_updated} students.")
        )
