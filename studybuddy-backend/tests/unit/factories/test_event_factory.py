"""Unit tests for Event and EventRegistration factories.

Tests the factory methods to ensure they generate valid test data
with the expected attributes and relationships.
"""

from datetime import UTC, datetime, timedelta

from tests.factories.event_factory import EventFactory, EventRegistrationFactory


class TestEventFactory:
    """Test EventFactory generates valid event instances."""

    def test_create_basic_event(self):
        """Test creating a basic event with default values."""
        event = EventFactory()

        assert event["id"] is not None
        assert event["community_id"] is not None
        assert event["creator_id"] is not None
        assert event["title"] is not None
        assert event["description"] is not None
        assert event["type"] in ("online", "offline", "hybrid")
        assert event["start_time"] is not None
        assert event["end_time"] is not None
        assert event["end_time"] > event["start_time"]
        assert event["participant_limit"] is not None
        assert event["participant_limit"] >= 10
        assert event["status"] in ("draft", "published", "completed", "cancelled")
        assert event["created_at"] is not None
        assert event["updated_at"] is not None

    def test_create_online_event(self):
        """Test creating an online event."""
        event = EventFactory.online()

        assert event["type"] == "online"
        assert event["location"] is None

    def test_create_offline_event(self):
        """Test creating an offline event with location."""
        event = EventFactory.offline()

        assert event["type"] == "offline"
        assert event["location"] is not None
        assert isinstance(event["location"], str)
        assert len(event["location"]) > 0

    def test_create_hybrid_event(self):
        """Test creating a hybrid event."""
        event = EventFactory.hybrid()

        assert event["type"] == "hybrid"
        assert event["location"] is not None

    def test_create_draft_event(self):
        """Test creating a draft event."""
        event = EventFactory.draft()

        assert event["status"] == "draft"

    def test_create_published_event(self):
        """Test creating a published event."""
        event = EventFactory.published()

        assert event["status"] == "published"

    def test_create_completed_event(self):
        """Test creating a completed event (in the past)."""
        event = EventFactory.completed()

        assert event["status"] == "completed"
        assert event["start_time"] < datetime.now(UTC)
        assert event["end_time"] < datetime.now(UTC)

    def test_create_cancelled_event(self):
        """Test creating a cancelled event."""
        event = EventFactory.cancelled()

        assert event["status"] == "cancelled"

    def test_create_starting_soon_event(self):
        """Test creating an event starting in 1 hour."""
        event = EventFactory.starting_soon()

        assert event["status"] == "published"
        now = datetime.now(UTC)
        assert event["start_time"] > now
        assert event["start_time"] < now + timedelta(hours=2)

    def test_create_full_capacity_event(self):
        """Test creating an event with limited capacity."""
        event = EventFactory.full_capacity()

        assert event["participant_limit"] is not None
        assert event["participant_limit"] == 2

    def test_create_unlimited_capacity_event(self):
        """Test creating an event with no capacity limit."""
        event = EventFactory.unlimited_capacity()

        assert event["participant_limit"] is None

    def test_custom_title(self):
        """Test creating an event with custom title."""
        custom_title = "Python Workshop: Advanced Topics"
        event = EventFactory(title=custom_title)

        assert event["title"] == custom_title

    def test_custom_participant_limit(self):
        """Test creating an event with custom participant limit."""
        event = EventFactory(participant_limit=50)

        assert event["participant_limit"] == 50

    def test_custom_timing(self):
        """Test creating an event with custom start and end times."""
        start = datetime.now(UTC) + timedelta(days=10)
        end = start + timedelta(hours=3)
        event = EventFactory(start_time=start, end_time=end)

        assert event["start_time"] == start
        assert event["end_time"] == end

    def test_multiple_events_have_unique_ids(self):
        """Test that multiple events have unique IDs."""
        event1 = EventFactory()
        event2 = EventFactory()

        assert event1["id"] != event2["id"]


class TestEventRegistrationFactory:
    """Test EventRegistrationFactory generates valid registration instances."""

    def test_create_basic_registration(self):
        """Test creating a basic registration with default values."""
        registration = EventRegistrationFactory()

        assert registration["id"] is not None
        assert registration["event_id"] is not None
        assert registration["user_id"] is not None
        assert registration["status"] in (
            "registered",
            "waitlisted",
            "attended",
            "no_show",
        )
        assert registration["registered_at"] is not None

    def test_create_registered_status(self):
        """Test creating a registration with 'registered' status."""
        registration = EventRegistrationFactory.registered()

        assert registration["status"] == "registered"

    def test_create_waitlisted_status(self):
        """Test creating a registration with 'waitlisted' status."""
        registration = EventRegistrationFactory.waitlisted()

        assert registration["status"] == "waitlisted"

    def test_create_attended_status(self):
        """Test creating a registration with 'attended' status."""
        registration = EventRegistrationFactory.attended()

        assert registration["status"] == "attended"

    def test_create_no_show_status(self):
        """Test creating a registration with 'no_show' status."""
        registration = EventRegistrationFactory.no_show()

        assert registration["status"] == "no_show"

    def test_create_for_specific_event(self):
        """Test creating a registration for a specific event."""
        event = EventFactory()
        registration = EventRegistrationFactory.for_event(event["id"])

        assert registration["event_id"] == event["id"]

    def test_create_for_specific_user(self):
        """Test creating a registration for a specific user."""
        from tests.factories.user_factory import UserFactory

        user = UserFactory()
        registration = EventRegistrationFactory.for_user(user["id"])

        assert registration["user_id"] == user["id"]

    def test_multiple_registrations_have_unique_ids(self):
        """Test that multiple registrations have unique IDs."""
        reg1 = EventRegistrationFactory()
        reg2 = EventRegistrationFactory()

        assert reg1["id"] != reg2["id"]

    def test_registration_timestamp_is_recent(self):
        """Test that registration timestamp is recent (within last minute)."""
        registration = EventRegistrationFactory()

        now = datetime.now(UTC)
        time_diff = now - registration["registered_at"]
        assert time_diff.total_seconds() < 60  # Within last minute


class TestEventFactoryEdgeCases:
    """Test EventFactory edge cases and validation."""

    def test_event_duration_is_positive(self):
        """Test that event end time is always after start time."""
        for _ in range(10):  # Test multiple random generations
            event = EventFactory()
            assert event["end_time"] > event["start_time"]

    def test_participant_limit_is_valid(self):
        """Test that participant limit is a valid number or None."""
        event = EventFactory()
        assert event["participant_limit"] is None or event["participant_limit"] > 0

    def test_location_matches_event_type(self):
        """Test that location is set appropriately based on event type."""
        online = EventFactory.online()
        offline = EventFactory.offline()
        hybrid = EventFactory.hybrid()

        assert online["location"] is None
        assert offline["location"] is not None
        assert hybrid["location"] is not None


class TestEventRegistrationFactoryEdgeCases:
    """Test EventRegistrationFactory edge cases."""

    def test_registration_for_event_and_user(self):
        """Test creating a registration for specific event and user."""
        event = EventFactory()
        from tests.factories.user_factory import UserFactory

        user = UserFactory()

        registration = EventRegistrationFactory(
            event_id=event["id"], user_id=user["id"], status="registered"
        )

        assert registration["event_id"] == event["id"]
        assert registration["user_id"] == user["id"]
        assert registration["status"] == "registered"
