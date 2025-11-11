"""Event registration status enumeration.

Defines the status states for event registrations in the system.
"""

from enum import Enum


class RegistrationStatus(str, Enum):
    """Enumeration of event registration states.

    Event registrations track participant involvement through different states:

    - REGISTERED: User successfully registered and has a confirmed spot
    - WAITLISTED: Event at capacity, user is on waitlist awaiting opening
    - ATTENDED: User attended the event (marked after event completion)
    - NO_SHOW: User registered but did not attend the event

    Example:
        >>> status = RegistrationStatus.REGISTERED
        >>> print(status.value)
        'registered'
        >>> RegistrationStatus.WAITLISTED == 'waitlisted'
        True
    """

    REGISTERED = "registered"
    WAITLISTED = "waitlisted"
    ATTENDED = "attended"
    NO_SHOW = "no_show"
