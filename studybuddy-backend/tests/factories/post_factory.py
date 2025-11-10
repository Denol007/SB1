"""Test factories for post, reaction, and comment models.

Factories for generating test data for posts, reactions, and comments using Factory Boy.
Follows TDD - these factories support test-first development for User Story 3 (Social Feed).
"""

from datetime import UTC, datetime
from uuid import uuid4

import factory
from faker import Faker

from app.domain.enums.reaction_type import ReactionType

fake = Faker()


class PostFactory(factory.Factory):
    """Factory for creating Post model instances with realistic test data.

    Uses Factory Boy and Faker to generate posts with random but realistic
    data. Supports both build() for unsaved instances and create() when
    integrated with database session.

    Attributes:
        id: UUID primary key (auto-generated).
        author_id: UUID of the user who created the post.
        community_id: UUID of the community where post was created.
        content: Post content text.
        attachments: Optional JSON array of attachment metadata (images, files, etc.).
        is_pinned: Whether post is pinned (default False).
        edited_at: Timestamp when post was last edited (None if never edited).
        created_at: Timestamp when post was created.
        deleted_at: Soft delete timestamp (None for active posts).

    Example:
        >>> # Build a post instance (not persisted)
        >>> post = PostFactory.build()
        >>> print(post.content)
        'Just finished my CS221 assignment! Anyone else working on Problem Set 3?'

        >>> # Build with specific attributes
        >>> pinned_post = PostFactory.build(
        ...     author_id=user.id,
        ...     community_id=community.id,
        ...     is_pinned=True
        ... )

        >>> # Build with attachments
        >>> post_with_image = PostFactory.build(
        ...     attachments=[
        ...         {"type": "image", "url": "https://example.com/image.jpg"}
        ...     ]
        ... )
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Will be replaced when integrated with actual Post model

    id = factory.LazyFunction(uuid4)
    author_id = factory.LazyFunction(uuid4)
    community_id = factory.LazyFunction(uuid4)
    content = factory.LazyFunction(
        lambda: fake.paragraph(nb_sentences=fake.random_int(min=1, max=5))
    )
    attachments = None  # Default no attachments
    is_pinned = False
    edited_at = None  # Default never edited
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    deleted_at = None  # Default not deleted

    @classmethod
    def with_attachments(cls, **kwargs):
        """Create a post with image attachments.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Post: Post instance with attachments.

        Example:
            >>> post = PostFactory.with_attachments(author_id=user.id)
            >>> print(len(post['attachments']))
            2
        """
        attachments = [
            {
                "type": "image",
                "url": fake.image_url(),
                "filename": f"image_{i}.jpg",
                "size": fake.random_int(min=50000, max=5000000),
            }
            for i in range(fake.random_int(min=1, max=3))
        ]
        return cls.build(attachments=attachments, **kwargs)

    @classmethod
    def pinned(cls, **kwargs):
        """Create a pinned post.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Post: Pinned post instance.

        Example:
            >>> post = PostFactory.pinned(community_id=community.id)
            >>> print(post['is_pinned'])
            True
        """
        return cls.build(is_pinned=True, **kwargs)

    @classmethod
    def edited(cls, **kwargs):
        """Create a post that has been edited.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Post: Edited post instance.

        Example:
            >>> post = PostFactory.edited()
            >>> assert post['edited_at'] is not None
        """
        created_at = kwargs.pop("created_at", datetime.now(UTC))
        edited_at = fake.date_time_between(start_date=created_at, end_date="now", tzinfo=UTC)
        return cls.build(created_at=created_at, edited_at=edited_at, **kwargs)


class ReactionFactory(factory.Factory):
    """Factory for creating Reaction model instances with realistic test data.

    Uses Factory Boy to generate reactions with random reaction types.
    Reactions represent user engagement with posts (like, love, celebrate, support).

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: UUID of the user who created the reaction.
        post_id: UUID of the post being reacted to.
        reaction_type: Type of reaction (like, love, celebrate, support).
        created_at: Timestamp when reaction was created.

    Example:
        >>> # Build a reaction instance (not persisted)
        >>> reaction = ReactionFactory.build()
        >>> print(reaction.reaction_type)
        ReactionType.LIKE

        >>> # Build with specific attributes
        >>> love_reaction = ReactionFactory.build(
        ...     user_id=user.id,
        ...     post_id=post.id,
        ...     reaction_type=ReactionType.LOVE
        ... )

        >>> # Build celebration reaction
        >>> celebrate = ReactionFactory.celebrate(user_id=user.id, post_id=post.id)
        >>> print(celebrate['reaction_type'])
        celebrate
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Will be replaced when integrated with actual Reaction model

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    post_id = factory.LazyFunction(uuid4)
    reaction_type = factory.LazyFunction(lambda: fake.random_element(elements=list(ReactionType)))
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))

    @classmethod
    def like(cls, **kwargs):
        """Create a 'like' reaction.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Reaction: Like reaction instance.

        Example:
            >>> reaction = ReactionFactory.like(user_id=user.id, post_id=post.id)
            >>> print(reaction['reaction_type'])
            like
        """
        return cls.build(reaction_type=ReactionType.LIKE, **kwargs)

    @classmethod
    def love(cls, **kwargs):
        """Create a 'love' reaction.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Reaction: Love reaction instance.

        Example:
            >>> reaction = ReactionFactory.love(user_id=user.id, post_id=post.id)
            >>> print(reaction['reaction_type'])
            love
        """
        return cls.build(reaction_type=ReactionType.LOVE, **kwargs)

    @classmethod
    def celebrate(cls, **kwargs):
        """Create a 'celebrate' reaction.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Reaction: Celebrate reaction instance.

        Example:
            >>> reaction = ReactionFactory.celebrate(user_id=user.id, post_id=post.id)
            >>> print(reaction['reaction_type'])
            celebrate
        """
        return cls.build(reaction_type=ReactionType.CELEBRATE, **kwargs)

    @classmethod
    def support(cls, **kwargs):
        """Create a 'support' reaction.

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Reaction: Support reaction instance.

        Example:
            >>> reaction = ReactionFactory.support(user_id=user.id, post_id=post.id)
            >>> print(reaction['reaction_type'])
            support
        """
        return cls.build(reaction_type=ReactionType.SUPPORT, **kwargs)


class CommentFactory(factory.Factory):
    """Factory for creating Comment model instances with realistic test data.

    Uses Factory Boy and Faker to generate comments with random but realistic
    data. Supports nested comments via parent_comment_id for threaded discussions.

    Attributes:
        id: UUID primary key (auto-generated).
        author_id: UUID of the user who created the comment.
        post_id: UUID of the post being commented on.
        parent_comment_id: Optional UUID of parent comment (for nested replies).
        content: Comment content text.
        created_at: Timestamp when comment was created.
        deleted_at: Soft delete timestamp (None for active comments).

    Example:
        >>> # Build a comment instance (not persisted)
        >>> comment = CommentFactory.build()
        >>> print(comment.content)
        'Great post! I completely agree with your analysis.'

        >>> # Build with specific attributes
        >>> comment = CommentFactory.build(
        ...     author_id=user.id,
        ...     post_id=post.id
        ... )

        >>> # Build a reply to another comment
        >>> reply = CommentFactory.reply(
        ...     post_id=post.id,
        ...     parent_comment_id=parent_comment.id
        ... )
        >>> assert reply['parent_comment_id'] == parent_comment.id
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Will be replaced when integrated with actual Comment model

    id = factory.LazyFunction(uuid4)
    author_id = factory.LazyFunction(uuid4)
    post_id = factory.LazyFunction(uuid4)
    parent_comment_id = None  # Default top-level comment
    content = factory.LazyFunction(lambda: fake.sentence(nb_words=fake.random_int(min=5, max=30)))
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    deleted_at = None  # Default not deleted

    @classmethod
    def reply(cls, **kwargs):
        """Create a reply comment (nested comment).

        Args:
            **kwargs: Additional attributes to override. Must include parent_comment_id.

        Returns:
            Comment: Reply comment instance.

        Example:
            >>> reply = CommentFactory.reply(
            ...     post_id=post.id,
            ...     parent_comment_id=parent_comment.id,
            ...     author_id=user.id
            ... )
            >>> assert reply['parent_comment_id'] is not None
        """
        if "parent_comment_id" not in kwargs:
            kwargs["parent_comment_id"] = uuid4()
        return cls.build(**kwargs)

    @classmethod
    def short(cls, **kwargs):
        """Create a short comment (1-2 sentences).

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Comment: Short comment instance.

        Example:
            >>> comment = CommentFactory.short(author_id=user.id, post_id=post.id)
            >>> len(comment['content'].split()) < 15
            True
        """
        content = fake.sentence(nb_words=fake.random_int(min=3, max=8))
        return cls.build(content=content, **kwargs)

    @classmethod
    def long(cls, **kwargs):
        """Create a long comment (multiple paragraphs).

        Args:
            **kwargs: Additional attributes to override.

        Returns:
            Comment: Long comment instance.

        Example:
            >>> comment = CommentFactory.long(author_id=user.id, post_id=post.id)
            >>> len(comment['content'].split()) > 50
            True
        """
        content = fake.paragraph(nb_sentences=fake.random_int(min=5, max=10))
        return cls.build(content=content, **kwargs)
