"""Unit tests for abstract email backend.

Following TDD principles:
1. Write tests FIRST (they should FAIL)
2. Implement the feature
3. Run tests (they should PASS)
4. Refactor while keeping tests passing
"""

import pytest

from app.infrastructure.email_service.base import EmailBackend


class TestEmailBackend:
    """Test cases for abstract EmailBackend class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that EmailBackend cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            EmailBackend()

    def test_requires_send_email_method(self):
        """Test that subclasses must implement send_email method."""

        class IncompleteEmailBackend(EmailBackend):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteEmailBackend()

    def test_requires_send_verification_email_method(self):
        """Test that subclasses must implement send_verification_email method."""

        class PartialEmailBackend(EmailBackend):
            async def send_email(self, to, subject, body, html=None):
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            PartialEmailBackend()

    def test_requires_send_event_reminder_method(self):
        """Test that subclasses must implement send_event_reminder method."""

        class AlmostCompleteEmailBackend(EmailBackend):
            async def send_email(self, to, subject, body, html=None):
                pass

            async def send_verification_email(self, to, token, university_name):
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            AlmostCompleteEmailBackend()

    def test_can_instantiate_complete_implementation(self):
        """Test that a complete implementation can be instantiated."""

        class CompleteEmailBackend(EmailBackend):
            async def send_email(self, to, subject, body, html=None):
                pass

            async def send_verification_email(self, to, token, university_name):
                pass

            async def send_event_reminder(self, to, event_title, event_time, event_location):
                pass

            async def send_event_cancellation(
                self, to, event_title, event_time, cancellation_reason
            ):
                pass

        # Should not raise
        backend = CompleteEmailBackend()
        assert backend is not None
        assert isinstance(backend, EmailBackend)
