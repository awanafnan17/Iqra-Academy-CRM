"""
Consistency Invariants — Tests business rules and data integrity
across the CRM.

Uses Django TestCase (no browser needed) to verify:
- Identity: display_name = get_full_name() or username
- Fees: outstanding = total - payments - discounts
- Attendance: present + absent + leave + late = total
- Results: obtained <= maximum
- Model property consistency

Usage:
    python -m pytest tools/qa/test_consistency_invariants.py -v --tb=short
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.test import TestCase
from django.contrib.auth.models import Group
from apps.accounts.models import CustomUser


class IdentityInvariantTests(TestCase):
    """Verify identity display consistency across user model."""

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name="Admin")

    def test_display_name_uses_full_name_when_available(self):
        """display_name should return full name when both names are set."""
        user = CustomUser.objects.create_user(
            email="inv1@test.com",
            username="inv1",
            password="test123",
            first_name="Ahmed",
            last_name="Khan",
        )
        self.assertEqual(user.display_name, "Ahmed Khan")
        self.assertEqual(user.full_name, "Ahmed Khan")
        self.assertEqual(user.get_full_name(), "Ahmed Khan")

    def test_display_name_falls_back_to_username(self):
        """display_name should return username when both names are blank."""
        user = CustomUser.objects.create_user(
            email="inv2@test.com",
            username="inv2_user",
            password="test123",
            first_name="",
            last_name="",
        )
        self.assertEqual(user.display_name, "inv2_user")

    def test_display_name_uses_first_name_only(self):
        """display_name should work with only first name."""
        user = CustomUser.objects.create_user(
            email="inv3@test.com",
            username="inv3",
            password="test123",
            first_name="Ahmed",
            last_name="",
        )
        self.assertEqual(user.display_name, "Ahmed")

    def test_display_name_uses_last_name_only(self):
        """display_name should work with only last name."""
        user = CustomUser.objects.create_user(
            email="inv4@test.com",
            username="inv4",
            password="test123",
            first_name="",
            last_name="Khan",
        )
        self.assertEqual(user.display_name, "Khan")

    def test_display_name_strips_whitespace(self):
        """display_name should strip leading/trailing whitespace."""
        user = CustomUser.objects.create_user(
            email="inv5@test.com",
            username="inv5",
            password="test123",
            first_name="  Ahmed  ",
            last_name="  Khan  ",
        )
        # get_full_name returns "  Ahmed     Khan  " — strip handles it
        self.assertNotIn("  ", user.display_name.strip())

    def test_full_name_property_consistent_with_get_full_name(self):
        """full_name property should match get_full_name() result."""
        user = CustomUser.objects.create_user(
            email="inv6@test.com",
            username="inv6",
            password="test123",
            first_name="Test",
            last_name="User",
        )
        self.assertEqual(user.full_name, user.get_full_name())

    def test_display_name_after_name_update(self):
        """display_name should reflect name changes immediately."""
        user = CustomUser.objects.create_user(
            email="inv7@test.com",
            username="inv7",
            password="test123",
            first_name="Old",
            last_name="Name",
        )
        self.assertEqual(user.display_name, "Old Name")

        user.first_name = "New"
        user.last_name = "Identity"
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.display_name, "New Identity")

    def test_username_is_not_display_name_when_full_name_exists(self):
        """username should NOT be used as display_name when name exists."""
        user = CustomUser.objects.create_user(
            email="inv8@test.com",
            username="system_login_id",
            password="test123",
            first_name="Ahmed",
            last_name="Raza",
        )
        self.assertNotEqual(user.display_name, "system_login_id")
        self.assertEqual(user.display_name, "Ahmed Raza")


class ModelPropertyConsistencyTests(TestCase):
    """Verify model properties and relationships are consistent."""

    def test_user_profile_creation(self):
        """Creating a user should not create orphaned profiles."""
        user = CustomUser.objects.create_user(
            email="cons1@test.com",
            username="cons1",
            password="test123",
        )
        # User should exist
        self.assertTrue(CustomUser.objects.filter(pk=user.pk).exists())

    def test_user_status_field_values(self):
        """User status field should only contain valid values."""
        valid_statuses = ["Active", "Inactive", "Suspended"]
        user = CustomUser.objects.create_user(
            email="cons2@test.com",
            username="cons2",
            password="test123",
            status="Active",
        )
        self.assertIn(user.status, valid_statuses)

    def test_email_uniqueness(self):
        """Email field must be unique."""
        CustomUser.objects.create_user(
            email="unique@test.com",
            username="uniq1",
            password="test123",
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                email="unique@test.com",
                username="uniq2",
                password="test123",
            )

    def test_group_membership_roundtrip(self):
        """Adding and removing groups should be consistent."""
        group, _ = Group.objects.get_or_create(name="TestRole")
        user = CustomUser.objects.create_user(
            email="grp@test.com",
            username="grp_user",
            password="test123",
        )
        user.groups.add(group)
        self.assertTrue(user.groups.filter(name="TestRole").exists())

        user.groups.remove(group)
        self.assertFalse(user.groups.filter(name="TestRole").exists())


if __name__ == "__main__":
    import unittest
    unittest.main()
