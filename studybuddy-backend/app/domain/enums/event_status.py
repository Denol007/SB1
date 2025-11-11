"""Event status enumeration.

Defines the lifecycle states of events in the system.
"""

from enum import Enum


class EventStatus(str, Enum):
    """Enumeration of event lifecycle states.

    Events progress through different states from creation to completion:

    - DRAFT: Event is being created but not yet visible to members
    - PUBLISHED: Event is live and accepting registrations
    - COMPLETED: Event has finished (automatically set after end_time)
    - CANCELLED: Event was cancelled by moderator/creator

    Example:
        >>> event_status = EventStatus.PUBLISHED
        >>> print(event_status.value)
        'published'
        >>> EventStatus.CANCELLED == 'cancelled'
        True
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
