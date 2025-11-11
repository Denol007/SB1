"""Event type enumeration.

Defines the types of events that can be created in the system.
"""

from enum import Enum


class EventType(str, Enum):
    """Enumeration of event types.

    Events can be one of three types, each determining how participants
    can attend:

    - ONLINE: Virtual events attended remotely via video/chat
    - OFFLINE: In-person events at a physical location
    - HYBRID: Mixed format allowing both online and offline participation

    Example:
        >>> event_type = EventType.ONLINE
        >>> print(event_type.value)
        'online'
        >>> EventType.HYBRID == 'hybrid'
        True
    """

    ONLINE = "online"
    OFFLINE = "offline"
    HYBRID = "hybrid"
