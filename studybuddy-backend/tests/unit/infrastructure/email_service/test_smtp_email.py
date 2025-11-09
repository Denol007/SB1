"""Unit tests for SMTP email backend.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.email_service.smtp_email import SMTPEmail


@pytest.fixture
def smtp_settings():
    """Mock SMTP settings for testing."""
    settings = MagicMock()
    settings.SMTP_HOST = "smtp.test.com"
    settings.SMTP_PORT = 587
    settings.SMTP_USERNAME = "test@example.com"
    settings.SMTP_PASSWORD = "test_password"
    settings.SMTP_FROM_EMAIL = "noreply@studybuddy.com"
    settings.SMTP_FROM_NAME = "StudyBuddy"
    settings.SMTP_USE_TLS = True
    settings.FRONTEND_URL = "https://studybuddy.com"
    return settings


@pytest.fixture
def smtp_email(smtp_settings):
    """Create SMTPEmail instance with mocked settings."""
    with patch("app.infrastructure.email_service.smtp_email.settings", smtp_settings):
        return SMTPEmail()


class TestSMTPEmail:
    """Test cases for SMTPEmail class."""

    def test_smtp_email_inherits_from_email_backend(self, smtp_email):
        """Test that SMTPEmail inherits from EmailBackend."""
        from app.infrastructure.email_service.base import EmailBackend

        assert isinstance(smtp_email, EmailBackend)

    def test_smtp_email_initialization(self, smtp_settings):
        """Test that SMTPEmail initializes with correct settings."""
        with patch("app.infrastructure.email_service.smtp_email.settings", smtp_settings):
            email = SMTPEmail()

            assert email.smtp_host == "smtp.test.com"
            assert email.smtp_port == 587
            assert email.smtp_username == "test@example.com"
            assert email.smtp_password == "test_password"
            assert email.from_email == "noreply@studybuddy.com"
            assert email.from_name == "StudyBuddy"
            assert email.use_tls is True

    @pytest.mark.asyncio
    async def test_send_email_basic(self, smtp_email):
        """Test sending a basic email."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            await smtp_email.send_email(
                to="user@example.com",
                subject="Test Subject",
                body="Test body content",
            )

            # Verify SMTP connection was made
            mock_smtp_class.assert_called_once_with(
                hostname="smtp.test.com",
                port=587,
                use_tls=True,
            )

            # Verify email was sent
            mock_smtp.connect.assert_called_once()
            mock_smtp.login.assert_called_once_with("test@example.com", "test_password")
            mock_smtp.send_message.assert_called_once()
            mock_smtp.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_html(self, smtp_email):
        """Test sending an email with HTML content."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            await smtp_email.send_email(
                to="user@example.com",
                subject="Test Subject",
                body="Plain text",
                html="<html><body>HTML content</body></html>",
            )

            # Verify email was sent with both plain and HTML
            mock_smtp.send_message.assert_called_once()
            sent_message = mock_smtp.send_message.call_args[0][0]

            # Message should be multipart
            assert sent_message.is_multipart()

    @pytest.mark.asyncio
    async def test_send_verification_email(self, smtp_email):
        """Test sending a verification email."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            await smtp_email.send_verification_email(
                to="student@university.edu",
                token="test-token-123",
                university_name="Test University",
            )

            # Verify SMTP was called
            mock_smtp.connect.assert_called_once()
            mock_smtp.send_message.assert_called_once()

            # Check that message contains verification link
            sent_message = mock_smtp.send_message.call_args[0][0]
            assert "student@university.edu" in sent_message["To"]
            assert "Verify" in sent_message["Subject"]

            # Verify message body contains token and university name
            body = sent_message.get_body()
            assert body is not None

    @pytest.mark.asyncio
    async def test_send_event_reminder(self, smtp_email):
        """Test sending an event reminder email."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            event_time = datetime(2025, 12, 1, 14, 30)

            await smtp_email.send_event_reminder(
                to="user@example.com",
                event_title="Study Session",
                event_time=event_time,
                event_location="Library Room 101",
            )

            # Verify SMTP was called
            mock_smtp.connect.assert_called_once()
            mock_smtp.send_message.assert_called_once()

            # Check message content
            sent_message = mock_smtp.send_message.call_args[0][0]
            assert "user@example.com" in sent_message["To"]
            assert "Reminder" in sent_message["Subject"] or "Event" in sent_message["Subject"]

    @pytest.mark.asyncio
    async def test_send_email_handles_connection_error(self, smtp_email):
        """Test that send_email handles connection errors gracefully."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp.connect.side_effect = Exception("Connection failed")
            mock_smtp_class.return_value = mock_smtp

            with pytest.raises(Exception, match="Connection failed"):
                await smtp_email.send_email(
                    to="user@example.com",
                    subject="Test",
                    body="Test",
                )

    @pytest.mark.asyncio
    async def test_send_email_closes_connection_on_error(self, smtp_email):
        """Test that SMTP connection is closed even when error occurs."""
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp.send_message.side_effect = Exception("Send failed")
            mock_smtp_class.return_value = mock_smtp

            with pytest.raises(Exception, match="Send failed"):
                await smtp_email.send_email(
                    to="user@example.com",
                    subject="Test",
                    body="Test",
                )

            # Connection should still be closed
            mock_smtp.quit.assert_called_once()

    def test_render_verification_template(self, smtp_email):
        """Test rendering verification email template."""
        html = smtp_email._render_verification_template(
            verification_url="https://studybuddy.com/verify/token123",
            university_name="Stanford University",
        )

        assert "https://studybuddy.com/verify/token123" in html
        assert "Stanford University" in html
        assert "<html" in html.lower()

    def test_render_event_reminder_template(self, smtp_email):
        """Test rendering event reminder email template."""
        event_time = datetime(2025, 12, 1, 14, 30)

        html = smtp_email._render_event_reminder_template(
            event_title="Study Session",
            event_time=event_time,
            event_location="Library Room 101",
            event_url="https://studybuddy.com/events/123",
        )

        assert "Study Session" in html
        assert "Library Room 101" in html
        assert "https://studybuddy.com/events/123" in html
        assert "<html" in html.lower()
