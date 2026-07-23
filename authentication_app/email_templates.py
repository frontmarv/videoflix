"""
Email templates for the authentication app.

This module contains HTML and plain text email templates.
"""


def _build_html_email_template(title: str, intro_text: str, cta_label: str, cta_link: str, warning_text: str, outro_text: str) -> str:
    """Build a consistent HTML email layout for auth emails."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
            <div style="text-align: center; margin-bottom: 40px;">
                <img src="cid:logo_image" alt="Videoflix Logo" width="251" height="40" style="display: block; margin: 0 auto; border: 0; max-width: 100%; height: auto;">
            </div>

            <div style="color: #333; line-height: 1.6;">
                <h1 style="font-size: 24px; margin: 0 0 20px; color: #333;">{title}</h1>
                <p style="font-size: 16px; margin: 0 0 20px;">Dear User,</p>
                <p style="font-size: 16px; margin: 0 0 20px;">{intro_text}</p>

                <div style="text-align: center;">
                    <a href="{cta_link}" style="display: inline-block; background-color: #1222d9; color: #ffffff; padding: 14px 40px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; margin: 30px 0; text-align: center;">{cta_label}</a>
                </div>

                <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px; margin: 20px 0; font-size: 14px; color: #856404;">
                    <strong>Link Expiration:</strong> {warning_text}
                </div>

                <p style="font-size: 16px; margin: 0 0 20px;">{outro_text}</p>
            </div>

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; text-align: center;">
                <p style="margin: 0;">Best regards,<br><strong>Your Videoflix Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """


def get_activation_email_template(activation_link: str) -> tuple[str, str]:
    """
    Get activation email templates (plain text and HTML).

    Args:
        activation_link: The activation link to include in the email

    Returns:
        A tuple of (plain_text_message, html_message)
    """
    plain_message = (
        f'Hi there,\n\n'
        f'Please activate your account by clicking the link below:\n\n'
        f'{activation_link}\n\n'
        f'This link expires in 24 hours.\n'
    )

    html_message = _build_html_email_template(
        title='Welcome to Videoflix',
        intro_text='Thank you for registering with <strong>Videoflix</strong>. To complete your registration and verify your email address, please click the button below:',
        cta_label='Activate Account',
        cta_link=activation_link,
        warning_text='This activation link expires in 24 hours. If you did not create an account with us, please disregard this email.',
        outro_text='If you did not create an account with us, please disregard this email.',
    )

    return plain_message, html_message


def get_password_reset_email_template(reset_link: str) -> tuple[str, str]:
    """
    Get password reset email templates (plain text and HTML).

    Args:
        reset_link: The password reset link to include in the email

    Returns:
        A tuple of (plain_text_message, html_message)
    """
    plain_message = (
        f'Hi there,\n\n'
        f'Please reset your password by clicking the link below:\n\n'
        f'{reset_link}\n\n'
        f'This link expires in 24 hours.\n'
    )

    html_message = _build_html_email_template(
        title='Reset Your Password',
        intro_text='We received a request to reset your password. To complete the password reset, please click the button below:',
        cta_label='Reset Password',
        cta_link=reset_link,
        warning_text='This password reset link expires in 24 hours. If you did not request a password reset, please ignore this email.',
        outro_text='If you did not request a password reset, please ignore this email. Your account is secure.',
    )

    return plain_message, html_message
