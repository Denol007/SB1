"""Unit tests for EventType enumeration.

Tests the EventType enum to ensure proper values and string equality.
"""

import pytest

from app.domain.enums.event_type import EventType


class TestEventType:
    """Test cases for EventType enumeration."""

    def test_event_type_values(self):
        """Test that all event type values are correct."""
        assert EventType.ONLINE.value == "online"
        assert EventType.OFFLINE.value == "offline"
        assert EventType.HYBRID.value == "hybrid"

    def test_event_type_string_equality(self):
        """Test that EventType can be compared with strings."""
        assert EventType.ONLINE == "online"
        assert EventType.OFFLINE == "offline"
        assert EventType.HYBRID == "hybrid"

    def test_event_type_members(self):
        """Test that EventType has exactly three members."""
        assert len(EventType) == 3
        assert set(EventType) == {
            EventType.ONLINE,
            EventType.OFFLINE,
            EventType.HYBRID,
        }

    def test_event_type_from_value(self):
        """Test creating EventType from string values."""
        assert EventType("online") == EventType.ONLINE
        assert EventType("offline") == EventType.OFFLINE
        assert EventType("hybrid") == EventType.HYBRID

    def test_event_type_invalid_value(self):
        """Test that invalid values raise ValueError."""
        with pytest.raises(ValueError):
            EventType("invalid")

    def test_event_type_is_string_enum(self):
        """Test that EventType is a string enum."""
        assert isinstance(EventType.ONLINE, str)
        assert isinstance(EventType.OFFLINE.value, str)

    def test_event_type_iteration(self):
        """Test iteration over EventType values."""
        types = list(EventType)
        assert len(types) == 3
        assert EventType.ONLINE in types
        assert EventType.OFFLINE in types
        assert EventType.HYBRID in types

    def test_event_type_string_representation(self):
        """Test string representation of EventType."""
        assert EventType.ONLINE.value == "online"
        assert EventType.OFFLINE.value == "offline"
        assert EventType.HYBRID.value == "hybrid"

    def test_event_type_names(self):
        """Test that EventType member names are correct."""
        assert EventType.ONLINE.name == "ONLINE"
        assert EventType.OFFLINE.name == "OFFLINE"
        assert EventType.HYBRID.name == "HYBRID"

    def test_event_type_in_dict(self):
        """Test using EventType as dictionary keys."""
        event_counts = {
            EventType.ONLINE: 5,
            EventType.OFFLINE: 3,
            EventType.HYBRID: 2,
        }
        assert event_counts[EventType.ONLINE] == 5
        assert event_counts[EventType.OFFLINE] == 3
        assert event_counts[EventType.HYBRID] == 2
