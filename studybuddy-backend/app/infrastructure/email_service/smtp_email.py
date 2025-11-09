"""SMTP email backend implementation.

This module provides an SMTP-based implementation of the EmailBackend interface.
It uses aiosmtplib for async SMTP operations and supports both plain text
and HTML emails with template rendering.
"""

import logging
from datetime import datetime
from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.infrastructure.email_service.base import EmailBackend

logger = logging.getLogger(__name__)


class SMTPEmail(EmailBackend):
    """SMTP email backend implementation.

    This class implements the EmailBackend interface using SMTP protocol.
    It supports TLS encryption, authentication, and HTML email templates.

    Attributes:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_username: SMTP authentication username.
        smtp_password: SMTP authentication password.
        from_email: Sender email address.
        from_name: Sender display name.
        use_tls: Whether to use TLS encryption.

    Examples:
        email_backend = SMTPEmail()
        await email_backend.send_verification_email(
            to="student@university.edu",
            token="abc123",
            university_name="Stanford University"
        )
    """

    def __init__(self) -> None:
        """Initialize SMTP email backend with settings."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> None:
        """Send an email via SMTP.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain text email body.
            html: Optional HTML email body.

        Raises:
            Exception: If SMTP connection or email sending fails.
        """
        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to
        message["Subject"] = subject

        # Set plain text content
        message.set_content(body)

        # Add HTML alternative if provided
        if html:
            message.add_alternative(html, subtype="html")

        # Send email via SMTP
        smtp_client = aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=self.use_tls,
        )

        try:
            await smtp_client.connect()
            await smtp_client.login(self.smtp_username, self.smtp_password)
            await smtp_client.send_message(message)
            logger.info(f"Email sent successfully to {to}")
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            raise
        finally:
            await smtp_client.quit()

    async def send_verification_email(
        self,
        to: str,
        token: str,
        university_name: str,
    ) -> None:
        """Send student verification email.

        Args:
            to: Recipient email address (university email).
            token: Verification token for the confirmation link.
            university_name: Name of the university for display.

        Raises:
            Exception: If email sending fails.
        """
        verification_url = f"{settings.FRONTEND_URL}/verify/{token}"

        subject = f"Verify your {university_name} student status"

        # Plain text version
        body = f"""
Hello,

Thank you for registering with StudyBuddy!

To verify your student status at {university_name}, please click the link below:

{verification_url}

This link will expire in 24 hours.

If you did not request this verification, please ignore this email.

Best regards,
The StudyBuddy Team
"""

        # HTML version with template
        html = self._render_verification_template(
            verification_url=verification_url,
            university_name=university_name,
        )

        await self.send_email(
            to=to,
            subject=subject,
            body=body.strip(),
            html=html,
        )

        logger.info(f"Verification email sent to {to} for {university_name}")

    async def send_event_reminder(
        self,
        to: str,
        event_title: str,
        event_time: datetime,
        event_location: str,
    ) -> None:
        """Send event reminder email.

        Args:
            to: Recipient email address.
            event_title: Title of the event.
            event_time: Event start time.
            event_location: Event location (physical or virtual).

        Raises:
            Exception: If email sending fails.
        """
        # Format event time
        formatted_time = event_time.strftime("%A, %B %d, %Y at %I:%M %p")

        subject = f"Reminder: {event_title}"

        # Plain text version
        body = f"""
Hello,

This is a reminder about your upcoming event:

Event: {event_title}
When: {formatted_time}
Where: {event_location}

Don't forget to attend!

Best regards,
The StudyBuddy Team
"""

        # HTML version with template
        event_url = f"{settings.FRONTEND_URL}/events"
        html = self._render_event_reminder_template(
            event_title=event_title,
            event_time=event_time,
            event_location=event_location,
            event_url=event_url,
        )

        await self.send_email(
            to=to,
            subject=subject,
            body=body.strip(),
            html=html,
        )

        logger.info(f"Event reminder sent to {to} for '{event_title}'")

    def _render_verification_template(
        self,
        verification_url: str,
        university_name: str,
    ) -> str:
        """Render verification email HTML template.

        Args:
            verification_url: Full verification URL with token.
            university_name: Name of the university.

        Returns:
            Rendered HTML email template.
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Student Status</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #4F46E5;
        }}
        h1 {{
            color: #1F2937;
            font-size: 24px;
            margin-bottom: 20px;
        }}
        .button {{
            display: inline-block;
            background-color: #4F46E5;
            color: #ffffff;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 6px;
            font-weight: 500;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            font-size: 14px;
            color: #6B7280;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">StudyBuddy</div>
        </div>

        <h1>Verify Your Student Status</h1>

        <p>Hello,</p>

        <p>Thank you for registering with StudyBuddy! To verify your student status at <strong>{university_name}</strong>, please click the button below:</p>

        <div style="text-align: center;">
            <a href="{verification_url}" class="button">Verify My Account</a>
        </div>

        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>

        <p><strong>Note:</strong> This verification link will expire in 24 hours.</p>

        <p>If you did not request this verification, please ignore this email.</p>

        <div class="footer">
            <p>Best regards,<br>The StudyBuddy Team</p>
        </div>
    </div>
</body>
</html>
"""

    def _render_event_reminder_template(
        self,
        event_title: str,
        event_time: datetime,
        event_location: str,
        event_url: str,
    ) -> str:
        """Render event reminder email HTML template.

        Args:
            event_title: Title of the event.
            event_time: Event start time.
            event_location: Event location.
            event_url: URL to view event details.

        Returns:
            Rendered HTML email template.
        """
        formatted_time = event_time.strftime("%A, %B %d, %Y at %I:%M %p")

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Reminder</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #4F46E5;
        }}
        h1 {{
            color: #1F2937;
            font-size: 24px;
            margin-bottom: 20px;
        }}
        .event-details {{
            background-color: #F3F4F6;
            border-left: 4px solid #4F46E5;
            padding: 20px;
            margin: 20px 0;
        }}
        .event-details p {{
            margin: 8px 0;
        }}
        .button {{
            display: inline-block;
            background-color: #4F46E5;
            color: #ffffff;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 6px;
            font-weight: 500;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            font-size: 14px;
            color: #6B7280;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">StudyBuddy</div>
        </div>

        <h1>🔔 Event Reminder</h1>

        <p>Hello,</p>

        <p>This is a friendly reminder about your upcoming event:</p>

        <div class="event-details">
            <p><strong>📅 Event:</strong> {event_title}</p>
            <p><strong>🕐 When:</strong> {formatted_time}</p>
            <p><strong>📍 Where:</strong> {event_location}</p>
        </div>

        <p>Don't forget to attend! We're looking forward to seeing you there.</p>

        <div style="text-align: center;">
            <a href="{event_url}" class="button">View Event Details</a>
        </div>

        <div class="footer">
            <p>Best regards,<br>The StudyBuddy Team</p>
        </div>
    </div>
</body>
</html>
"""
