"""
Background tasks for the authentication app.

These functions are designed to be executed by django-rq workers.
"""

import logging
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()


def send_activation_email_task(user_pk, activation_link):
    """
    Send an account activation email to the user.

    This task is designed to run asynchronously via RQ.

    Args:
        user_pk: Primary key of the user to send the email to
        activation_link: The activation link to include in the email

    Raises:
        User.DoesNotExist: If the user does not exist
        Exception: If the email fails to send
    """
    try:
        user = User.objects.get(pk=user_pk)

        message = (
            f'Hi {user.email},\n\n'
            f'Please activate your account by clicking the link below:\n\n'
            f'{activation_link}\n\n'
            f'This link expires in 24 hours.\n'
        )

        send_mail(
            subject='Activate your Videoflix account',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Activation email sent to user {user_pk} ({user.email})")
    except User.DoesNotExist:
        logger.error(f"User with pk {user_pk} does not exist")
        raise
    except Exception as e:
        logger.error(
            f"Failed to send activation email to user {user_pk}: {str(e)}", exc_info=True)
        raise


def send_password_reset_email_task(user_pk, reset_link):
    """
    Send a password reset email to the user.

    This task is designed to run asynchronously via RQ.

    Args:
        user_pk: Primary key of the user to send the email to
        reset_link: The password reset link to include in the email

    Raises:
        User.DoesNotExist: If the user does not exist
        Exception: If the email fails to send
    """
    try:
        user = User.objects.get(pk=user_pk)

        message = (
            f'Hi {user.email},\n\n'
            f'Please reset your password by clicking the link below:\n\n'
            f'{reset_link}\n\n'
            f'This link expires in 24 hours.\n'
        )

        send_mail(
            subject='Reset your Videoflix password',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(
            f"Password reset email sent to user {user_pk} ({user.email})")

    except User.DoesNotExist:
        logger.error(
            f"Tried to send activation email to non-existent user {user_pk}")
        raise
    except Exception as e:
        logger.error(
            f"Failed to send activation email to user {user_pk}: {str(e)}", exc_info=True)
        raise
