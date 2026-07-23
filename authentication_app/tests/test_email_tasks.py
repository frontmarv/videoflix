from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase, TestCase, override_settings

from authentication_app.tasks import _attach_inline_logo, logger, send_activation_email_task


MINIMAL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0bIDATx\x9cc\xf8\x0f\x00\x01\x01\x01\x00\x18\xdd\x8d\xb1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class InlineLogoAttachmentTests(SimpleTestCase):
    def test_attach_inline_logo_adds_cid_and_inline_disposition(self):
        email = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            from_email="noreply@videoflix.com",
            to=["user@example.com"],
        )
        email.attach_alternative(
            '<html><body><img src="cid:logo_image" alt="Logo"></body></html>',
            "text/html",
        )

        with TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            logo_path = base_dir / "media" / "logo" / "Videoflix_logo.png"
            logo_path.parent.mkdir(parents=True, exist_ok=True)
            logo_path.write_bytes(MINIMAL_PNG_BYTES)

            with override_settings(BASE_DIR=base_dir, MEDIA_ROOT=base_dir / "media"):
                _attach_inline_logo(email, user_pk="test-user")

        message = email.message()
        image_parts = [part for part in message.walk(
        ) if part.get_content_type() == "image/png"]

        self.assertEqual(len(image_parts), 1)
        self.assertEqual(image_parts[0].get("Content-ID"), "<logo_image>")
        self.assertIn("inline", image_parts[0].get(
            "Content-Disposition", "").lower())

    def test_attach_inline_logo_logs_warning_when_logo_missing(self):
        email = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            from_email="noreply@videoflix.com",
            to=["user@example.com"],
        )
        email.attach_alternative(
            '<html><body><img src="cid:logo_image" alt="Logo"></body></html>',
            "text/html",
        )

        with TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            with override_settings(BASE_DIR=base_dir, MEDIA_ROOT=base_dir / "media"):
                with self.assertLogs(logger, level="WARNING") as captured:
                    _attach_inline_logo(email, user_pk="missing-logo-user")

        self.assertTrue(
            any("Could not attach logo image" in line for line in captured.output))

        message = email.message()
        image_parts = [part for part in message.walk(
        ) if part.get_content_type() == "image/png"]
        self.assertEqual(image_parts, [])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@videoflix.com",
)
class ActivationEmailTaskTests(TestCase):
    def test_send_activation_email_task_builds_html_and_inline_logo(self):
        user = get_user_model().objects.create_user(
            email="task-user@example.com",
            password="safe-pass-123",
        )
        activation_link = "http://localhost:4200/activate?token=abc"

        with TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            logo_path = base_dir / "media" / "logo" / "Videoflix_logo.png"
            logo_path.parent.mkdir(parents=True, exist_ok=True)
            logo_path.write_bytes(MINIMAL_PNG_BYTES)

            with override_settings(BASE_DIR=base_dir, MEDIA_ROOT=base_dir / "media"):
                send_activation_email_task(user.pk, activation_link)

        self.assertEqual(len(mail.outbox), 1)
        email_message = mail.outbox[0].message()

        html_parts = [part for part in email_message.walk(
        ) if part.get_content_type() == "text/html"]
        image_parts = [part for part in email_message.walk(
        ) if part.get_content_type() == "image/png"]

        self.assertEqual(len(html_parts), 1)
        self.assertIn("cid:logo_image", html_parts[0].get_payload(
            decode=True).decode("utf-8"))
        self.assertEqual(len(image_parts), 1)
        self.assertEqual(image_parts[0].get("Content-ID"), "<logo_image>")
