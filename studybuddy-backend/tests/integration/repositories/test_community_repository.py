"""Integration tests for CommunityRepository.

These tests verify the CommunityRepository implementation against a real database,
ensuring all CRUD operations work correctly with PostgreSQL.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from app.infrastructure.database.models.membership import Membership
from app.infrastructure.database.models.user import User
from app.infrastructure.repositories.community_repository import (
    SQLAlchemyCommunityRepository,
)


@pytest.mark.asyncio
class TestCommunityRepository:
    """Test suite for CommunityRepository implementation."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession):
        """Create a CommunityRepository instance with database session.

        Args:
            db_session: Database session fixture.

        Returns:
            SQLAlchemyCommunityRepository: Repository instance for testing.
        """
        return SQLAlchemyCommunityRepository(db_session)

    async def test_create_community(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test creating a new community."""
        # Act
        community = await repository.create(
            name="Stanford Computer Science",
            description="CS community at Stanford",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Assert
        assert community.id is not None
        assert community.name == "Stanford Computer Science"
        assert community.description == "CS community at Stanford"
        assert community.type == CommunityType.UNIVERSITY
        assert community.visibility == CommunityVisibility.PUBLIC
        assert community.parent_id is None
        assert community.requires_verification is False
        assert community.avatar_url is None
        assert community.cover_url is None
        assert community.member_count == 0
        assert community.created_at is not None
        assert community.updated_at is not None
        assert community.deleted_at is None

    async def test_create_community_with_parent(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test creating a sub-community with a parent."""
        # Arrange
        parent = await repository.create(
            name="Stanford University",
            description="Main Stanford community",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        child = await repository.create(
            name="Stanford CS Department",
            description="Computer Science Department",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=parent.id,
        )
        await db_session.commit()

        # Assert
        assert child.parent_id == parent.id
        assert child.id != parent.id

    async def test_create_community_with_invalid_parent_raises_error(
        self, repository: SQLAlchemyCommunityRepository
    ):
        """Test creating community with non-existent parent raises ValueError."""
        # Arrange
        invalid_parent_id = uuid4()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await repository.create(
                name="Invalid Community",
                description="Should fail",
                type=CommunityType.UNIVERSITY,
                visibility=CommunityVisibility.PUBLIC,
                parent_id=invalid_parent_id,
            )

        assert "not found" in str(exc_info.value).lower()

    async def test_create_community_with_all_optional_fields(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test creating community with all optional fields."""
        # Act
        community = await repository.create(
            name="Business Club",
            description="Entrepreneurship community",
            type=CommunityType.BUSINESS,
            visibility=CommunityVisibility.PRIVATE,
            requires_verification=True,
            avatar_url="https://example.com/avatar.jpg",
            cover_url="https://example.com/cover.jpg",
        )
        await db_session.commit()

        # Assert
        assert community.requires_verification is True
        assert community.avatar_url == "https://example.com/avatar.jpg"
        assert community.cover_url == "https://example.com/cover.jpg"

    async def test_get_by_id(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test retrieving community by ID."""
        # Arrange
        created = await repository.create(
            name="Test Community",
            description="Test description",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        retrieved = await repository.get_by_id(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Community"

    async def test_get_by_id_nonexistent_returns_none(
        self, repository: SQLAlchemyCommunityRepository
    ):
        """Test retrieving non-existent community returns None."""
        # Arrange
        nonexistent_id = uuid4()

        # Act
        result = await repository.get_by_id(nonexistent_id)

        # Assert
        assert result is None

    async def test_get_by_id_excludes_soft_deleted(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test that get_by_id excludes soft-deleted communities."""
        # Arrange
        community = await repository.create(
            name="To Delete",
            description="Will be deleted",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()
        community_id = community.id

        await repository.delete(community_id)
        await db_session.commit()

        # Act
        result = await repository.get_by_id(community_id)

        # Assert
        assert result is None

    async def test_get_by_id_including_deleted(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test retrieving soft-deleted community with including_deleted method."""
        # Arrange
        community = await repository.create(
            name="Deleted Community",
            description="Will be deleted",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()
        community_id = community.id

        await repository.delete(community_id)
        await db_session.commit()

        # Act
        result = await repository.get_by_id_including_deleted(community_id)

        # Assert
        assert result is not None
        assert result.id == community_id
        assert result.deleted_at is not None

    async def test_list_by_type(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test listing communities by type."""
        # Arrange
        await repository.create(
            name="University 1",
            description="First university",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await repository.create(
            name="University 2",
            description="Second university",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await repository.create(
            name="Business 1",
            description="First business",
            type=CommunityType.BUSINESS,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        universities = await repository.list_by_type(CommunityType.UNIVERSITY)
        businesses = await repository.list_by_type(CommunityType.BUSINESS)

        # Assert
        assert len(universities) == 2
        assert len(businesses) == 1
        assert all(c.type == CommunityType.UNIVERSITY for c in universities)

    async def test_list_by_type_with_pagination(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test pagination when listing by type."""
        # Arrange
        for i in range(5):
            await repository.create(
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.HOBBY,
                visibility=CommunityVisibility.PUBLIC,
            )
        await db_session.commit()

        # Act
        page1 = await repository.list_by_type(CommunityType.HOBBY, skip=0, limit=2)
        page2 = await repository.list_by_type(CommunityType.HOBBY, skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id  # Different communities

    async def test_list_by_visibility(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test listing communities by visibility."""
        # Arrange
        await repository.create(
            name="Public Community",
            description="Public",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await repository.create(
            name="Private Community",
            description="Private",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PRIVATE,
        )
        await db_session.commit()

        # Act
        public = await repository.list_by_visibility(CommunityVisibility.PUBLIC)
        private = await repository.list_by_visibility(CommunityVisibility.PRIVATE)

        # Assert
        assert len(public) == 1
        assert len(private) == 1
        assert public[0].visibility == CommunityVisibility.PUBLIC

    async def test_list_all(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test listing all communities."""
        # Arrange
        for i in range(3):
            await repository.create(
                name=f"Community {i}",
                description=f"Description {i}",
                type=CommunityType.HOBBY,
                visibility=CommunityVisibility.PUBLIC,
            )
        await db_session.commit()

        # Act
        all_communities = await repository.list_all()

        # Assert
        assert len(all_communities) >= 3  # May include others from previous tests

    async def test_list_all_with_pagination(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test pagination when listing all communities."""
        # Arrange
        for i in range(5):
            await repository.create(
                name=f"Test Community {i}",
                description=f"Description {i}",
                type=CommunityType.HOBBY,
                visibility=CommunityVisibility.PUBLIC,
            )
        await db_session.commit()

        # Act
        page1 = await repository.list_all(skip=0, limit=3)
        page2 = await repository.list_all(skip=3, limit=3)

        # Assert
        assert len(page1) == 3
        assert len(page2) >= 2

    async def test_get_children(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test retrieving child communities."""
        # Arrange
        parent = await repository.create(
            name="Parent Community",
            description="Parent",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        child1 = await repository.create(
            name="Child 1",
            description="First child",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=parent.id,
        )
        child2 = await repository.create(
            name="Child 2",
            description="Second child",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=parent.id,
        )
        await db_session.commit()

        # Act
        children = await repository.get_children(parent.id)

        # Assert
        assert len(children) == 2
        assert all(c.parent_id == parent.id for c in children)
        child_ids = {c.id for c in children}
        assert child1.id in child_ids
        assert child2.id in child_ids

    async def test_get_children_excludes_deleted(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test that get_children excludes soft-deleted children."""
        # Arrange
        parent = await repository.create(
            name="Parent",
            description="Parent",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        child = await repository.create(
            name="Child",
            description="Will be deleted",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            parent_id=parent.id,
        )
        await db_session.commit()

        await repository.delete(child.id)
        await db_session.commit()

        # Act
        children = await repository.get_children(parent.id)

        # Assert
        assert len(children) == 0

    async def test_update_community(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test updating community fields."""
        # Arrange
        community = await repository.create(
            name="Original Name",
            description="Original description",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        updated = await repository.update(
            community.id,
            name="Updated Name",
            description="Updated description",
            visibility=CommunityVisibility.PRIVATE,
        )
        await db_session.commit()

        # Assert
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.visibility == CommunityVisibility.PRIVATE
        assert updated.updated_at > community.created_at

    async def test_update_community_partial_fields(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test updating only some fields."""
        # Arrange
        community = await repository.create(
            name="Original",
            description="Original desc",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        updated = await repository.update(community.id, name="New Name")
        await db_session.commit()

        # Assert
        assert updated.name == "New Name"
        assert updated.description == "Original desc"  # Unchanged

    async def test_update_nonexistent_community_returns_none(
        self, repository: SQLAlchemyCommunityRepository
    ):
        """Test updating non-existent community returns None."""
        # Arrange
        nonexistent_id = uuid4()

        # Act
        result = await repository.update(nonexistent_id, name="New Name")

        # Assert
        assert result is None

    async def test_update_invalid_field_raises_error(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test updating invalid field raises ValueError."""
        # Arrange
        community = await repository.create(
            name="Test",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await repository.update(community.id, id=uuid4())  # ID shouldn't be updatable

        assert "cannot be updated" in str(exc_info.value).lower()

    async def test_delete_community(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test soft deleting a community."""
        # Arrange
        community = await repository.create(
            name="To Delete",
            description="Will be deleted",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Act
        success = await repository.delete(community.id)
        await db_session.commit()

        # Assert
        assert success is True
        deleted = await repository.get_by_id_including_deleted(community.id)
        assert deleted.deleted_at is not None

    async def test_delete_nonexistent_community_returns_false(
        self, repository: SQLAlchemyCommunityRepository
    ):
        """Test deleting non-existent community returns False."""
        # Arrange
        nonexistent_id = uuid4()

        # Act
        success = await repository.delete(nonexistent_id)

        # Assert
        assert success is False

    async def test_get_members(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test retrieving community members."""
        # Arrange
        community = await repository.create(
            name="Test Community",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Create users and memberships
        user1 = User(
            google_id="google_test1",
            email="user1@test.edu",
            name="User One",
            role="student",
        )
        user2 = User(
            google_id="google_test2",
            email="user2@test.edu",
            name="User Two",
            role="student",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        membership1 = Membership(
            user_id=user1.id, community_id=community.id, role=MembershipRole.ADMIN
        )
        membership2 = Membership(
            user_id=user2.id, community_id=community.id, role=MembershipRole.MEMBER
        )
        db_session.add(membership1)
        db_session.add(membership2)
        await db_session.commit()

        # Act
        members = await repository.get_members(community.id)

        # Assert
        assert len(members) == 2
        member_user_ids = {m.user_id for m in members}
        assert user1.id in member_user_ids
        assert user2.id in member_user_ids

    async def test_get_members_by_role(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test retrieving community members by role."""
        # Arrange
        community = await repository.create(
            name="Test Community",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Create users and memberships
        admin = User(
            google_id="google_admin",
            email="admin@test.edu",
            name="Admin User",
            role="student",
        )
        member = User(
            google_id="google_member",
            email="member@test.edu",
            name="Member User",
            role="student",
        )
        db_session.add(admin)
        db_session.add(member)
        await db_session.flush()

        admin_membership = Membership(
            user_id=admin.id, community_id=community.id, role=MembershipRole.ADMIN
        )
        member_membership = Membership(
            user_id=member.id, community_id=community.id, role=MembershipRole.MEMBER
        )
        db_session.add(admin_membership)
        db_session.add(member_membership)
        await db_session.commit()

        # Act
        admins = await repository.get_members_by_role(community.id, MembershipRole.ADMIN)
        members = await repository.get_members_by_role(community.id, MembershipRole.MEMBER)

        # Assert
        assert len(admins) == 1
        assert len(members) == 1
        assert admins[0].role == MembershipRole.ADMIN
        assert members[0].role == MembershipRole.MEMBER

    async def test_count_members(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test counting community members."""
        # Arrange
        community = await repository.create(
            name="Test Community",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()

        # Create users and memberships
        for i in range(3):
            user = User(
                google_id=f"google_count{i}",
                email=f"count{i}@test.edu",
                name=f"Count User {i}",
                role="student",
            )
            db_session.add(user)
            await db_session.flush()
            membership = Membership(
                user_id=user.id, community_id=community.id, role=MembershipRole.MEMBER
            )
            db_session.add(membership)
        await db_session.commit()

        # Act
        count = await repository.count_members(community.id)

        # Assert
        assert count == 3

    async def test_update_member_count(
        self, repository: SQLAlchemyCommunityRepository, db_session: AsyncSession
    ):
        """Test updating denormalized member count."""
        # Arrange
        community = await repository.create(
            name="Test Community",
            description="Test",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PUBLIC,
        )
        await db_session.commit()
        assert community.member_count == 0

        # Act
        updated = await repository.update_member_count(community.id, 42)
        await db_session.commit()

        # Assert
        assert updated is not None
        assert updated.member_count == 42

    async def test_update_member_count_nonexistent_returns_none(
        self, repository: SQLAlchemyCommunityRepository
    ):
        """Test updating member count for non-existent community returns None."""
        # Arrange
        nonexistent_id = uuid4()

        # Act
        result = await repository.update_member_count(nonexistent_id, 10)

        # Assert
        assert result is None
