import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.academics.models import Session
from apps.students.models import Student, Guardian, Enrollment
from apps.finance.models import Payment

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds a demo database with synthetic records and role accounts for safe external testing."

    def handle(self, *args, **options):
        self.stdout.write("Running baseline system seed (groups, permissions)...")
        call_command("seed_system")

        self.stdout.write("Seeding demo accounts and synthetic database records...")
        
        # Define demo accounts
        demo_accounts = [
            {
                "email": "admin@iqra.test",
                "first_name": "Demo",
                "last_name": "Admin",
                "role": "Admin",
                "is_staff": True,
                "is_superuser": True
            },
            {
                "email": "principal@iqra.test",
                "first_name": "Demo",
                "last_name": "Principal",
                "role": "Principal",
                "is_staff": True,
                "is_superuser": False
            },
            {
                "email": "teacher@iqra.test",
                "first_name": "Demo",
                "last_name": "Teacher",
                "role": "Teacher",
                "is_staff": True,
                "is_superuser": False
            },
            {
                "email": "accountant@iqra.test",
                "first_name": "Demo",
                "last_name": "Accountant",
                "role": "Accountant",
                "is_staff": True,
                "is_superuser": False
            },
            {
                "email": "registrar@iqra.test",
                "first_name": "Demo",
                "last_name": "Registrar",
                "role": "Registrar",
                "is_staff": True,
                "is_superuser": False
            },
            {
                "email": "student@iqra.test",
                "first_name": "Demo",
                "last_name": "Student",
                "role": "Student",
                "is_staff": False,
                "is_superuser": False
            },
            {
                "email": "guardian@iqra.test",
                "first_name": "Demo",
                "last_name": "Guardian",
                "role": "Guardian",
                "is_staff": False,
                "is_superuser": False
            }
        ]

        with transaction.atomic():
            # Create user objects
            users = {}
            for acc in demo_accounts:
                user, created = User.objects.get_or_create(
                    email=acc["email"],
                    defaults={
                        "first_name": acc["first_name"],
                        "last_name": acc["last_name"],
                        "is_staff": acc["is_staff"],
                        "is_superuser": acc["is_superuser"],
                        "status": "Active",
                        "is_active": True
                    }
                )
                user.set_password("demopass123")
                user.save()
                
                # Assign role group
                group = Group.objects.filter(name=acc["role"]).first()
                if group:
                    user.groups.add(group)
                    
                users[acc["role"]] = user
                if created:
                    self.stdout.write(f"  Created user account: {acc['email']} (Role: {acc['role']})")
                else:
                    self.stdout.write(f"  Verified / Reset user account: {acc['email']} (Role: {acc['role']})")

            # Create synthetic records
            self.stdout.write("Creating synthetic CRM records...")
            
            # 1. Session
            session, _ = Session.objects.get_or_create(
                code="DEMO2026",
                defaults={
                    "name": "Demo Session 2026",
                    "status": "Active",
                    "fee": Decimal("1500.00"),
                    "registration_fee": Decimal("250.00"),
                    "start_date": datetime.date(2026, 1, 1),
                    "end_date": datetime.date(2026, 12, 31)
                }
            )
            
            # 2. Student Profile
            student, _ = Student.objects.get_or_create(
                email="student@iqra.test",
                defaults={
                    "full_name": "Muhammad Ali",
                    "phone": "03001234567",
                    "gender": "Male",
                    "date_of_birth": datetime.date(2010, 5, 15),
                    "status": "Active",
                    "portal_user": users["Student"]
                }
            )
            
            # 3. Guardian Profile
            guardian, _ = Guardian.objects.get_or_create(
                portal_user=users["Guardian"],
                defaults={
                    "student": student,
                    "full_name": "Ali Raza",
                    "phone": "03007654321",
                    "relationship": "Father",
                    "is_primary": True
                }
            )
            
            # 4. Enrollment
            enrollment, _ = Enrollment.objects.get_or_create(
                student=student,
                session=session,
                defaults={
                    "status": "Active",
                    "fee": Decimal("1500.00"),
                    "registration_fee": Decimal("250.00"),
                    "registration_date": datetime.date(2026, 1, 1),
                    "enrolled_by": users["Registrar"]
                }
            )
            
            # 5. Payment
            Payment.objects.get_or_create(
                enrollment=enrollment,
                amount=Decimal("1750.00"), # Tuition + Registration fee
                defaults={
                    "payment_status": "confirmed",
                    "payment_date": datetime.date(2026, 1, 5),
                    "payment_method": "Cash",
                    "recorded_by": users["Accountant"]
                }
            )

        self.stdout.write(self.style.SUCCESS("Demo database setup complete! Ready for external testing."))
