"""Email value object with validation.

Provides a validated email representation with domain extraction
and university email detection.
"""

import re


class Email:
    """Email value object with validation and normalization.

    This is an immutable value object that ensures email addresses
    are valid according to a simplified RFC 5322 format.

    Attributes:
        value: The normalized email address (lowercase).
        local_part: The part before the @ symbol.
        domain: The domain part after the @ symbol.
        is_university_email: True if the email is from a .edu domain.

    Raises:
        ValueError: If the email format is invalid.

    Example:
        >>> email = Email("Student@Stanford.EDU")
        >>> email.value
        'student@stanford.edu'
        >>> email.domain
        'stanford.edu'
        >>> email.is_university_email
        True
    """

    # RFC 5321 limits
    MAX_EMAIL_LENGTH = 254
    MAX_LOCAL_PART_LENGTH = 64

    # Simplified email regex (not fully RFC 5322 compliant, but practical)
    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"  # Local part
        r"@"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"  # Domain start
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"  # Subdomains
        r"\.[a-zA-Z]{2,}$"  # TLD
    )

    # Explicit type annotations for MyPy
    value: str
    local_part: str
    domain: str
    is_university_email: bool

    def __init__(self, email: str) -> None:
        """Create a new Email value object with validation.

        Args:
            email: The email address to validate and normalize.

        Raises:
            ValueError: If the email is invalid.
        """
        # Strip whitespace
        email = email.strip()

        # Check for empty
        if not email:
            raise ValueError("Email cannot be empty")

        # Normalize to lowercase
        email = email.lower()

        # Check length
        if len(email) > self.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email too long (max {self.MAX_EMAIL_LENGTH} characters)")

        # Validate format with regex
        if not self.EMAIL_REGEX.match(email):
            raise ValueError("Invalid email format: must be in format local@domain.tld")

        # Split into parts
        if email.count("@") != 1:
            raise ValueError("Invalid email format: must contain exactly one @")

        local, domain = email.split("@")

        # Validate local part
        if not local:
            raise ValueError("Invalid email format: missing local part")

        if len(local) > self.MAX_LOCAL_PART_LENGTH:
            raise ValueError(f"Local part too long (max {self.MAX_LOCAL_PART_LENGTH} characters)")

        # Validate domain
        if not domain:
            raise ValueError("Invalid email format: missing domain")

        # Check if university email (.edu domain)
        is_edu = domain.endswith(".edu")

        # Set attributes (making instance immutable-like)
        object.__setattr__(self, "value", email)
        object.__setattr__(self, "local_part", local)
        object.__setattr__(self, "domain", domain)
        object.__setattr__(self, "is_university_email", is_edu)

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent modification after initialization.

        Args:
            name: Attribute name.
            value: Attribute value.

        Raises:
            AttributeError: Always, to enforce immutability.
        """
        raise AttributeError("Email is immutable")

    def __str__(self) -> str:
        """Return the email address as a string.

        Returns:
            The normalized email address.
        """
        return self.value

    def __repr__(self) -> str:
        """Return a developer-friendly representation.

        Returns:
            A string representation suitable for debugging.
        """
        return f"Email(value='{self.value}')"

    def __eq__(self, other: object) -> bool:
        """Compare two Email objects for equality.

        Args:
            other: Another object to compare.

        Returns:
            True if both are Email objects with the same value.
        """
        if not isinstance(other, Email):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        """Return hash of the email value.

        Returns:
            Hash of the normalized email address.
        """
        return hash(self.value)
