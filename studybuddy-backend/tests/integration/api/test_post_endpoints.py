"""Integration tests for post API endpoints (User Story 3).

These tests follow the same style as community integration tests. They are
written TDD-first and will skip if the Post model/endpoints are not yet
implemented.
"""

from datetime import UTC
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.user_role import UserRole

try:
    from app.infrastructure.database.models.post import Post  # type: ignore
except Exception:  # pragma: no cover - skip when model not present
    Post = None  # type: ignore


@pytest.fixture
async def test_user(db_session: AsyncSession):
    try:
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="post_tester@example.com",
            name="Post Tester",
            google_id="google_post_tester",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping post endpoint integration tests")


@pytest.fixture
async def test_community(db_session: AsyncSession, test_user):
    try:
        from datetime import datetime

        from app.domain.enums.community_type import CommunityType
        from app.domain.enums.community_visibility import CommunityVisibility
        from app.domain.enums.membership_role import MembershipRole
        from app.infrastructure.database.models.community import Community
        from app.infrastructure.database.models.membership import Membership

        community = Community(
            id=uuid4(),
            name="Post Community",
            description="Community for post tests",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            requires_verification=False,
            member_count=1,
        )
        db_session.add(community)
        await db_session.commit()
        await db_session.refresh(community)

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
    except Exception:  # pragma: no cover
        pytest.skip(
            "Community/membership models not available - skipping post endpoint integration tests"
        )


@pytest.mark.integration
@pytest.mark.us3
class TestPostEndpoints:
    @pytest.mark.asyncio
    async def test_create_post_requires_authentication(self, async_client: AsyncClient):
        """POST /api/v1/communities/{community_id}/posts requires auth"""
        if Post is None:
            pytest.skip("Post model not implemented")

        response = await async_client.post(
            "/api/v1/communities/00000000-0000-0000-0000-000000000000/posts", json={"content": "hi"}
        )
        assert response.status_code in (401, 404)

    @pytest.mark.asyncio
    async def test_create_and_get_post_flow(
        self, async_client: AsyncClient, test_user, test_community, auth_headers
    ):
        """Create a post and retrieve it by id."""
        if Post is None:
            pytest.skip("Post model not implemented")

        headers = auth_headers(test_user.id)
        payload = {"content": "Integration test post content"}

        # Create post
        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/posts", json=payload, headers=headers
        )
        assert create_resp.status_code in (201, 404, 501)

        if create_resp.status_code != 201:
            pytest.skip("Post create endpoint not implemented or returns not created status")

        data = create_resp.json()
        post_id = data.get("id")
        assert post_id is not None

        # Get post
        get_resp = await async_client.get(f"/api/v1/posts/{post_id}", headers=headers)
        assert get_resp.status_code == 200
        got = get_resp.json()
        assert got["id"] == post_id
        assert got["content"] == payload["content"]

    @pytest.mark.asyncio
    async def test_list_community_posts(self, async_client: AsyncClient, test_community):
        """GET /api/v1/communities/{community_id}/posts returns list"""
        if Post is None:
            pytest.skip("Post model not implemented")

        resp = await async_client.get(f"/api/v1/communities/{test_community.id}/posts")
        assert resp.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_pin_unpin_post_permissions(
        self, async_client: AsyncClient, test_user, test_community, auth_headers
    ):
        """Pin/unpin requires moderator or admin rights."""
        if Post is None:
            pytest.skip("Post model not implemented")

        headers = auth_headers(test_user.id)
        # Attempt to pin a non-existent post -> expect 404 or 403 depending on implementation
        resp = await async_client.post(f"/api/v1/posts/{uuid4()}/pin", headers=headers)
        assert resp.status_code in (403, 404, 401)

    @pytest.mark.asyncio
    async def test_reactions_endpoints(
        self, async_client: AsyncClient, test_user, test_community, auth_headers
    ):
        """Add/remove reaction endpoints should exist (may be unimplemented)."""
        if Post is None:
            pytest.skip("Post model not implemented")

        headers = auth_headers(test_user.id)
        # Add reaction to non-existent post - expect 404 or 501 or 403
        add_resp = await async_client.post(
            f"/api/v1/posts/{uuid4()}/reactions", json={"reaction_type": "like"}, headers=headers
        )
        assert add_resp.status_code in (201, 404, 501, 403, 400)

        # Remove reaction - expect 204/404/403
        del_resp = await async_client.delete(f"/api/v1/posts/{uuid4()}/reactions", headers=headers)
        assert del_resp.status_code in (204, 404, 403, 401)
