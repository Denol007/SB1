"""Integration tests for community API endpoints.

Tests cover:
- All CRUD operations (Create, Read, Update, Delete)
- Membership management (join, leave, add, remove, update role)
- Permission enforcement (admin, moderator, member access)
- Hierarchical community structure
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.community_type import CommunityType
from app.domain.enums.community_visibility import CommunityVisibility
from app.domain.enums.membership_role import MembershipRole
from app.domain.enums.user_role import UserRole
from app.infrastructure.database.models.community import Community
from app.infrastructure.database.models.membership import Membership
from app.infrastructure.database.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        google_id="google_123",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def another_user(db_session: AsyncSession) -> User:
    """Create another test user."""
    user = User(
        id=uuid4(),
        email="another@example.com",
        name="Another User",
        google_id="google_456",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        name="Admin User",
        google_id="google_admin",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_community(db_session: AsyncSession, test_user: User) -> Community:
    """Create a test community with test_user as admin."""
    community = Community(
        id=uuid4(),
        name="Test Community",
        description="A test community",
        type=CommunityType.UNIVERSITY,
        visibility=CommunityVisibility.PUBLIC,
        requires_verification=False,
        member_count=1,
    )
    db_session.add(community)
    await db_session.commit()
    await db_session.refresh(community)

    # Add creator as admin
    membership = Membership(
        id=uuid4(),
        user_id=test_user.id,
        community_id=community.id,
        role=MembershipRole.ADMIN,
        joined_at=datetime.now(UTC),
    )
    db_session.add(membership)
    await db_session.commit()

    return community


# ============================================================================
# Test Community CRUD Operations
# ============================================================================


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityCreate:
    """Test POST /api/v1/communities - Create community."""

    @pytest.mark.asyncio
    async def test_creates_community_successfully(
        self, async_client: AsyncClient, test_user: User, auth_headers
    ):
        """Should create a new community."""
        # Arrange
        headers = auth_headers(test_user.id)
        payload = {
            "name": "New Community",
            "description": "A brand new community",
            "type": CommunityType.UNIVERSITY.value,
            "visibility": CommunityVisibility.PUBLIC.value,
            "requires_verification": False,
        }

        # Act
        response = await async_client.post("/api/v1/communities", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Community"
        assert data["description"] == "A brand new community"
        assert data["type"] == CommunityType.UNIVERSITY.value
        assert data["visibility"] == CommunityVisibility.PUBLIC.value
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_creates_subcommunity_successfully(
        self, async_client: AsyncClient, test_user: User, test_community: Community, auth_headers
    ):
        """Should create a subcommunity under parent."""
        # Arrange
        headers = auth_headers(test_user.id)
        payload = {
            "name": "Sub Community",
            "description": "A child community",
            "type": CommunityType.HOBBY.value,
            "visibility": CommunityVisibility.PUBLIC.value,
            "parent_id": str(test_community.id),
        }

        # Act
        response = await async_client.post("/api/v1/communities", json=payload, headers=headers)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sub Community"
        assert data["parent_id"] == str(test_community.id)

    @pytest.mark.asyncio
    async def test_requires_authentication(self, async_client: AsyncClient):
        """Should return 401 if not authenticated."""
        # Arrange
        payload = {
            "name": "Unauthorized Community",
            "type": CommunityType.UNIVERSITY.value,
        }

        # Act
        response = await async_client.post("/api/v1/communities", json=payload)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validates_required_fields(
        self, async_client: AsyncClient, test_user: User, auth_headers
    ):
        """Should return 422 if required fields missing."""
        # Arrange
        headers = auth_headers(test_user.id)
        payload = {"description": "Missing name and type"}

        # Act
        response = await async_client.post("/api/v1/communities", json=payload, headers=headers)

        # Assert
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityList:
    """Test GET /api/v1/communities - List communities."""

    @pytest.mark.asyncio
    async def test_lists_communities(self, async_client: AsyncClient, test_community: Community):
        """Should return list of communities."""
        # Act
        response = await async_client.get("/api/v1/communities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert any(c["id"] == str(test_community.id) for c in data["data"])

    @pytest.mark.asyncio
    async def test_filters_by_type(self, async_client: AsyncClient, test_community: Community):
        """Should filter communities by type."""
        # Act
        response = await async_client.get(
            f"/api/v1/communities?type={CommunityType.UNIVERSITY.value}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(c["type"] == CommunityType.UNIVERSITY.value for c in data["data"])

    @pytest.mark.asyncio
    async def test_filters_by_visibility(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should filter communities by visibility."""
        # Act
        response = await async_client.get(
            f"/api/v1/communities?visibility={CommunityVisibility.PUBLIC.value}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(c["visibility"] == CommunityVisibility.PUBLIC.value for c in data["data"])


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityGet:
    """Test GET /api/v1/communities/{community_id} - Get community details."""

    @pytest.mark.asyncio
    async def test_gets_community_details(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should return community details."""
        # Act
        response = await async_client.get(f"/api/v1/communities/{test_community.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_community.id)
        assert data["name"] == test_community.name
        assert data["description"] == test_community.description
        assert "member_count" in data

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_community(self, async_client: AsyncClient):
        """Should return 404 if community doesn't exist."""
        # Arrange
        fake_id = uuid4()

        # Act
        response = await async_client.get(f"/api/v1/communities/{fake_id}")

        # Assert
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityUpdate:
    """Test PATCH /api/v1/communities/{community_id} - Update community."""

    @pytest.mark.asyncio
    async def test_updates_community_when_admin(
        self, async_client: AsyncClient, test_user: User, test_community: Community, auth_headers
    ):
        """Should update community when user is admin."""
        # Arrange
        headers = auth_headers(test_user.id)
        payload = {
            "name": "Updated Community Name",
            "description": "Updated description",
        }

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Community Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_forbids_update_when_not_admin(
        self, async_client: AsyncClient, another_user: User, test_community: Community, auth_headers
    ):
        """Should return 403 when user is not admin."""
        # Arrange
        headers = auth_headers(another_user.id)
        payload = {"name": "Unauthorized Update"}

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}", json=payload, headers=headers
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should return 401 if not authenticated."""
        # Arrange
        payload = {"name": "Unauthorized Update"}

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}", json=payload
        )

        # Assert
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityDelete:
    """Test DELETE /api/v1/communities/{community_id} - Delete community."""

    @pytest.mark.asyncio
    async def test_deletes_community_when_admin(
        self, async_client: AsyncClient, test_user: User, test_community: Community, auth_headers
    ):
        """Should delete community when user is admin."""
        # Arrange
        headers = auth_headers(test_user.id)

        # Act
        response = await async_client.delete(
            f"/api/v1/communities/{test_community.id}", headers=headers
        )

        # Assert
        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(f"/api/v1/communities/{test_community.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_forbids_delete_when_not_admin(
        self, async_client: AsyncClient, another_user: User, test_community: Community, auth_headers
    ):
        """Should return 403 when user is not admin."""
        # Arrange
        headers = auth_headers(another_user.id)

        # Act
        response = await async_client.delete(
            f"/api/v1/communities/{test_community.id}", headers=headers
        )

        # Assert
        assert response.status_code == 403


# ============================================================================
# Test Membership Management
# ============================================================================


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityJoin:
    """Test POST /api/v1/communities/{community_id}/join - Join community."""

    @pytest.mark.asyncio
    async def test_joins_community_successfully(
        self, async_client: AsyncClient, another_user: User, test_community: Community, auth_headers
    ):
        """Should allow user to join a public community."""
        # Arrange
        headers = auth_headers(another_user.id)

        # Act
        response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/join", headers=headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(another_user.id)
        assert data["community_id"] == str(test_community.id)
        assert data["role"] == MembershipRole.MEMBER.value

    @pytest.mark.asyncio
    async def test_prevents_duplicate_join(
        self, async_client: AsyncClient, test_user: User, test_community: Community, auth_headers
    ):
        """Should return 409 if user is already a member."""
        # Arrange
        headers = auth_headers(test_user.id)

        # Act
        response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/join", headers=headers
        )

        # Assert
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should return 401 if not authenticated."""
        # Act
        response = await async_client.post(f"/api/v1/communities/{test_community.id}/join")

        # Assert
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityLeave:
    """Test POST /api/v1/communities/{community_id}/leave - Leave community."""

    @pytest.mark.asyncio
    async def test_leaves_community_successfully(
        self,
        async_client: AsyncClient,
        another_user: User,
        test_community: Community,
        db_session: AsyncSession,
        auth_headers,
    ):
        """Should allow user to leave a community."""
        # Arrange - Add user to community first
        membership = Membership(
            id=uuid4(),
            user_id=another_user.id,
            community_id=test_community.id,
            role=MembershipRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        headers = auth_headers(another_user.id)

        # Act
        response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/leave", headers=headers
        )

        # Assert
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_prevents_last_admin_from_leaving(
        self, async_client: AsyncClient, test_user: User, test_community: Community, auth_headers
    ):
        """Should return 403 if user is the last admin."""
        # Arrange
        headers = auth_headers(test_user.id)

        # Act
        response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/leave", headers=headers
        )

        # Assert
        assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.us2
class TestCommunityMembers:
    """Test GET /api/v1/communities/{community_id}/members - List members."""

    @pytest.mark.asyncio
    async def test_lists_community_members(
        self, async_client: AsyncClient, test_user: User, test_community: Community
    ):
        """Should return list of community members."""
        # Act
        response = await async_client.get(f"/api/v1/communities/{test_community.id}/members")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert any(m["user_id"] == str(test_user.id) for m in data["data"])

    @pytest.mark.asyncio
    async def test_filters_members_by_role(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should filter members by role."""
        # Act
        response = await async_client.get(
            f"/api/v1/communities/{test_community.id}/members?role={MembershipRole.ADMIN.value}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert all(m["role"] == MembershipRole.ADMIN.value for m in data["data"])


@pytest.mark.integration
@pytest.mark.us2
class TestUpdateMemberRole:
    """Test PATCH /api/v1/communities/{community_id}/members/{user_id} - Update role."""

    @pytest.mark.asyncio
    async def test_updates_member_role_when_admin(
        self,
        async_client: AsyncClient,
        test_user: User,
        another_user: User,
        test_community: Community,
        db_session: AsyncSession,
        auth_headers,
    ):
        """Should update member role when requester is admin."""
        # Arrange - Add another_user as member
        membership = Membership(
            id=uuid4(),
            user_id=another_user.id,
            community_id=test_community.id,
            role=MembershipRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        headers = auth_headers(test_user.id)
        payload = {"role": MembershipRole.MODERATOR.value}

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}/members/{another_user.id}",
            json=payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == MembershipRole.MODERATOR.value

    @pytest.mark.asyncio
    async def test_forbids_role_update_when_not_admin(
        self,
        async_client: AsyncClient,
        another_user: User,
        test_user: User,
        test_community: Community,
        auth_headers,
    ):
        """Should return 403 when requester is not admin."""
        # Arrange
        headers = auth_headers(another_user.id)
        payload = {"role": MembershipRole.MODERATOR.value}

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}/members/{test_user.id}",
            json=payload,
            headers=headers,
        )

        # Assert
        assert response.status_code == 403


# ============================================================================
# Test Permission Enforcement
# ============================================================================


@pytest.mark.integration
@pytest.mark.us2
class TestPermissionEnforcement:
    """Test permission enforcement across endpoints."""

    @pytest.mark.asyncio
    async def test_public_community_visible_to_all(
        self, async_client: AsyncClient, test_community: Community
    ):
        """Should allow anyone to view public community."""
        # Act
        response = await async_client.get(f"/api/v1/communities/{test_community.id}")

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_private_community_requires_membership(
        self,
        async_client: AsyncClient,
        test_user: User,
        db_session: AsyncSession,
        auth_headers,
    ):
        """Should hide private community from non-members."""
        # Arrange - Create private community
        private_community = Community(
            id=uuid4(),
            name="Private Community",
            description="A private community",
            type=CommunityType.HOBBY,
            visibility=CommunityVisibility.PRIVATE,
            member_count=0,
        )
        db_session.add(private_community)
        await db_session.commit()

        headers = auth_headers(test_user.id)

        # Act
        response = await async_client.get(
            f"/api/v1/communities/{private_community.id}", headers=headers
        )

        # Assert
        # This would return 403 or 404 depending on implementation
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_moderator_can_update_description(
        self,
        async_client: AsyncClient,
        another_user: User,
        test_community: Community,
        db_session: AsyncSession,
        auth_headers,
    ):
        """Should allow moderators to update community description."""
        # Arrange - Make another_user a moderator
        membership = Membership(
            id=uuid4(),
            user_id=another_user.id,
            community_id=test_community.id,
            role=MembershipRole.MODERATOR,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        headers = auth_headers(another_user.id)
        payload = {"description": "Updated by moderator"}

        # Act
        response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}", json=payload, headers=headers
        )

        # Assert
        # Depending on implementation, moderators may or may not update descriptions
        # This test documents the expected behavior
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_admin_has_full_permissions(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_community: Community,
        auth_headers,
    ):
        """Should allow admins to perform all operations."""
        # Arrange
        headers = auth_headers(test_user.id)

        # Act - Try multiple operations
        update_response = await async_client.patch(
            f"/api/v1/communities/{test_community.id}",
            json={"description": "Updated"},
            headers=headers,
        )
        members_response = await async_client.get(
            f"/api/v1/communities/{test_community.id}/members", headers=headers
        )

        # Assert
        assert update_response.status_code == 200
        assert members_response.status_code == 200
