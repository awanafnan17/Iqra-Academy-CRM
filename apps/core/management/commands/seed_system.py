"""
Django management command to initialize the Academy CRM with default configurations.

Seeds:
- 7 Django Groups: Admin, Principal, Teacher, Accountant, Registrar, Student, Guardian.
- Default Permissions assigned to each Group.
- Global GradeConfig boundary configurations.
- Default ExpenseCategory configurations.

Safe, idempotent, and duplicate-safe execution.
All operations run inside a single transaction.atomic() block.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from apps.exams.models import GradeConfig
from apps.finance.models import ExpenseCategory


class Command(BaseCommand):
    """Management command to seed the system with default groups, permissions, grades, and expense categories."""

    help = "Seeds default Django groups, permissions, grade configurations, and expense categories."

    def handle(self, *args, **options):
        self.stdout.write("Initializing system configuration seed...")

        with transaction.atomic():
            self._seed_expense_categories()
            self._seed_grade_configs()
            self._seed_groups_and_permissions()

        self.stdout.write(self.style.SUCCESS("System seeding completed successfully!"))

    def _seed_expense_categories(self):
        """Seed default expense categories."""
        self.stdout.write("Seeding default expense categories...")
        expense_categories = [
            ("Rent", "Rent or lease payments for academy premises."),
            ("Utilities", "Electricity, gas, water, internet, and phone bills."),
            ("Salaries", "Monthly salaries and bonuses for teachers and staff."),
            ("Supplies", "Stationery, markers, printing paper, classroom materials."),
            ("Marketing", "Social media ads, flyers, banners, and advertising campaigns."),
            ("Repairs and Maintenance", "Renovations, hardware repairs, plumbing, electrical maintenance."),
            ("Miscellaneous", "Any minor or unclassified business expenses."),
        ]

        for name, description in expense_categories:
            category, created = ExpenseCategory.objects.get_or_create(
                name=name,
                defaults={"description": description, "is_active": True},
            )
            if created:
                self.stdout.write(f"  Created Expense Category: {name}")
            else:
                category.description = description
                category.is_active = True
                category.save(update_fields=["description", "is_active"])

    def _seed_grade_configs(self):
        """Seed global grade boundary configurations."""
        self.stdout.write("Seeding global grade configurations...")
        grades = [
            ("A+", Decimal("90.00"), Decimal("100.00"), Decimal("4.00"), 1),
            ("A", Decimal("80.00"), Decimal("89.99"), Decimal("4.00"), 2),
            ("B+", Decimal("75.00"), Decimal("79.99"), Decimal("3.50"), 3),
            ("B", Decimal("70.00"), Decimal("74.99"), Decimal("3.00"), 4),
            ("C+", Decimal("65.00"), Decimal("69.99"), Decimal("2.50"), 5),
            ("C", Decimal("60.00"), Decimal("64.99"), Decimal("2.00"), 6),
            ("D", Decimal("50.00"), Decimal("59.99"), Decimal("1.00"), 7),
            ("F", Decimal("0.00"), Decimal("49.99"), Decimal("0.00"), 8),
        ]

        for name, min_pct, max_pct, gp, order in grades:
            config, created = GradeConfig.objects.get_or_create(
                session=None,
                grade_name=name,
                defaults={
                    "min_percentage": min_pct,
                    "max_percentage": max_pct,
                    "grade_point": gp,
                    "sort_order": order,
                },
            )
            if created:
                self.stdout.write(f"  Created Grade boundary: {name}")
            else:
                config.min_percentage = min_pct
                config.max_percentage = max_pct
                config.grade_point = gp
                config.sort_order = order
                config.save(update_fields=[
                    "min_percentage", "max_percentage", "grade_point", "sort_order",
                ])

    def _seed_groups_and_permissions(self):
        """Seed Django groups and assign default permissions."""
        self.stdout.write("Seeding Django groups and permissions...")
        group_permissions = {
            "Admin": ["all"],
            "Principal": [
                "view_session", "add_session", "change_session",
                "view_subject", "add_subject", "change_subject",
                "view_teacherassignment", "add_teacherassignment", "change_teacherassignment",
                "view_student", "add_student", "change_student",
                "view_enrollment", "add_enrollment", "change_enrollment",
                "view_attendancerecord", "add_attendancerecord", "change_attendancerecord",
                "view_attendancelock", "add_attendancelock", "change_attendancelock",
                "view_exam", "add_exam", "change_exam",
                "view_examresult", "add_examresult", "change_examresult",
                "view_gradeconfig", "add_gradeconfig", "change_gradeconfig",
                "view_payment", "view_expense", "view_refund",
            ],
            "Teacher": [
                "view_session", "view_subject",
                "view_student", "view_enrollment",
                "view_attendancerecord", "add_attendancerecord", "change_attendancerecord",
                "view_exam", "add_exam", "change_exam",
                "view_examresult", "add_examresult", "change_examresult",
            ],
            "Accountant": [
                "view_session", "view_student", "view_enrollment",
                "view_payment", "add_payment", "change_payment",
                "view_expense", "add_expense", "change_expense",
                "view_refund", "add_refund", "change_refund",
                "view_expensecategory", "add_expensecategory", "change_expensecategory",
            ],
            "Registrar": [
                "view_session", "add_session", "change_session",
                "view_subject", "add_subject", "change_subject",
                "view_teacherassignment", "add_teacherassignment", "change_teacherassignment",
                "view_student", "add_student", "change_student",
                "view_enrollment", "add_enrollment", "change_enrollment",
                "view_attendancerecord", "view_attendancelock",
            ],
            "Student": [
                "view_session", "view_subject",
            ],
            "Guardian": [
                "view_session", "view_subject",
            ],
        }

        for group_name, codenames in group_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f"  Created Group: {group_name}")

            if "all" in codenames:
                all_perms = Permission.objects.all()
                group.permissions.set(all_perms)
            else:
                perms_list = []
                for codename in codenames:
                    perm = Permission.objects.filter(codename=codename).first()
                    if perm:
                        perms_list.append(perm)
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"    Warning: Permission '{codename}' not found in database.")
                        )
                group.permissions.set(perms_list)
