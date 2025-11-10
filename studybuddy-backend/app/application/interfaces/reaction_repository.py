"""Reaction repository interface.

Defines the contract for reaction data access operations.
Follows the Repository pattern from hexagonal architecture.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.enums.reaction_type import ReactionType
from app.infrastructure.database.models.reaction import Reaction


class ReactionRepository(ABC):
    """Abstract repository for reaction data access operations.

    This interface defines all database operations for reactions,
    enabling dependency inversion and testability through mocking.

    Example:
        >>> repository = SQLAlchemyReactionRepository(session)
        >>> reaction = await repository.create(
        ...     user_id=user_uuid,
        ...     post_id=post_uuid,
        ...     reaction_type=ReactionType.LIKE
        ... )
    """

    @abstractmethod
    async def create(
        self,
        user_id: UUID,
        post_id: UUID,
        reaction_type: ReactionType,
    ) -> Reaction:
        """Create a new reaction.

        Args:
            user_id: UUID of the user reacting.
            post_id: UUID of the post being reacted to.
            reaction_type: Type of reaction.

        Returns:
            Created Reaction instance with generated ID.

        Example:
            >>> reaction = await repository.create(
            ...     user_id=user_uuid,
            ...     post_id=post_uuid,
            ...     reaction_type=ReactionType.LOVE
            ... )
        """
        pass

    @abstractmethod
    async def get_by_user_and_post(
        self,
        user_id: UUID,
        post_id: UUID,
    ) -> Reaction | None:
        """Get a user's reaction to a specific post.

        Args:
            user_id: UUID of the user.
            post_id: UUID of the post.

        Returns:
            Reaction instance if found, None otherwise.

        Example:
            >>> reaction = await repository.get_by_user_and_post(
            ...     user_id=user_uuid,
            ...     post_id=post_uuid
            ... )
        """
        pass

    @abstractmethod
    async def update(
        self,
        reaction_id: UUID,
        reaction_type: ReactionType,
    ) -> Reaction:
        """Update a reaction's type.

        Args:
            reaction_id: UUID of the reaction to update.
            reaction_type: New reaction type.

        Returns:
            Updated Reaction instance.

        Example:
            >>> reaction = await repository.update(
            ...     reaction_id=uuid,
            ...     reaction_type=ReactionType.CELEBRATE
            ... )
        """
        pass

    @abstractmethod
    async def delete(self, reaction_id: UUID) -> None:
        """Delete a reaction.

        Args:
            reaction_id: UUID of the reaction to delete.

        Example:
            >>> await repository.delete(uuid)
        """
        pass

    @abstractmethod
    async def count_by_type(self, post_id: UUID) -> dict[ReactionType, int]:
        """Count reactions grouped by type for a post.

        Args:
            post_id: UUID of the post.

        Returns:
            Dictionary mapping reaction types to counts.
            Only includes types with count > 0.

        Example:
            >>> counts = await repository.count_by_type(post_uuid)
            >>> # {ReactionType.LIKE: 15, ReactionType.LOVE: 8}
        """
        pass
