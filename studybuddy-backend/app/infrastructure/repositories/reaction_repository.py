"""SQLAlchemy implementation of ReactionRepository.

Provides database operations for reactions using SQLAlchemy async ORM.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.reaction_repository import ReactionRepository
from app.domain.enums.reaction_type import ReactionType
from app.infrastructure.database.models.reaction import Reaction


class SQLAlchemyReactionRepository(ReactionRepository):
    """SQLAlchemy implementation of reaction repository.

    Handles all database operations for reactions using async SQLAlchemy.

    Args:
        session: SQLAlchemy async database session.

    Example:
        >>> async with async_session() as session:
        ...     repository = SQLAlchemyReactionRepository(session)
        ...     reaction = await repository.create(
        ...         user_id=user_uuid,
        ...         post_id=post_uuid,
        ...         reaction_type=ReactionType.LIKE
        ...     )
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

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
        """
        reaction = Reaction(
            user_id=user_id,
            post_id=post_id,
            reaction_type=reaction_type,
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)
        return reaction

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
        """
        result = await self.session.execute(
            select(Reaction).where(
                Reaction.user_id == user_id,
                Reaction.post_id == post_id,
            )
        )
        return result.scalar_one_or_none()

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

        Raises:
            ValueError: If reaction not found.
        """
        result = await self.session.execute(select(Reaction).where(Reaction.id == reaction_id))
        reaction = result.scalar_one_or_none()
        if not reaction:
            raise ValueError(f"Reaction {reaction_id} not found")

        reaction.reaction_type = reaction_type
        await self.session.commit()
        await self.session.refresh(reaction)
        return reaction

    async def delete(self, reaction_id: UUID) -> None:
        """Delete a reaction.

        Args:
            reaction_id: UUID of the reaction to delete.

        Raises:
            ValueError: If reaction not found.
        """
        result = await self.session.execute(select(Reaction).where(Reaction.id == reaction_id))
        reaction = result.scalar_one_or_none()
        if not reaction:
            raise ValueError(f"Reaction {reaction_id} not found")

        await self.session.delete(reaction)
        await self.session.commit()

    async def count_by_type(self, post_id: UUID) -> dict[ReactionType, int]:
        """Count reactions grouped by type for a post.

        Args:
            post_id: UUID of the post.

        Returns:
            Dictionary mapping reaction types to counts.
            Only includes types with count > 0.
        """
        result = await self.session.execute(
            select(
                Reaction.reaction_type,
                func.count(Reaction.id).label("count"),
            )
            .where(Reaction.post_id == post_id)
            .group_by(Reaction.reaction_type)
        )

        counts: dict[ReactionType, int] = {}
        for row in result:
            counts[row.reaction_type] = int(row.count)

        return counts
