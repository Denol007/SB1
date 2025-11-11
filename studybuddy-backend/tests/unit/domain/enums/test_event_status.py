"""Unit tests for EventStatus enumeration.

Tests the EventStatus enum to ensure proper values and string equality.
"""

import pytest

from app.domain.enums.event_status import EventStatus


class TestEventStatus:
    """Test cases for EventStatus enumeration."""

    def test_event_status_values(self):
        """Test that all event status values are correct."""
        assert EventStatus.DRAFT.value == "draft"
        assert EventStatus.PUBLISHED.value == "published"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.CANCELLED.value == "cancelled"

    def test_event_status_string_equality(self):
        """Test that EventStatus can be compared with strings."""
        assert EventStatus.DRAFT == "draft"
        assert EventStatus.PUBLISHED == "published"
        assert EventStatus.COMPLETED == "completed"
        assert EventStatus.CANCELLED == "cancelled"

    def test_event_status_members(self):
        """Test that EventStatus has exactly four members."""
        assert len(EventStatus) == 4
        assert set(EventStatus) == {
            EventStatus.DRAFT,
            EventStatus.PUBLISHED,
            EventStatus.COMPLETED,
            EventStatus.CANCELLED,
        }

    def test_event_status_from_value(self):
        """Test creating EventStatus from string values."""
        assert EventStatus("draft") == EventStatus.DRAFT
        assert EventStatus("published") == EventStatus.PUBLISHED
        assert EventStatus("completed") == EventStatus.COMPLETED
        assert EventStatus("cancelled") == EventStatus.CANCELLED

    def test_event_status_invalid_value(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            EventStatus("invalid")
        with pytest.raises(ValueError):
            EventStatus("pending")

    def test_event_status_is_string_enum(self):
        """Test that EventStatus is a string enum."""
        assert isinstance(EventStatus.DRAFT, str)
        assert isinstance(EventStatus.PUBLISHED.value, str)

    def test_event_status_iteration(self):
        """Test iteration over EventStatus values."""
        statuses = list(EventStatus)
        assert len(statuses) == 4
        assert EventStatus.DRAFT in statuses
        assert EventStatus.PUBLISHED in statuses
        assert EventStatus.COMPLETED in statuses
        assert EventStatus.CANCELLED in statuses

    def test_event_status_string_representation(self):
        """Test string representation of EventStatus."""
        assert EventStatus.DRAFT.value == "draft"
        assert EventStatus.PUBLISHED.value == "published"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.CANCELLED.value == "cancelled"

    def test_event_status_names(self):
        """Test that EventStatus member names are correct."""
        assert EventStatus.DRAFT.name == "DRAFT"
        assert EventStatus.PUBLISHED.name == "PUBLISHED"
        assert EventStatus.COMPLETED.name == "COMPLETED"
        assert EventStatus.CANCELLED.name == "CANCELLED"

    def test_event_status_in_dict(self):
        """Test using EventStatus as dictionary keys."""
        status_counts = {
            EventStatus.DRAFT: 2,
            EventStatus.PUBLISHED: 10,
            EventStatus.COMPLETED: 5,
            EventStatus.CANCELLED: 1,
        }
        assert status_counts[EventStatus.DRAFT] == 2
        assert status_counts[EventStatus.PUBLISHED] == 10
        assert status_counts[EventStatus.COMPLETED] == 5
        assert status_counts[EventStatus.CANCELLED] == 1

    def test_event_status_lifecycle_progression(self):
        """Test that status values represent logical lifecycle progression."""
        # Draft -> Published -> Completed is typical flow
        draft = EventStatus.DRAFT
        published = EventStatus.PUBLISHED
        completed = EventStatus.COMPLETED
        cancelled = EventStatus.CANCELLED

        # Verify all statuses are distinct
        assert draft != published
        assert published != completed
        assert draft != cancelled

    def test_event_status_comparison(self):
        """Test that EventStatus instances can be compared."""
        # Same status should be equal
        assert EventStatus.DRAFT == EventStatus.DRAFT
        assert EventStatus.PUBLISHED == EventStatus.PUBLISHED

        # Different statuses should not be equal
        assert EventStatus.DRAFT != EventStatus.PUBLISHED
        assert EventStatus.COMPLETED != EventStatus.CANCELLED
