import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.ai_engine.models import PredictionLog, ModelVersion
from apps.students.models import Student

User = get_user_model()


class AIEngineTests(TestCase):
    def setUp(self):
        super().setUp()

        # Create groups
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.principal_group, _ = Group.objects.get_or_create(name="Principal")
        self.registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")
        self.accountant_group, _ = Group.objects.get_or_create(name="Accountant")
        self.student_group, _ = Group.objects.get_or_create(name="Student")
        self.guardian_group, _ = Group.objects.get_or_create(name="Guardian")

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.admin_group)

        self.principal_user = User.objects.create_user(
            username="principal@test.com", email="principal@test.com", password="password"
        )
        self.principal_user.groups.add(self.principal_group)

        self.registrar_user = User.objects.create_user(
            username="registrar@test.com", email="registrar@test.com", password="password"
        )
        self.registrar_user.groups.add(self.registrar_group)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.teacher_group)

        self.accountant_user = User.objects.create_user(
            username="accountant@test.com", email="accountant@test.com", password="password"
        )
        self.accountant_user.groups.add(self.accountant_group)

        self.student_user = User.objects.create_user(
            username="student@test.com", email="student@test.com", password="password"
        )
        self.student_user.groups.add(self.student_group)

        self.guardian_user = User.objects.create_user(
            username="guardian@test.com", email="guardian@test.com", password="password"
        )
        self.guardian_user.groups.add(self.guardian_group)

        # Create student profile
        self.student = Student.objects.create(
            full_name="Fatima Khan",
            roll_number="CSS-01",
            gender="Female"
        )

        # Create Model Version
        self.model_version = ModelVersion.objects.create(
            model_type="dropout",
            version="1.0.0",
            file_path="models/dropout_v1.joblib",
            accuracy_score=0.9234,
            is_active=True,
            notes="First production-ready version"
        )

        # Create Prediction Log
        self.prediction_log = PredictionLog.objects.create(
            prediction_type="dropout",
            model_version=self.model_version,
            target_model="students.Student",
            target_object_id=self.student.pk,
            input_features='{"attendance_rate": 65.5, "gpa": 2.1}',
            prediction_value='{"dropout_probability": 0.82}',
            confidence_score=82.00,
            risk_level="high",
            is_acknowledged=False
        )

    def test_admin_can_open_prediction_list(self):
        """Admin can access prediction list view and see seeded record."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")
        self.assertContains(response, "Dropout Risk")

    def test_admin_can_open_prediction_detail(self):
        """Admin can access prediction detail view and see json properties."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_detail", kwargs={"pk": self.prediction_log.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")
        self.assertContains(response, "dropout_probability")

    def test_admin_can_open_model_version_list(self):
        """Admin can access model version list."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:model_version_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1.0.0")

    def test_admin_can_open_dropout_risk_dashboard(self):
        """Admin can access dropout risk dashboard and see real database metrics."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:dropout_risk_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

    def test_principal_can_open_dropout_risk_dashboard(self):
        """Principal can access dropout risk dashboard."""
        self.client.login(username="principal@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:dropout_risk_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_principal_cannot_open_prediction_views(self):
        """Principal is blocked from prediction list, detail and models list."""
        self.client.login(username="principal@test.com", password="password")
        
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_list"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("admin_panel:ai_engine:prediction_detail", kwargs={"pk": self.prediction_log.pk}))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("admin_panel:ai_engine:model_version_list"))
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_roles_are_blocked(self):
        """Registrar, Teacher, Accountant, Student, Guardian are blocked from all views."""
        blocked_users = [
            self.registrar_user,
            self.teacher_user,
            self.accountant_user,
            self.student_user,
            self.guardian_user
        ]
        endpoints = [
            reverse("admin_panel:ai_engine:prediction_list"),
            reverse("admin_panel:ai_engine:prediction_detail", kwargs={"pk": self.prediction_log.pk}),
            reverse("admin_panel:ai_engine:model_version_list"),
            reverse("admin_panel:ai_engine:dropout_risk_dashboard"),
        ]

        for user in blocked_users:
            self.client.login(username=user.username, password="password")
            for url in endpoints:
                response = self.client.get(url)
                # Should return 404 (middleware panel-level constraint or role check)
                self.assertEqual(response.status_code, 404, f"User {user.username} was not blocked from {url}")

    def test_anonymous_redirects_to_login(self):
        """Unauthenticated requests are redirected to login."""
        self.client.logout()
        endpoints = [
            reverse("admin_panel:ai_engine:prediction_list"),
            reverse("admin_panel:ai_engine:prediction_detail", kwargs={"pk": self.prediction_log.pk}),
            reverse("admin_panel:ai_engine:model_version_list"),
            reverse("admin_panel:ai_engine:dropout_risk_dashboard"),
        ]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_empty_prediction_list_renders_cleanly(self):
        """Prediction list renders cleanly with no predictions in DB."""
        PredictionLog.objects.all().delete()
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No AI predictions have been generated yet")

    def test_empty_model_version_list_renders_cleanly(self):
        """Model version list renders cleanly with no models in DB."""
        ModelVersion.objects.all().delete()
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:model_version_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No trained model versions are currently available")

    def test_empty_dropout_dashboard_renders_honestly(self):
        """Dropout dashboard displays clean empty state if no predictions exist in DB."""
        PredictionLog.objects.all().delete()
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:dropout_risk_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No AI predictions have been generated yet")

    def test_json_features_render_safely(self):
        """Malformed or string inputs are parsed safely by view logic."""
        malformed_pred = PredictionLog.objects.create(
            prediction_type="dropout",
            target_model="students.Student",
            target_object_id=self.student.pk,
            input_features='not-json',
            prediction_value='{"val": "good"}',
            risk_level="low"
        )
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_detail", kwargs={"pk": malformed_pred.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not-json")

    def test_post_acknowledge_updates_only_existing_acknowledgement_fields(self):
        """POST request to acknowledge updates only the is_acknowledged, acknowledged_by, and acknowledged_at fields."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.post(reverse("admin_panel:ai_engine:prediction_acknowledge", kwargs={"pk": self.prediction_log.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify db status
        self.prediction_log.refresh_from_db()
        self.assertTrue(self.prediction_log.is_acknowledged)
        self.assertEqual(self.prediction_log.acknowledged_by, self.admin_user)
        self.assertIsNotNone(self.prediction_log.acknowledged_at)

    def test_get_acknowledge_does_not_mutate(self):
        """GET request to acknowledge view is rejected with 404 and does not mutate db state."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:ai_engine:prediction_acknowledge", kwargs={"pk": self.prediction_log.pk}))
        self.assertEqual(response.status_code, 404)
        
        # Verify db status is unchanged
        self.prediction_log.refresh_from_db()
        self.assertFalse(self.prediction_log.is_acknowledged)

    def test_unauthorized_acknowledge_does_not_mutate(self):
        """Unauthorized user POST is blocked and does not mutate db state."""
        self.client.login(username="principal@test.com", password="password")
        response = self.client.post(reverse("admin_panel:ai_engine:prediction_acknowledge", kwargs={"pk": self.prediction_log.pk}))
        self.assertEqual(response.status_code, 404)

        # Verify db status is unchanged
        self.prediction_log.refresh_from_db()
        self.assertFalse(self.prediction_log.is_acknowledged)

    def test_no_fake_predictions_are_created(self):
        """Check that no views generate mock database entries of prediction logs."""
        initial_count = PredictionLog.objects.count()
        self.client.login(username="admin@test.com", password="password")
        self.client.get(reverse("admin_panel:ai_engine:prediction_list"))
        self.client.get(reverse("admin_panel:ai_engine:dropout_risk_dashboard"))
        
        self.assertEqual(PredictionLog.objects.count(), initial_count)
