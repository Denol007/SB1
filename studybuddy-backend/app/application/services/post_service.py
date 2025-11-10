"""Post service for business logic.

Handles:
- Post creation, updates, and deletion (soft delete)
- Community feed with pagination and pinned posts
- Post pinning/unpinning (moderator+)
- Reaction management (add, remove, count)
- Permission checks (author, moderator, admin)
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.application.interfaces.comment_repository import CommentRepository
from app.application.interfaces.membership_repository import MembershipRepository
from app.application.interfaces.post_repository import PostRepository
from app.application.interfaces.reaction_repository import ReactionRepository
from app.domain.enums.membership_role import MembershipRole
from app.domain.enums.reaction_type import ReactionType
from app.infrastructure.database.models.post import Post
from app.infrastructure.database.models.reaction import Reaction


class PostService:
    """Service for post and reaction management.

    This service implements business logic for post operations,
    including creation, updates, deletion, feed retrieval, pinning,
    and reaction management.

    Example:
        >>> service = PostService(post_repo, reaction_repo, comment_repo, membership_repo)
        >>> post = await service.create_post(
        ...     author_id=user_uuid,
        ...     community_id=community_uuid,
        ...     data={"content": "Great study session today!"}
        ... )
    """

    def __init__(
        self,
        post_repository: PostRepository,
        reaction_repository: ReactionRepository,
        comment_repository: CommentRepository,
        membership_repository: MembershipRepository,
    ):
        """Initialize the post service.

        Args:
            post_repository: Repository for post data access.
            reaction_repository: Repository for reaction data access.
            comment_repository: Repository for comment data access.
            membership_repository: Repository for membership data access.
        """
        self.post_repository = post_repository
        self.reaction_repository = reaction_repository
        self.comment_repository = comment_repository
        self.membership_repository = membership_repository

    async def create_post(
        self,
        author_id: UUID,
        community_id: UUID,
        data: dict[str, Any],
    ) -> Post:
        """Create a new post in a community.

        User must be a member of the community to create posts.

        Args:
            author_id: UUID of the user creating the post.
            community_id: UUID of the community to post in.
            data: Post data (content, attachments).

        Returns:
            Created Post instance.

        Raises:
            HTTPException 403: If user is not a member of the community.
            HTTPException 400: If content is empty.

        Example:
            >>> post = await service.create_post(
            ...     author_id=user_uuid,
            ...     community_id=community_uuid,
            ...     data={
            ...         "content": "Check out these study materials!",
            ...         "attachments": [{"type": "pdf", "url": "..."}]
            ...     }
            ... )
        """
        # Verify user is a member of the community
        membership = await self.membership_repository.get_by_user_and_community(
            user_id=author_id,
            community_id=community_id,
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this community to create posts",
            )

        # Validate content
        content = data.get("content", "").strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Post content cannot be empty",
            )

        # Create the post
        post = await self.post_repository.create(
            author_id=author_id,
            community_id=community_id,
            content=content,
            attachments=data.get("attachments"),
        )

        return post

    async def update_post(
        self,
        post_id: UUID,
        user_id: UUID,
        data: dict[str, Any],
    ) -> Post:
        """Update a post.

        Only the author can update their posts.

        Args:
            post_id: UUID of the post to update.
            user_id: UUID of the user making the update.
            data: Fields to update (content, attachments).

        Returns:
            Updated Post instance.

        Raises:
            HTTPException 404: If post doesn't exist.
            HTTPException 403: If user is not the author.

        Example:
            >>> post = await service.update_post(
            ...     post_id=post_uuid,
            ...     user_id=user_uuid,
            ...     data={"content": "Updated study notes!"}
            ... )
        """
        # Get the post
        post = await self.post_repository.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        # Check if user is the author
        if post.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update this post",
            )

        # Update the post (repository will set edited_at timestamp)
        updated_post = await self.post_repository.update(
            post_id=post_id,
            **data,
        )

        return updated_post

    async def delete_post(
        self,
        post_id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a post (soft delete).

        Authors can delete their own posts.
        Moderators and admins can delete any post in their community.

        Args:
            post_id: UUID of the post to delete.
            user_id: UUID of the user requesting deletion.

        Raises:
            HTTPException 404: If post doesn't exist.
            HTTPException 403: If user is not authorized to delete.

        Example:
            >>> await service.delete_post(
            ...     post_id=post_uuid,
            ...     user_id=user_uuid
            ... )
        """
        # Get the post
        post = await self.post_repository.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        # Check if user is author or has moderator+ role
        is_author = post.author_id == user_id
        is_moderator = await self.membership_repository.has_role(
            user_id=user_id,
            community_id=post.community_id,
            required_role=MembershipRole.MODERATOR,
        )

        if not (is_author or is_moderator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this post",
            )

        # Soft delete the post
        await self.post_repository.delete(post_id)

    async def get_community_feed(
        self,
        community_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Post]:
        """Get paginated community feed.

        Posts are sorted by created_at descending (newest first).
        Pinned posts appear first.

        Args:
            community_id: UUID of the community.
            page: Page number (1-indexed).
            page_size: Number of posts per page.

        Returns:
            List of Post instances for the requested page.

        Example:
            >>> posts = await service.get_community_feed(
            ...     community_id=community_uuid,
            ...     page=1,
            ...     page_size=20
            ... )
        """
        posts = await self.post_repository.list_by_community(
            community_id=community_id,
            page=page,
            page_size=page_size,
            sort_by="created_at",
            descending=True,
        )

        return posts

    async def pin_post(
        self,
        post_id: UUID,
        user_id: UUID,
    ) -> Post:
        """Pin a post to the top of the community feed.

        Only moderators and admins can pin posts.

        Args:
            post_id: UUID of the post to pin.
            user_id: UUID of the user requesting the pin.

        Returns:
            Updated Post instance with is_pinned=True.

        Raises:
            HTTPException 404: If post doesn't exist.
            HTTPException 403: If user is not a moderator.

        Example:
            >>> post = await service.pin_post(
            ...     post_id=post_uuid,
            ...     user_id=moderator_uuid
            ... )
        """
        # Get the post
        post = await self.post_repository.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        # Check if user has moderator+ role
        is_moderator = await self.membership_repository.has_role(
            user_id=user_id,
            community_id=post.community_id,
            required_role=MembershipRole.MODERATOR,
        )

        if not is_moderator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators and admins can pin posts",
            )

        # Pin the post
        updated_post = await self.post_repository.update(
            post_id=post_id,
            is_pinned=True,
        )

        return updated_post

    async def unpin_post(
        self,
        post_id: UUID,
        user_id: UUID,
    ) -> Post:
        """Unpin a post.

        Only moderators and admins can unpin posts.

        Args:
            post_id: UUID of the post to unpin.
            user_id: UUID of the user requesting the unpin.

        Returns:
            Updated Post instance with is_pinned=False.

        Raises:
            HTTPException 404: If post doesn't exist.
            HTTPException 403: If user is not a moderator.

        Example:
            >>> post = await service.unpin_post(
            ...     post_id=post_uuid,
            ...     user_id=moderator_uuid
            ... )
        """
        # Get the post
        post = await self.post_repository.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        # Check if user has moderator+ role
        is_moderator = await self.membership_repository.has_role(
            user_id=user_id,
            community_id=post.community_id,
            required_role=MembershipRole.MODERATOR,
        )

        if not is_moderator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators and admins can unpin posts",
            )

        # Unpin the post
        updated_post = await self.post_repository.update(
            post_id=post_id,
            is_pinned=False,
        )

        return updated_post

    async def add_reaction(
        self,
        post_id: UUID,
        user_id: UUID,
        reaction_type: ReactionType,
    ) -> Reaction:
        """Add or update a reaction to a post.

        If the user already reacted, updates the existing reaction.

        Args:
            post_id: UUID of the post to react to.
            user_id: UUID of the user reacting.
            reaction_type: Type of reaction to add.

        Returns:
            Reaction instance (created or updated).

        Raises:
            HTTPException 404: If post doesn't exist.

        Example:
            >>> reaction = await service.add_reaction(
            ...     post_id=post_uuid,
            ...     user_id=user_uuid,
            ...     reaction_type=ReactionType.LIKE
            ... )
        """
        # Verify post exists
        post = await self.post_repository.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        # Check if user already reacted
        existing_reaction = await self.reaction_repository.get_by_user_and_post(
            user_id=user_id,
            post_id=post_id,
        )

        if existing_reaction:
            # Update existing reaction
            updated_reaction = await self.reaction_repository.update(
                reaction_id=existing_reaction.id,
                reaction_type=reaction_type,
            )
            return updated_reaction
        else:
            # Create new reaction
            reaction = await self.reaction_repository.create(
                user_id=user_id,
                post_id=post_id,
                reaction_type=reaction_type,
            )
            return reaction

    async def remove_reaction(
        self,
        post_id: UUID,
        user_id: UUID,
    ) -> None:
        """Remove a user's reaction from a post.

        Args:
            post_id: UUID of the post.
            user_id: UUID of the user.

        Raises:
            HTTPException 404: If user hasn't reacted to the post.

        Example:
            >>> await service.remove_reaction(
            ...     post_id=post_uuid,
            ...     user_id=user_uuid
            ... )
        """
        # Get the user's reaction
        reaction = await self.reaction_repository.get_by_user_and_post(
            user_id=user_id,
            post_id=post_id,
        )

        if not reaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reaction not found",
            )

        # Delete the reaction
        await self.reaction_repository.delete(reaction.id)

    async def get_post_reactions(
        self,
        post_id: UUID,
    ) -> dict[ReactionType, int]:
        """Get reaction counts grouped by type for a post.

        Args:
            post_id: UUID of the post.

        Returns:
            Dictionary mapping reaction types to counts.

        Example:
            >>> reactions = await service.get_post_reactions(post_uuid)
            >>> # {ReactionType.LIKE: 15, ReactionType.LOVE: 8, ...}
        """
        counts = await self.reaction_repository.count_by_type(post_id)
        return counts
