import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def send_success_email(self, user_email: str, username: str, task_title: str) -> str:
    logger.info("Sending success email to %s for task '%s'", user_email, task_title)

    send_mail(
        subject=f"🎉 Task completed: {task_title}",
        message=(
            f"Hi {username},\n\n"
            f"Great job! Your task \"{task_title}\" was marked as completed successfully.\n\n"
            "Do you have another task waiting for you?\n\n"
            "— Task Manager Team"
        ),
        from_email=None,
        recipient_list=[user_email],
        fail_silently=False,
    )

    logger.info("Success email sent to %s", user_email)
    return f"success email sent to {user_email}"


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def send_failure_email(self, user_email: str, username: str, task_title: str) -> str:
    logger.info("Sending failure email to %s for task '%s'", user_email, task_title)

    send_mail(
        subject=f"Task not completed: {task_title}",
        message=(
            f"Hi {username},\n\n"
            f"We're sorry that your task \"{task_title}\" could not be completed.\n\n"
            "Maybe next time. Don't give up!\n\n"
            "— Task Manager Team"
        ),
        from_email=None,
        recipient_list=[user_email],
        fail_silently=False,
    )

    logger.info("Failure email sent to %s", user_email)
    return f"failure email sent to {user_email}"


@shared_task
def send_reminder_for_stale_tasks(max_age_hours: int = 24) -> str:
    from datetime import timedelta

    from jobs.models import Task

    cutoff = timezone.now() - timedelta(hours=max_age_hours)

    stale_tasks = Task.objects.filter(
        status=Task.STATUS_PENDING,
        reminder_sent=False,
        created_at__lt=cutoff,
    ).select_related("user")

    count = 0
    for task in stale_tasks:
        send_mail(
            subject=f"⏰ Reminder: '{task.title}' is still pending",
            message=(
                f"Hi {task.user.username},\n\n"
                f"This is a gentle reminder that your task \"{task.title}\" "
                f"has been pending for more than {max_age_hours} hours.\n\n"
                "Take a moment to mark it as completed or failed.\n\n"
                "— Task Manager Team"
            ),
            from_email=None,
            recipient_list=[task.user.email],
            fail_silently=False,
        )
        task.reminder_sent = True
        task.save(update_fields=["reminder_sent"])
        count += 1

    logger.info("Sent reminder emails for %s stale tasks", count)
    return f"sent {count} reminder emails"