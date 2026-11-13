from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from jobs.models import Task
from jobs.serializers import TaskSerializer
from jobs.tasks import send_failure_email, send_success_email


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()

        if task.status != Task.STATUS_PENDING:
            return Response(
                {"detail": "Only pending tasks can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = Task.STATUS_SUCCESS
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "finished_at"])

        send_success_email.delay(
            task.user.email, task.user.username, task.title
        )

        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        task = self.get_object()

        if task.status != Task.STATUS_PENDING:
            return Response(
                {"detail": "Only pending tasks can be marked as failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.status = Task.STATUS_FAILED
        task.finished_at = timezone.now()
        task.save(update_fields=["status", "finished_at"])

        send_failure_email.delay(
            task.user.email, task.user.username, task.title
        )

        return Response(TaskSerializer(task).data)