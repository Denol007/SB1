"""Unit tests for Sentry client integration."""

from unittest.mock import patch

from app.infrastructure.external.sentry_client import (
    capture_exception,
    capture_message,
    init_sentry,
    set_tag,
    set_user_context,
)


class TestSentryInitialization:
    """Tests for Sentry initialization."""

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.init")
    def test_init_sentry_with_dsn(self, mock_sentry_init):
        """Test that Sentry is initialized when DSN is provided."""
        dsn = "https://example@sentry.io/123456"
        environment = "production"

        init_sentry(dsn=dsn, environment=environment)

        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args.kwargs
        assert call_kwargs["dsn"] == dsn
        assert call_kwargs["environment"] == environment
        assert call_kwargs["traces_sample_rate"] == 0.1
        assert "integrations" in call_kwargs

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.init")
    def test_init_sentry_without_dsn(self, mock_sentry_init):
        """Test that Sentry is not initialized when DSN is not provided."""
        init_sentry(dsn=None, environment="development")

        mock_sentry_init.assert_not_called()

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.init")
    def test_init_sentry_with_empty_dsn(self, mock_sentry_init):
        """Test that Sentry is not initialized when DSN is empty string."""
        init_sentry(dsn="", environment="development")

        mock_sentry_init.assert_not_called()


class TestSentryErrorCapture:
    """Tests for Sentry error capture."""

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.capture_exception")
    def test_capture_exception(self, mock_capture):
        """Test capturing an exception."""
        exception = ValueError("Test error")

        capture_exception(exception)

        mock_capture.assert_called_once_with(exception)

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.capture_message")
    def test_capture_message(self, mock_capture):
        """Test capturing a message."""
        message = "Test message"
        level = "warning"

        capture_message(message, level=level)

        mock_capture.assert_called_once_with(message, level=level)

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.capture_message")
    def test_capture_message_default_level(self, mock_capture):
        """Test capturing a message with default level."""
        message = "Test message"

        capture_message(message)

        mock_capture.assert_called_once_with(message, level="info")


class TestSentryContext:
    """Tests for Sentry context setting."""

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.set_user")
    def test_set_user_context(self, mock_set_user):
        """Test setting user context."""
        user_id = "user-123"
        email = "test@example.com"
        username = "testuser"

        set_user_context(user_id=user_id, email=email, username=username)

        mock_set_user.assert_called_once_with(
            {
                "id": user_id,
                "email": email,
                "username": username,
            }
        )

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.set_user")
    def test_set_user_context_partial(self, mock_set_user):
        """Test setting user context with partial data."""
        user_id = "user-123"

        set_user_context(user_id=user_id)

        mock_set_user.assert_called_once_with(
            {
                "id": user_id,
                "email": None,
                "username": None,
            }
        )

    @patch("app.infrastructure.external.sentry_client.sentry_sdk.set_tag")
    def test_set_tag(self, mock_set_tag):
        """Test setting a tag."""
        key = "feature"
        value = "authentication"

        set_tag(key, value)

        mock_set_tag.assert_called_once_with(key, value)
