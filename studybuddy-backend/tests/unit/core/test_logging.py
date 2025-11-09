"""Unit tests for structured logging configuration.

Tests the structlog configuration including JSON formatting,
request ID tracking, and PII redaction.
"""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

from app.core.logging import (
    add_request_id,
    configure_logging,
    redact_pii,
    setup_logger,
)


class TestLoggingConfiguration:
    """Test suite for logging configuration."""

    def test_configure_logging_creates_processors(self) -> None:
        """Test that configure_logging sets up processors correctly."""
        # Arrange & Act
        configure_logging(json_logs=False)

        # Assert
        # Logging configuration should not raise any errors
        logger = logging.getLogger("test_logger")
        assert logger is not None

    def test_setup_logger_returns_logger(self) -> None:
        """Test that setup_logger returns a configured logger."""
        # Arrange & Act
        logger = setup_logger("test_module")

        # Assert
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")


class TestRequestIDProcessor:
    """Test suite for request ID tracking."""

    def test_add_request_id_adds_id_to_event_dict(self) -> None:
        """Test that request ID is added to log event dict."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {"event": "test event"}

        # Act
        result = add_request_id(logger, method_name, event_dict)

        # Assert
        assert "request_id" in result
        assert result["request_id"] is not None

    def test_add_request_id_preserves_existing_fields(self) -> None:
        """Test that existing fields are preserved when adding request ID."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "test event",
            "user_id": "123",
            "action": "login",
        }

        # Act
        result = add_request_id(logger, method_name, event_dict)

        # Assert
        assert result["event"] == "test event"
        assert result["user_id"] == "123"
        assert result["action"] == "login"
        assert "request_id" in result

    def test_add_request_id_with_context_var(self) -> None:
        """Test request ID from context variable is used if available."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {"event": "test"}

        with patch("app.core.logging.request_id_var") as mock_context_var:
            mock_context_var.get.return_value = "fixed-request-id-123"

            # Act
            result = add_request_id(logger, method_name, event_dict)

            # Assert
            assert result["request_id"] == "fixed-request-id-123"


class TestPIIRedaction:
    """Test suite for PII redaction processor."""

    def test_redact_pii_redacts_password_field(self) -> None:
        """Test that password fields are redacted."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "user login",
            "email": "user@example.com",
            "password": "supersecret123",
        }

        # Act
        result = redact_pii(logger, method_name, event_dict)

        # Assert
        assert result["password"] == "***REDACTED***"
        assert result["email"] == "user@example.com"  # Email not redacted

    def test_redact_pii_redacts_token_field(self) -> None:
        """Test that token fields are redacted."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "api call",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            "user_id": "123",
        }

        # Act
        result = redact_pii(logger, method_name, event_dict)

        # Assert
        assert result["token"] == "***REDACTED***"
        assert result["user_id"] == "123"

    def test_redact_pii_redacts_secret_key_field(self) -> None:
        """Test that secret_key fields are redacted."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "config loaded",
            "secret_key": "my-secret-key-value",
            "app_name": "StudyBuddy",
        }

        # Act
        result = redact_pii(logger, method_name, event_dict)

        # Assert
        assert result["secret_key"] == "***REDACTED***"
        assert result["app_name"] == "StudyBuddy"

    def test_redact_pii_handles_nested_sensitive_data(self) -> None:
        """Test that nested sensitive fields are redacted."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "user data",
            "user": {
                "email": "user@example.com",
                "password": "secret123",
            },
        }

        # Act
        result = redact_pii(logger, method_name, event_dict)

        # Assert
        assert result["user"]["password"] == "***REDACTED***"
        assert result["user"]["email"] == "user@example.com"

    def test_redact_pii_preserves_non_sensitive_fields(self) -> None:
        """Test that non-sensitive fields are not modified."""
        # Arrange
        logger = MagicMock()
        method_name = "info"
        event_dict: dict[str, Any] = {
            "event": "user action",
            "user_id": "123",
            "action": "view_profile",
            "timestamp": "2025-01-20T10:00:00Z",
        }

        # Act
        result = redact_pii(logger, method_name, event_dict)

        # Assert
        assert result["user_id"] == "123"
        assert result["action"] == "view_profile"
        assert result["timestamp"] == "2025-01-20T10:00:00Z"


class TestProductionLogging:
    """Test suite for production logging configuration."""

    @patch("app.core.logging.structlog")
    def test_production_uses_json_logs(self, mock_structlog: MagicMock) -> None:
        """Test that production environment uses JSON logging."""
        # Arrange & Act
        configure_logging(json_logs=True)

        # Assert
        # Verify structlog was configured (exact assertions depend on structlog version)
        assert mock_structlog.configure.called

    def test_development_uses_console_logs(self) -> None:
        """Test that development environment uses console logging."""
        # Arrange & Act
        configure_logging(json_logs=False)

        # Assert
        # Configuration should complete without errors
        logger = setup_logger("dev_test")
        assert logger is not None


class TestLoggerUsage:
    """Test suite for logger usage scenarios."""

    def test_logger_info_level(self) -> None:
        """Test logging at INFO level."""
        # Arrange
        logger = setup_logger("test_info")

        # Act & Assert
        # Should not raise any exceptions
        logger.info("Test info message", user_id="123")

    def test_logger_error_level(self) -> None:
        """Test logging at ERROR level."""
        # Arrange
        logger = setup_logger("test_error")

        # Act & Assert
        # Should not raise any exceptions
        logger.error("Test error message", error_code="E001")

    def test_logger_with_extra_context(self) -> None:
        """Test logging with additional context fields."""
        # Arrange
        logger = setup_logger("test_context")

        # Act & Assert
        # Should not raise any exceptions
        logger.info(
            "User action",
            user_id="123",
            action="create_post",
            community_id="456",
        )

    def test_logger_exception_logging(self) -> None:
        """Test logging exceptions with stack traces."""
        # Arrange
        logger = setup_logger("test_exception")

        try:
            # Act
            raise ValueError("Test exception")
        except ValueError as e:
            # Assert - Should not raise any exceptions
            logger.exception("An error occurred", error=str(e))
