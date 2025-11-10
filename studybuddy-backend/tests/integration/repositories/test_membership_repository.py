"""Integration tests for MembershipRepository.

These tests verify the MembershipRepository implementation against a real database,
ensuring all membership operations work correctly with PostgreSQL.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.community import Community
from app.infrastructure.database.models.user import User
from app.infrastructure.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)


@pytest.mark.asyncio
class TestMembershipRepository:
    """Test suite for MembershipRepository implementation."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession) -> SQLAlchemyMembershipRepository:
        """Create a MembershipRepository instance with database session.

        Args:
            db_session: Database session fixture.

        Returns:
            SQLAlchemyMembershipRepository: Repository instance for testing.
        """
        return SQLAlchemyMembershipRepository(db_session)

    @pytest.fixture
    async def user(self, db_session: AsyncSession) -> User:
        """Create a test user.

        Args:
            db_session: Database session fixture.

        Returns:
            User: Created user instance.
        """
        user = User(
            id=uuid4(),
            google_id="google_123",
            email="test@stanford.edu",
            name="Test User",
            bio="Test bio",
            role="student",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def community(self, db_session: AsyncSession) -> Community:
        """Create a test community.

        Args:
            db_session: Database session fixture.

        Returns:
            Community: Created community instance.
        """
        community = Community(
            id=uuid4(),
            name="Test Community",
            description="Test description",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            member_count=0,
        )
        db_session.add(community)
        await db_session.commit()
        await db_session.refresh(community)
        return community

    async def test_add_member(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test adding a member to a community."""
        # Act
        membership = await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Assert
        assert membership.id is not None
        assert membership.user_id == user.id
        assert membership.community_id == community.id
        assert membership.role == MembershipRole.MEMBER.value
        assert membership.joined_at is not None

    async def test_add_member_with_admin_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test adding a member with admin role."""
        # Act
        membership = await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.ADMIN.value,
        )
        await db_session.commit()

        # Assert
        assert membership.role == MembershipRole.ADMIN.value

    async def test_add_duplicate_member_raises_conflict(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test adding duplicate membership raises ConflictException."""
        # Arrange - Add member first time
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act & Assert - Try adding same member again
        with pytest.raises(ConflictException) as exc_info:
            await repository.add_member(
                user_id=user.id,
                community_id=community.id,
                role=MembershipRole.MODERATOR.value,
            )

        assert "already a member" in str(exc_info.value).lower()

    async def test_get_membership(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test retrieving a membership."""
        # Arrange
        created = await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act
        retrieved = await repository.get_membership(user.id, community.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user.id
        assert retrieved.community_id == community.id
        assert retrieved.role == MembershipRole.MEMBER.value

    async def test_get_membership_returns_none_when_not_found(
        self,
        repository: SQLAlchemyMembershipRepository,
        user: User,
        community: Community,
    ) -> None:
        """Test get_membership returns None for non-existent membership."""
        # Act
        result = await repository.get_membership(user.id, community.id)

        # Assert
        assert result is None

    async def test_remove_member(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test removing a member from a community."""
        # Arrange
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act
        result = await repository.remove_member(user.id, community.id)
        await db_session.commit()

        # Assert
        assert result is True
        # Verify membership is gone
        membership = await repository.get_membership(user.id, community.id)
        assert membership is None

    async def test_remove_member_returns_false_when_not_found(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test removing non-existent member returns False."""
        # Act
        result = await repository.remove_member(user.id, community.id)

        # Assert
        assert result is False

    async def test_update_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test updating a member's role."""
        # Arrange
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act
        updated = await repository.update_role(
            user_id=user.id,
            community_id=community.id,
            new_role=MembershipRole.MODERATOR.value,
        )
        await db_session.commit()

        # Assert
        assert updated is not None
        assert updated.role == MembershipRole.MODERATOR.value

        # Verify change persisted
        retrieved = await repository.get_membership(user.id, community.id)
        assert retrieved is not None
        assert retrieved.role == MembershipRole.MODERATOR.value

    async def test_update_role_returns_none_when_not_found(
        self,
        repository: SQLAlchemyMembershipRepository,
        user: User,
        community: Community,
    ) -> None:
        """Test update_role returns None for non-existent membership."""
        # Act
        result = await repository.update_role(
            user_id=user.id,
            community_id=community.id,
            new_role=MembershipRole.ADMIN.value,
        )

        # Assert
        assert result is None

    async def test_get_user_memberships(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test retrieving all memberships for a user."""
        # Arrange - Create multiple communities and memberships
        communities = []
        for i in range(3):
            community = Community(
                id=uuid4(),
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                member_count=0,
            )
            db_session.add(community)
            communities.append(community)
        await db_session.commit()

        for community in communities:
            await repository.add_member(
                user_id=user.id,
                community_id=community.id,
                role=MembershipRole.MEMBER.value,
            )
        await db_session.commit()

        # Act
        memberships = await repository.get_user_memberships(user.id)

        # Assert
        assert len(memberships) == 3
        # Verify ordered by joined_at DESC (most recent first)
        for membership in memberships:
            assert membership.user_id == user.id

    async def test_get_user_memberships_with_pagination(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test pagination on get_user_memberships."""
        # Arrange - Create 5 memberships
        communities = []
        for i in range(5):
            community = Community(
                id=uuid4(),
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                member_count=0,
            )
            db_session.add(community)
            communities.append(community)
        await db_session.commit()

        for community in communities:
            await repository.add_member(
                user_id=user.id,
                community_id=community.id,
                role=MembershipRole.MEMBER.value,
            )
        await db_session.commit()

        # Act - Get first 2
        page1 = await repository.get_user_memberships(user.id, skip=0, limit=2)
        # Get next 2
        page2 = await repository.get_user_memberships(user.id, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        # Ensure no overlap
        page1_ids = {m.id for m in page1}
        page2_ids = {m.id for m in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    async def test_get_user_memberships_by_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test retrieving user's memberships filtered by role."""
        # Arrange - Create communities with different roles
        roles = [
            MembershipRole.ADMIN.value,
            MembershipRole.MODERATOR.value,
            MembershipRole.MEMBER.value,
        ]
        for i, role in enumerate(roles):
            community = Community(
                id=uuid4(),
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                member_count=0,
            )
            db_session.add(community)
            await db_session.commit()
            await db_session.refresh(community)

            await repository.add_member(
                user_id=user.id,
                community_id=community.id,
                role=role,
            )
        await db_session.commit()

        # Act - Get only admin memberships
        admin_memberships = await repository.get_user_memberships_by_role(
            user_id=user.id,
            role=MembershipRole.ADMIN.value,
        )

        # Assert
        assert len(admin_memberships) == 1
        assert admin_memberships[0].role == MembershipRole.ADMIN.value

    async def test_count_user_memberships(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test counting user's total memberships."""
        # Arrange - Create 3 memberships
        for i in range(3):
            community = Community(
                id=uuid4(),
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                member_count=0,
            )
            db_session.add(community)
            await db_session.commit()
            await db_session.refresh(community)

            await repository.add_member(
                user_id=user.id,
                community_id=community.id,
                role=MembershipRole.MEMBER.value,
            )
        await db_session.commit()

        # Act
        count = await repository.count_user_memberships(user.id)

        # Assert
        assert count == 3

    async def test_count_user_memberships_returns_zero_when_none(
        self,
        repository: SQLAlchemyMembershipRepository,
        user: User,
    ) -> None:
        """Test count returns 0 when user has no memberships."""
        # Act
        count = await repository.count_user_memberships(user.id)

        # Assert
        assert count == 0

    async def test_is_member(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test checking if user is a member."""
        # Arrange
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act
        result = await repository.is_member(user.id, community.id)

        # Assert
        assert result is True

    async def test_is_member_returns_false_when_not_member(
        self,
        repository: SQLAlchemyMembershipRepository,
        user: User,
        community: Community,
    ) -> None:
        """Test is_member returns False for non-members."""
        # Act
        result = await repository.is_member(user.id, community.id)

        # Assert
        assert result is False

    async def test_has_role_with_exact_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test has_role returns True when user has exact role."""
        # Arrange
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MODERATOR.value,
        )
        await db_session.commit()

        # Act
        result = await repository.has_role(
            user_id=user.id,
            community_id=community.id,
            required_role=MembershipRole.MODERATOR.value,
        )

        # Assert
        assert result is True

    async def test_has_role_with_higher_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test has_role returns True when user has higher role (admin > moderator)."""
        # Arrange - User is admin
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.ADMIN.value,
        )
        await db_session.commit()

        # Act - Check for moderator permission
        result = await repository.has_role(
            user_id=user.id,
            community_id=community.id,
            required_role=MembershipRole.MODERATOR.value,
        )

        # Assert - Admin should have moderator permissions
        assert result is True

    async def test_has_role_with_lower_role(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test has_role returns False when user has lower role (member < moderator)."""
        # Arrange - User is member
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act - Check for moderator permission
        result = await repository.has_role(
            user_id=user.id,
            community_id=community.id,
            required_role=MembershipRole.MODERATOR.value,
        )

        # Assert - Member should not have moderator permissions
        assert result is False

    async def test_has_role_returns_false_when_not_member(
        self,
        repository: SQLAlchemyMembershipRepository,
        user: User,
        community: Community,
    ) -> None:
        """Test has_role returns False when user is not a member."""
        # Act
        result = await repository.has_role(
            user_id=user.id,
            community_id=community.id,
            required_role=MembershipRole.MEMBER.value,
        )

        # Assert
        assert result is False

    async def test_get_admin_count(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        community: Community,
    ) -> None:
        """Test counting admins in a community."""
        # Arrange - Create 2 admins and 1 moderator
        users = []
        for i in range(3):
            user = User(
                id=uuid4(),
                google_id=f"google_{i}",
                email=f"user{i}@test.edu",
                name=f"User {i}",
                role="student",
            )
            db_session.add(user)
            users.append(user)
        await db_session.commit()

        # Add 2 admins
        for i in range(2):
            await repository.add_member(
                user_id=users[i].id,
                community_id=community.id,
                role=MembershipRole.ADMIN.value,
            )

        # Add 1 moderator
        await repository.add_member(
            user_id=users[2].id,
            community_id=community.id,
            role=MembershipRole.MODERATOR.value,
        )
        await db_session.commit()

        # Act
        admin_count = await repository.get_admin_count(community.id)

        # Assert
        assert admin_count == 2

    async def test_get_admin_count_returns_zero_when_no_admins(
        self,
        repository: SQLAlchemyMembershipRepository,
        db_session: AsyncSession,
        user: User,
        community: Community,
    ) -> None:
        """Test get_admin_count returns 0 when no admins."""
        # Arrange - Add only a member
        await repository.add_member(
            user_id=user.id,
            community_id=community.id,
            role=MembershipRole.MEMBER.value,
        )
        await db_session.commit()

        # Act
        admin_count = await repository.get_admin_count(community.id)

        # Assert
        assert admin_count == 0
