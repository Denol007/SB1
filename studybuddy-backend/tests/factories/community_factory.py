"""Test factories for community and membership models.

Factories for generating test data for communities and memberships using Factory Boy.
Follows TDD - these factories support test-first development.
"""

from datetime import UTC, datetime
from uuid import uuid4

import factory

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole


class CommunityFactory(factory.Factory):
    """Factory for creating Community model instances with realistic test data.

    Uses Factory Boy and Faker to generate communities with random but realistic
    data. Supports both build() for unsaved instances and create() when
    integrated with database session.

    Attributes:
        id: UUID primary key (auto-generated).
        name: Community name.
        description: Community description.
        type: Community type (university, business, student_council, hobby).
        visibility: Visibility setting (public, private, closed).
        parent_id: Optional parent community UUID (for hierarchical communities).
        requires_verification: Whether student verification is required.
        avatar_url: URL to community avatar image (optional).
        cover_url: URL to community cover image (optional).
        member_count: Number of members (default 0).
        created_at: Timestamp when community was created.
        updated_at: Timestamp when community was last updated.
        deleted_at: Soft delete timestamp (None for active communities).

    Example:
        >>> # Build a community instance (not persisted)
        >>> community = CommunityFactory.build()
        >>> print(community.name)
        'Stanford Computer Science'

        >>> # Build with specific attributes
        >>> private_community = CommunityFactory.build(
        ...     type=CommunityType.UNIVERSITY,
        ...     visibility=CommunityVisibility.PRIVATE,
        ...     requires_verification=True
        ... )

        >>> # Create a hierarchy of communities
        >>> parent = CommunityFactory.build(type=CommunityType.UNIVERSITY)
        >>> child = CommunityFactory.build(
        ...     type=CommunityType.UNIVERSITY,
        ...     parent_id=parent['id']
        ... )
    """

    class Meta:
        """Factory configuration."""

        model = dict

    # Primary key
    id = factory.LazyFunction(uuid4)

    # Basic information
    name = factory.Faker(
        "random_element",
        elements=[
            "Stanford Computer Science",
            "MIT Engineering Club",
            "Harvard Business Society",
            "Berkeley Data Science",
            "Yale Literature Circle",
            "Princeton Physics Lab",
            "Cornell Agriculture Forum",
            "Columbia Journalism",
            "Penn Medicine",
            "Brown Arts & Culture",
        ],
    )

    description = factory.Faker(
        "random_element",
        elements=[
            "A vibrant community for students and enthusiasts to connect, share knowledge, and collaborate.",
            "Join us to explore ideas, build projects, and grow together in a supportive environment.",
            "Connect with peers, attend events, and participate in discussions about topics you're passionate about.",
            "An inclusive space for learning, networking, and making lasting connections.",
            "Share your experiences, ask questions, and engage with a community of like-minded individuals.",
        ],
    )

    # Community settings
    type = factory.Faker(
        "random_element",
        elements=[
            CommunityType.UNIVERSITY,
            CommunityType.BUSINESS,
            CommunityType.STUDENT_COUNCIL,
            CommunityType.HOBBY,
        ],
    )

    visibility = factory.Faker(
        "random_element",
        elements=[
            CommunityVisibility.PUBLIC,
            CommunityVisibility.PRIVATE,
            CommunityVisibility.CLOSED,
        ],
    )

    # Hierarchical relationship (nullable)
    parent_id = None

    # Verification requirement (primarily for university communities)
    requires_verification = factory.Faker("boolean", chance_of_getting_true=30)

    # Media URLs (optional)
    avatar_url = factory.Faker(
        "random_element",
        elements=[
            None,
            "https://example.com/avatars/community1.jpg",
            "https://example.com/avatars/community2.jpg",
            "https://example.com/avatars/community3.jpg",
        ],
    )

    cover_url = factory.Faker(
        "random_element",
        elements=[
            None,
            "https://example.com/covers/community1.jpg",
            "https://example.com/covers/community2.jpg",
            "https://example.com/covers/community3.jpg",
        ],
    )

    # Statistics
    member_count = factory.Faker("random_int", min=0, max=10000)

    # Timestamps
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))

    # Soft delete (None = not deleted)
    deleted_at = None


class MembershipFactory(factory.Factory):
    """Factory for creating Membership model instances with realistic test data.

    Uses Factory Boy to generate memberships with random but realistic
    data. Supports both build() for unsaved instances and create() when
    integrated with database session.

    Attributes:
        id: UUID primary key (auto-generated).
        user_id: UUID foreign key to user.
        community_id: UUID foreign key to community.
        role: Membership role (admin, moderator, member).
        joined_at: Timestamp when user joined the community.

    Example:
        >>> # Build a membership instance (not persisted)
        >>> membership = MembershipFactory.build()
        >>> print(membership.role)
        MembershipRole.MEMBER

        >>> # Build with specific attributes
        >>> admin_membership = MembershipFactory.build(
        ...     role=MembershipRole.ADMIN,
        ...     user_id=uuid4(),
        ...     community_id=uuid4()
        ... )

        >>> # Create multiple memberships for a community
        >>> community_id = uuid4()
        >>> admin = MembershipFactory.build(
        ...     community_id=community_id,
        ...     role=MembershipRole.ADMIN
        ... )
        >>> moderator = MembershipFactory.build(
        ...     community_id=community_id,
        ...     role=MembershipRole.MODERATOR
        ... )
        >>> member = MembershipFactory.build(
        ...     community_id=community_id,
        ...     role=MembershipRole.MEMBER
        ... )
    """

    class Meta:
        """Factory configuration."""

        model = dict

    # Primary key
    id = factory.LazyFunction(uuid4)

    # Foreign keys
    user_id = factory.LazyFunction(uuid4)
    community_id = factory.LazyFunction(uuid4)

    # Role assignment
    # Most memberships are regular members, fewer moderators, fewest admins
    role = factory.Faker(
        "random_element",
        elements=[
            MembershipRole.MEMBER,
            MembershipRole.MEMBER,
            MembershipRole.MEMBER,
            MembershipRole.MEMBER,
            MembershipRole.MEMBER,
            MembershipRole.MODERATOR,
            MembershipRole.MODERATOR,
            MembershipRole.ADMIN,
        ],
    )

    # Timestamp
    joined_at = factory.Faker(
        "date_time_between",
        start_date="-2y",
        end_date="now",
        tzinfo=UTC,
    )
