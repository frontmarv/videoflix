"""
Centralized task queuing service for django-rq.

Provides a unified interface for enqueueing background tasks across the application.
"""

import logging
import django_rq
from django.conf import settings

logger = logging.getLogger(__name__)


class TaskService:
    """Centralized service for enqueueing background tasks to RQ queues."""

    @staticmethod
    def _enqueue_task(task_function, *args, queue_name='default', job_timeout=None, **kwargs):
        """
        Enqueue a task to the specified RQ queue.

        Args:
            task_function: The function to enqueue (imported from app tasks module)
            *args: Positional arguments for the task function
            queue_name: Name of the RQ queue (default: 'default')
            job_timeout: Job timeout in seconds (default: None, uses queue default)
            **kwargs: Keyword arguments for the task function

        Returns:
            Job object from RQ, or None if enqueueing failed

        Raises:
            Exception: If RQ is not properly configured or Redis is unavailable
        """
        try:
            queue = django_rq.get_queue(queue_name)
            job = queue.enqueue(task_function, *args,
                                job_timeout=job_timeout, **kwargs)
            logger.info(
                f"Task enqueued: {task_function.__name__} (Job ID: {job.id}, Queue: {queue_name})"
            )
            return job
        except Exception as e:
            logger.error(
                f"Failed to enqueue task {task_function.__name__}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def send_activation_email(user_pk, activation_link):
        """
        Enqueue an activation email task.

        Args:
            user_pk: Primary key of the user to send activation email to
            activation_link: The activation link to include in the email

        Returns:
            Job object from RQ
        """
        from authentication_app.tasks import send_activation_email_task

        job_timeout = getattr(settings, 'TASK_TIMEOUT_EMAIL', 300)
        return TaskService._enqueue_task(
            send_activation_email_task,
            user_pk,
            activation_link,
            job_timeout=job_timeout,
        )

    @staticmethod
    def send_password_reset_email(user_pk, reset_link):
        """
        Enqueue a password reset email task.

        Args:
            user_pk: Primary key of the user to send password reset email to
            reset_link: The password reset link to include in the email

        Returns:
            Job object from RQ
        """
        from authentication_app.tasks import send_password_reset_email_task

        job_timeout = getattr(settings, 'TASK_TIMEOUT_EMAIL', 300)
        return TaskService._enqueue_task(
            send_password_reset_email_task,
            user_pk,
            reset_link,
            job_timeout=job_timeout,
        )
