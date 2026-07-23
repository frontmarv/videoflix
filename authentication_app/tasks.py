"""
Background tasks for the authentication app.

These functions are designed to be executed by django-rq workers.
"""

import logging
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
from .email_templates import get_activation_email_template, get_password_reset_email_template

logger = logging.getLogger(__name__)

User = get_user_model()


def _attach_inline_logo(email: EmailMultiAlternatives, user_pk) -> None:
    """Attach logo image as CID for HTML email rendering."""
    logo_candidates = [
        Path(settings.BASE_DIR) / 'media' / 'logo' / 'Videoflix_logo.png',
        Path(settings.MEDIA_ROOT) / 'logo' / 'Videoflix_logo.png',
    ]

    for logo_path in logo_candidates:
        if logo_path.exists():
            with open(logo_path, 'rb') as img_file:
                img_data = img_file.read()

            logo = MIMEImage(img_data, _subtype='png')
            logo.add_header('Content-ID', '<logo_image>')
            logo.add_header('Content-Disposition', 'inline',
                            filename='Videoflix_logo.png')
            email.attach(logo)
            return

    logger.warning(
        f"Could not attach logo image for user {user_pk}: no logo found in expected paths"
    )


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

        plain_message, html_message = get_activation_email_template(
            activation_link)

        email = EmailMultiAlternatives(
            subject='Activate your Videoflix account',
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")

        _attach_inline_logo(email, user_pk)

        email.send(fail_silently=False)

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

        plain_message, html_message = get_password_reset_email_template(
            reset_link)

        # Create email with HTML alternative
        email = EmailMultiAlternatives(
            subject='Reset your Videoflix password',
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")

        _attach_inline_logo(email, user_pk)

        email.send(fail_silently=False)

        logger.info(
            f"Password reset email sent to user {user_pk} ({user.email})")

    except User.DoesNotExist:
        logger.error(
            f"Tried to send password reset email to non-existent user {user_pk}")
        raise
    except Exception as e:
        logger.error(
            f"Failed to send password reset email to user {user_pk}: {str(e)}", exc_info=True)
        raise
