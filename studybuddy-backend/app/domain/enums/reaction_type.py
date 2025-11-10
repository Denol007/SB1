"""Reaction type enumeration for post reactions.

Defines the types of reactions users can add to posts (like, love, celebrate, support).
"""

from enum import Enum


class ReactionType(str, Enum):
    """Enumeration of reaction types for posts.

    Attributes:
        LIKE: Standard like reaction.
        LOVE: Love/heart reaction.
        CELEBRATE: Celebration reaction (for achievements, milestones).
        SUPPORT: Support/solidarity reaction (for challenges, difficulties).

    Example:
        >>> reaction = ReactionType.LIKE
        >>> print(reaction.value)
        'like'

        >>> # Check if string matches enum
        >>> ReactionType('celebrate') == ReactionType.CELEBRATE
        True
    """

    LIKE = "like"
    LOVE = "love"
    CELEBRATE = "celebrate"
    SUPPORT = "support"

    def __str__(self) -> str:
        """Return the string representation of the reaction type.

        Returns:
            str: The reaction type value.
        """
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "ReactionType":
        """Create ReactionType from string value.

        Args:
            value: String representation of reaction type.

        Returns:
            ReactionType: The corresponding enum value.

        Raises:
            ValueError: If value is not a valid reaction type.

        Example:
            >>> reaction = ReactionType.from_string('love')
            >>> print(reaction)
            love
        """
        try:
            return cls(value.lower())
        except ValueError as e:
            valid_types = ", ".join([r.value for r in cls])
            raise ValueError(
                f"Invalid reaction type: {value}. Must be one of: {valid_types}"
            ) from e
