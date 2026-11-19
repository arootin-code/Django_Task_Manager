from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from jobs.models import Task


class TaskCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )
        self.other_user = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_task_success(self):
        url = "/api/tasks/"
        data = {"title": "Buy milk", "description": "From the store"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Buy milk")
        self.assertEqual(response.data["status"], Task.STATUS_PENDING)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.first().user, self.user)

    def test_create_task_empty_title(self):
        url = "/api/tasks/"
        response = self.client.post(url, {"title": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.count(), 0)

    def test_user_cannot_see_other_tasks(self):
        Task.objects.create(user=self.other_user, title="Bob's secret task")
        url = "/api/tasks/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class JWTAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )

    def test_login_success(self):
        url = "/api/auth/login/"
        data = {"username": "alice", "password": "pass12345"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password(self):
        url = "/api/auth/login/"
        data = {"username": "alice", "password": "wrongpass"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_access_without_token_returns_401(self):
        url = "/api/tasks/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class CeleryEmailTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)

    @patch("jobs.views.send_success_email.delay")
    def test_complete_sends_success_email(self, mock_delay):
        task = Task.objects.create(user=self.user, title="Finish report")
        url = f"/api/tasks/{task.id}/complete/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Task.STATUS_SUCCESS)
        self.assertIsNotNone(response.data["finished_at"])
        mock_delay.assert_called_once_with(
            "alice@example.com", "alice", "Finish report"
        )

    @patch("jobs.views.send_failure_email.delay")
    def test_fail_sends_failure_email(self, mock_delay):
        task = Task.objects.create(user=self.user, title="Doomed task")
        url = f"/api/tasks/{task.id}/fail/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Task.STATUS_FAILED)
        mock_delay.assert_called_once_with(
            "alice@example.com", "alice", "Doomed task"
        )

    def test_complete_nonexistent_task_returns_404(self):
        url = "/api/tasks/99999/complete/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

from datetime import timedelta

from django.utils import timezone

from jobs.tasks import send_reminder_for_stale_tasks


class ReminderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )

    @patch("jobs.tasks.send_mail")
    def test_old_pending_task_gets_reminder(self, mock_send_mail):
        task = Task.objects.create(user=self.user, title="Forgotten task")
        Task.objects.filter(pk=task.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )

        result = send_reminder_for_stale_tasks()

        mock_send_mail.assert_called_once()
        task.refresh_from_db()
        self.assertTrue(task.reminder_sent)
        self.assertIn("sent 1", result)

    @patch("jobs.tasks.send_mail")
    def test_new_pending_task_no_reminder(self, mock_send_mail):
        Task.objects.create(user=self.user, title="Fresh task")

        result = send_reminder_for_stale_tasks()

        mock_send_mail.assert_not_called()
        self.assertIn("sent 0", result)

    @patch("jobs.tasks.send_mail")
    def test_reminder_not_sent_twice(self, mock_send_mail):
        task = Task.objects.create(
            user=self.user, title="Already reminded", reminder_sent=True
        )
        Task.objects.filter(pk=task.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )

        result = send_reminder_for_stale_tasks()

        mock_send_mail.assert_not_called()
        self.assertIn("sent 0", result)