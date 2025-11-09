"""Abstract email backend interface.

This module provides the abstract base class for all email backends.
Following the Strategy pattern, it allows different email implementations
(SMTP, SendGrid, AWS SES, etc.) to be swapped without changing business logic.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class EmailBackend(ABC):
    """Abstract base class for email backends.

    All email implementations must inherit from this class and implement
    all abstract methods. This ensures a consistent interface across
    different email providers.

    Examples:
        class MySMTPEmail(EmailBackend):
            async def send_email(self, to, subject, body, html=None):
                # SMTP implementation
                pass

            async def send_verification_email(self, to, token, university_name):
                # Verification email implementation
                pass

            async def send_event_reminder(self, to, event_title, event_time, event_location):
                # Event reminder implementation
                pass
    """

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> None:
        """Send a generic email.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain text email body.
            html: Optional HTML email body.

        Raises:
            Exception: If email sending fails.
        """
        pass

    @abstractmethod
    async def send_verification_email(
        self,
        to: str,
        token: str,
        university_name: str,
    ) -> None:
        """Send student verification email with confirmation link.

        Args:
            to: Recipient email address (university email).
            token: Verification token for the confirmation link.
            university_name: Name of the university for display.

        Raises:
            Exception: If email sending fails.
        """
        pass

    @abstractmethod
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
        pass
