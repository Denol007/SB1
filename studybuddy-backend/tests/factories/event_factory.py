"""Test factories for Event and EventRegistration models.

Provides Factory Boy factories for creating test instances of events
and event registrations with realistic fake data.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import factory
from factory import fuzzy

from tests.factories.community_factory import CommunityFactory
from tests.factories.user_factory import UserFactory


class EventFactory(factory.Factory):
    """Factory for creating Event test instances.

    Generates realistic event data for testing using Faker.
    Supports online, offline, and hybrid events with various statuses.

    Example:
        >>> event = EventFactory()
        >>> event.title
        'Python Workshop: Advanced Topics'
        >>> event.type
        'online'

        >>> offline_event = EventFactory.offline()
        >>> offline_event.location
        'Stanford University, Main Campus'
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Will be replaced with Event model when available

    # Primary fields
    id = factory.LazyFunction(uuid4)
    community_id = factory.LazyFunction(lambda: CommunityFactory().get("id"))
    creator_id = factory.LazyFunction(lambda: UserFactory().get("id"))

    # Event details
    title = factory.Faker(
        "sentence",
        nb_words=4,
        variable_nb_words=True,
    )
    description = factory.Faker("paragraph", nb_sentences=3)

    # Event type: online, offline, hybrid
    type = fuzzy.FuzzyChoice(["online", "offline", "hybrid"])

    # Location (for offline/hybrid events)
    location = factory.LazyAttribute(
        lambda obj: (
            factory.Faker("address").evaluate(None, None, {"locale": "en_US"})
            if obj.type in ("offline", "hybrid")
            else None
        )
    )

    # Event timing - default to 7 days from now
    start_time = factory.LazyFunction(lambda: datetime.now(UTC) + timedelta(days=7))
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time + timedelta(hours=2)  # 2 hour duration by default
    )

    # Capacity settings
    participant_limit = fuzzy.FuzzyInteger(10, 100)

    # Event status: draft, published, completed, cancelled
    status = fuzzy.FuzzyChoice(["draft", "published", "completed", "cancelled"])

    # Timestamps
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))

    @classmethod
    def online(cls, **kwargs):
        """Create an online event.

        Returns:
            Event instance configured for online delivery.
        """
        kwargs.setdefault("type", "online")
        kwargs.setdefault("location", None)
        return cls(**kwargs)

    @classmethod
    def offline(cls, **kwargs):
        """Create an offline (in-person) event.

        Returns:
            Event instance configured for in-person attendance.
        """
        kwargs.setdefault("type", "offline")
        kwargs.setdefault(
            "location", "Stanford University, Main Campus, Room 101, Palo Alto, CA 94305"
        )
        return cls(**kwargs)

    @classmethod
    def hybrid(cls, **kwargs):
        """Create a hybrid event (both online and offline).

        Returns:
            Event instance configured for hybrid attendance.
        """
        kwargs.setdefault("type", "hybrid")
        kwargs.setdefault(
            "location",
            "MIT Student Center, Building W20, 84 Massachusetts Ave, Cambridge, MA 02139",
        )
        return cls(**kwargs)

    @classmethod
    def draft(cls, **kwargs):
        """Create an event in draft status.

        Returns:
            Event instance in draft status (not yet published).
        """
        kwargs.setdefault("status", "draft")
        return cls(**kwargs)

    @classmethod
    def published(cls, **kwargs):
        """Create a published event.

        Returns:
            Event instance in published status (visible to members).
        """
        kwargs.setdefault("status", "published")
        return cls(**kwargs)

    @classmethod
    def completed(cls, **kwargs):
        """Create a completed event.

        Returns:
            Event instance in completed status (event has ended).
        """
        kwargs.setdefault("status", "completed")
        kwargs.setdefault("start_time", datetime.now(UTC) - timedelta(days=2))
        kwargs.setdefault("end_time", datetime.now(UTC) - timedelta(days=2, hours=-2))
        return cls(**kwargs)

    @classmethod
    def cancelled(cls, **kwargs):
        """Create a cancelled event.

        Returns:
            Event instance in cancelled status.
        """
        kwargs.setdefault("status", "cancelled")
        return cls(**kwargs)

    @classmethod
    def starting_soon(cls, **kwargs):
        """Create an event starting in 1 hour.

        Returns:
            Event instance starting very soon (for reminder testing).
        """
        kwargs.setdefault("status", "published")
        kwargs.setdefault("start_time", datetime.now(UTC) + timedelta(hours=1))
        kwargs.setdefault("end_time", datetime.now(UTC) + timedelta(hours=1) + timedelta(hours=2))
        return cls(**kwargs)

    @classmethod
    def full_capacity(cls, **kwargs):
        """Create an event at full capacity.

        Returns:
            Event instance with participant_limit set to a small number
            (useful for testing waitlist functionality).
        """
        kwargs.setdefault("participant_limit", 2)
        return cls(**kwargs)

    @classmethod
    def unlimited_capacity(cls, **kwargs):
        """Create an event with no participant limit.

        Returns:
            Event instance with no capacity restrictions.
        """
        kwargs.setdefault("participant_limit", None)
        return cls(**kwargs)


class EventRegistrationFactory(factory.Factory):
    """Factory for creating EventRegistration test instances.

    Generates realistic event registration data for testing.
    Supports different registration statuses.

    Example:
        >>> registration = EventRegistrationFactory()
        >>> registration.status
        'registered'

        >>> waitlisted = EventRegistrationFactory.waitlisted()
        >>> waitlisted.status
        'waitlisted'
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Will be replaced with EventRegistration model when available

    # Primary fields
    id = factory.LazyFunction(uuid4)
    event_id = factory.LazyFunction(lambda: EventFactory().get("id"))
    user_id = factory.LazyFunction(lambda: UserFactory().get("id"))

    # Registration status: registered, waitlisted, attended, no_show
    status = fuzzy.FuzzyChoice(["registered", "waitlisted", "attended", "no_show"])

    # Timestamp
    registered_at = factory.LazyFunction(lambda: datetime.now(UTC))

    @classmethod
    def registered(cls, **kwargs):
        """Create a registration with 'registered' status.

        Returns:
            EventRegistration instance in registered status.
        """
        kwargs.setdefault("status", "registered")
        return cls(**kwargs)

    @classmethod
    def waitlisted(cls, **kwargs):
        """Create a registration with 'waitlisted' status.

        Returns:
            EventRegistration instance in waitlisted status (event at capacity).
        """
        kwargs.setdefault("status", "waitlisted")
        return cls(**kwargs)

    @classmethod
    def attended(cls, **kwargs):
        """Create a registration with 'attended' status.

        Returns:
            EventRegistration instance marked as attended (after event).
        """
        kwargs.setdefault("status", "attended")
        return cls(**kwargs)

    @classmethod
    def no_show(cls, **kwargs):
        """Create a registration with 'no_show' status.

        Returns:
            EventRegistration instance marked as no-show (registered but didn't attend).
        """
        kwargs.setdefault("status", "no_show")
        return cls(**kwargs)

    @classmethod
    def for_event(cls, event_id, **kwargs):
        """Create a registration for a specific event.

        Args:
            event_id: UUID of the event to register for.

        Returns:
            EventRegistration instance for the specified event.
        """
        kwargs.setdefault("event_id", event_id)
        return cls(**kwargs)

    @classmethod
    def for_user(cls, user_id, **kwargs):
        """Create a registration for a specific user.

        Args:
            user_id: UUID of the user registering.

        Returns:
            EventRegistration instance for the specified user.
        """
        kwargs.setdefault("user_id", user_id)
        return cls(**kwargs)
