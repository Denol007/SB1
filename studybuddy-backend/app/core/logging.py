"""Structured logging configuration using structlog.

This module configures structlog for the application, providing:
- JSON logging for production environments
- Console logging for development
- Request ID tracking across all logs
- PII redaction (passwords, tokens, secret keys)
- Contextual logging with user IDs and other metadata
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable for request ID tracking across async boundaries
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def add_request_id(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add request ID to log event dictionary.

    This processor adds a unique request ID to every log entry. If a request ID
    is already set in the context variable (e.g., from middleware), it uses that.
    Otherwise, it generates a new UUID.

    Args:
        logger: The logger instance.
        method_name: The name of the logging method called.
        event_dict: The event dictionary to process.

    Returns:
        The event dictionary with request_id added.

    Example:
        >>> logger.info("Processing request", user_id="123")
        {"event": "Processing request", "request_id": "abc-123", "user_id": "123"}
    """
    request_id = request_id_var.get()
    if not request_id:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

    event_dict["request_id"] = request_id
    return event_dict


def redact_pii(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Redact personally identifiable information from logs.

    This processor replaces sensitive field values with '***REDACTED***' to prevent
    accidental logging of passwords, tokens, or secret keys.

    Args:
        logger: The logger instance.
        method_name: The name of the logging method called.
        event_dict: The event dictionary to process.

    Returns:
        The event dictionary with sensitive fields redacted.

    Example:
        >>> logger.info("User login", email="user@example.com", password="secret")
        {"event": "User login", "email": "user@example.com", "password": "***REDACTED***"}
    """
    sensitive_fields = {
        "password",
        "token",
        "secret_key",
        "access_token",
        "refresh_token",
        "api_key",
        "auth_token",
        "jwt_secret",
        "client_secret",
    }

    def _redact_dict(data: Any) -> Any:
        """Recursively redact sensitive fields in nested dictionaries."""
        if isinstance(data, dict):
            return {
                key: "***REDACTED***" if key in sensitive_fields else _redact_dict(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [_redact_dict(item) for item in data]
        else:
            return data

    return _redact_dict(event_dict)


def configure_logging(json_logs: bool = True) -> None:
    """Configure structlog for the application.

    Sets up structlog with appropriate processors for production or development.
    In production (json_logs=True), outputs structured JSON logs. In development
    (json_logs=False), outputs human-readable console logs.

    Args:
        json_logs: If True, use JSON formatting (production).
                   If False, use console formatting (development).

    Example:
        >>> # Production
        >>> configure_logging(json_logs=True)
        >>> # Development
        >>> configure_logging(json_logs=False)
    """
    # Shared processors for all environments
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # Merge context variables
        structlog.stdlib.add_log_level,  # Add log level name
        structlog.stdlib.add_logger_name,  # Add logger name
        structlog.processors.TimeStamper(fmt="iso"),  # Add ISO 8601 timestamp
        structlog.processors.StackInfoRenderer(),  # Render stack traces
        add_request_id,  # Add request ID to all logs
        redact_pii,  # Redact sensitive information
    ]

    # Environment-specific final processor
    if json_logs:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,  # Format exception info
            structlog.processors.JSONRenderer(),  # Render as JSON
        ]
    else:
        # Development: Console output with colors
        processors = shared_processors + [
            structlog.processors.format_exc_info,  # Format exception info
            structlog.dev.ConsoleRenderer(),  # Render with colors
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def setup_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Create a configured logger instance.

    This is the primary way to get a logger in the application. It returns
    a structlog BoundLogger that automatically includes all configured processors.

    Args:
        name: The name of the logger, typically __name__ of the module.

    Returns:
        A configured structlog logger instance.

    Example:
        >>> # In a module
        >>> logger = setup_logger(__name__)
        >>> logger.info("User created", user_id="123", email="user@example.com")
        >>> logger.error("Database connection failed", error="timeout")
        >>> try:
        >>>     risky_operation()
        >>> except Exception as e:
        >>>     logger.exception("Operation failed", operation="risky")
    """
    return structlog.get_logger(name)


# Convenience function to set request ID in context
def set_request_id(request_id: str) -> None:
    """Set the request ID in the context variable.

    This is typically called by middleware at the start of each request.

    Args:
        request_id: The unique request identifier (usually a UUID).

    Example:
        >>> # In middleware
        >>> set_request_id(str(uuid.uuid4()))
        >>> logger.info("Request started")  # Will include the request_id
    """
    request_id_var.set(request_id)


# Convenience function to get current request ID
def get_request_id() -> str:
    """Get the current request ID from the context variable.

    Returns:
        The current request ID, or empty string if not set.

    Example:
        >>> current_id = get_request_id()
        >>> print(f"Current request: {current_id}")
    """
    return request_id_var.get()
