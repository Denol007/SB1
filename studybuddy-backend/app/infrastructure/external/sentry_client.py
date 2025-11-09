"""Sentry client for error tracking and performance monitoring.

This module provides integration with Sentry for comprehensive error tracking,
performance monitoring, and release tracking in the StudyBuddy application.
"""

import logging
from typing import Any, Literal

import sentry_sdk
from sentry_sdk._types import Event
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

logger = logging.getLogger(__name__)


def init_sentry(
    dsn: str | None,
    environment: str = "development",
    traces_sample_rate: float = 0.1,
    release: str | None = None,
) -> None:
    """Initialize Sentry SDK for error and performance monitoring.

    Args:
        dsn: Sentry Data Source Name (DSN) for the project.
            If None or empty, Sentry will not be initialized.
        environment: Deployment environment (development, staging, production).
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0).
            Default is 0.1 (10% of transactions).
        release: Application release version for tracking.
            Format: "studybuddy@{version}"

    Returns:
        None
    """
    if not dsn:
        logger.info("Sentry DSN not provided. Skipping Sentry initialization.")
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            release=release,
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="url"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR,  # Send errors and above as events
                ),
            ],
            # Additional settings
            send_default_pii=False,  # Don't send PII (GDPR compliance)
            attach_stacktrace=True,  # Attach stack traces to messages
            before_send=_before_send,  # Filter/modify events before sending
        )
        logger.info(f"Sentry initialized successfully for environment: {environment}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _before_send(event: Event, hint: dict[str, Any]) -> Event | None:
    """Filter and modify events before sending to Sentry.

    Args:
        event: The event data dictionary.
        hint: Additional context about the event.

    Returns:
        The modified event dictionary, or None to drop the event.
    """
    # Example: Filter out certain errors or add additional context
    # For now, just return the event as-is
    return event


def capture_exception(exception: Exception, **kwargs: Any) -> None:
    """Capture an exception and send it to Sentry.

    Args:
        exception: The exception to capture.
        **kwargs: Additional keyword arguments to pass to Sentry.

    Returns:
        None
    """
    sentry_sdk.capture_exception(exception, **kwargs)


def capture_message(
    message: str,
    level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info",
    **kwargs: Any,
) -> None:
    """Capture a message and send it to Sentry.

    Args:
        message: The message to capture.
        level: Severity level (debug, info, warning, error, fatal).
        **kwargs: Additional keyword arguments to pass to Sentry.

    Returns:
        None
    """
    sentry_sdk.capture_message(message, level=level, **kwargs)


def set_user_context(
    user_id: str | None = None,
    email: str | None = None,
    username: str | None = None,
    **kwargs: Any,
) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: The user's unique identifier.
        email: The user's email address.
        username: The user's username.
        **kwargs: Additional user attributes.

    Returns:
        None
    """
    user_data = {
        "id": user_id,
        "email": email,
        "username": username,
        **kwargs,
    }
    sentry_sdk.set_user(user_data)


def set_tag(key: str, value: Any) -> None:
    """Set a tag for Sentry events.

    Tags are key-value pairs that can be used to filter and search events.

    Args:
        key: The tag key.
        value: The tag value.

    Returns:
        None
    """
    sentry_sdk.set_tag(key, value)


def clear_user_context() -> None:
    """Clear the current user context.

    Useful when logging out or switching users.

    Returns:
        None
    """
    sentry_sdk.set_user(None)
