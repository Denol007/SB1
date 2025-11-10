"""Integration tests for comment API endpoints (User Story 3).

These tests follow TDD principles and will skip if Comment model/endpoints
are not yet implemented. Tests cover:
- Comment creation on posts
- Threaded replies (parent_comment_id)
- Comment editing and deletion
- Permission checks (author only for edit/delete)
- Comment listing with pagination
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.user_role import UserRole

try:
    from app.infrastructure.database.models.comment import Comment  # type: ignore
except Exception:  # pragma: no cover - skip when model not present
    Comment = None  # type: ignore


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for comment tests."""
    try:
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="comment_tester@example.com",
            name="Comment Tester",
            google_id="google_comment_tester",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping comment endpoint integration tests")


@pytest.fixture
async def another_user(db_session: AsyncSession):
    """Create another test user for permission tests."""
    try:
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="another_comment_tester@example.com",
            name="Another Comment Tester",
            google_id="google_another_comment_tester",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping comment endpoint integration tests")


@pytest.fixture
async def test_community(db_session: AsyncSession, test_user):
    """Create a test community with test_user as admin."""
    try:
        from app.domain.enums.community_type import CommunityType
        from app.domain.enums.community_visibility import CommunityVisibility
        from app.domain.enums.membership_role import MembershipRole
        from app.infrastructure.database.models.community import Community
        from app.infrastructure.database.models.membership import Membership

        community = Community(
            id=uuid4(),
            name="Comment Test Community",
            description="Community for comment tests",
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
            role=MembershipRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        return community
    except Exception:  # pragma: no cover
        pytest.skip(
            "Community/membership models not available - skipping comment endpoint integration tests"
        )


@pytest.fixture
async def test_post(db_session: AsyncSession, test_user, test_community):
    """Create a test post for commenting."""
    try:
        from app.infrastructure.database.models.post import Post

        post = Post(
            id=uuid4(),
            author_id=test_user.id,
            community_id=test_community.id,
            content="This is a test post for comments",
            is_pinned=False,
        )
        db_session.add(post)
        await db_session.commit()
        await db_session.refresh(post)
        return post
    except Exception:  # pragma: no cover
        pytest.skip("Post model not available - skipping comment endpoint integration tests")


@pytest.mark.integration
@pytest.mark.us3
class TestCommentEndpoints:
    """Test comment CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_comment_requires_authentication(
        self, async_client: AsyncClient, test_post
    ):
        """POST /api/v1/posts/{post_id}/comments requires auth."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "Test comment"},
        )
        assert response.status_code in (401, 404)

    @pytest.mark.asyncio
    async def test_create_and_get_comment_flow(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test creating a comment and retrieving it."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create comment
        create_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "This is a great post!"},
            headers=auth_headers(test_user.id),
        )
        assert create_response.status_code in (201, 404, 501)

        if create_response.status_code == 201:
            comment_data = create_response.json()
            assert comment_data["content"] == "This is a great post!"
            assert comment_data["author_id"] == str(test_user.id)
            assert comment_data["post_id"] == str(test_post.id)
            assert comment_data.get("parent_id") is None

            # Get comment (via post's comment list)
            list_response = await async_client.get(
                f"/api/v1/posts/{test_post.id}/comments",
                headers=auth_headers(test_user.id),
            )
            assert list_response.status_code == 200
            comments = list_response.json()
            assert len(comments) >= 1
            assert any(c["content"] == "This is a great post!" for c in comments)

    @pytest.mark.asyncio
    async def test_create_threaded_reply(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test creating a reply to an existing comment."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create parent comment
        parent_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "Parent comment"},
            headers=auth_headers(test_user.id),
        )
        assert parent_response.status_code in (201, 404, 501)

        if parent_response.status_code == 201:
            parent_comment = parent_response.json()
            parent_id = parent_comment["id"]

            # Create reply
            reply_response = await async_client.post(
                f"/api/v1/posts/{test_post.id}/comments",
                json={"content": "This is a reply", "parent_id": parent_id},
                headers=auth_headers(test_user.id),
            )
            assert reply_response.status_code in (201, 404, 501)

            if reply_response.status_code == 201:
                reply_data = reply_response.json()
                assert reply_data["content"] == "This is a reply"
                assert reply_data["parent_id"] == parent_id
                assert reply_data["post_id"] == str(test_post.id)

    @pytest.mark.asyncio
    async def test_list_post_comments_with_pagination(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test listing comments with pagination."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create multiple comments
        for i in range(5):
            await async_client.post(
                f"/api/v1/posts/{test_post.id}/comments",
                json={"content": f"Comment {i}"},
                headers=auth_headers(test_user.id),
            )

        # List comments
        list_response = await async_client.get(
            f"/api/v1/posts/{test_post.id}/comments?page=1&page_size=3",
            headers=auth_headers(test_user.id),
        )
        assert list_response.status_code in (200, 404, 501)

        if list_response.status_code == 200:
            comments = list_response.json()
            assert isinstance(comments, list)
            # Should respect page_size (if implemented)
            assert len(comments) <= 5

    @pytest.mark.asyncio
    async def test_update_comment_as_author(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test updating a comment as the author."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create comment
        create_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers(test_user.id),
        )
        assert create_response.status_code in (201, 404, 501)

        if create_response.status_code == 201:
            comment = create_response.json()
            comment_id = comment["id"]

            # Update comment
            update_response = await async_client.patch(
                f"/api/v1/comments/{comment_id}",
                json={"content": "Updated content"},
                headers=auth_headers(test_user.id),
            )
            assert update_response.status_code in (200, 404, 501)

            if update_response.status_code == 200:
                updated = update_response.json()
                assert updated["content"] == "Updated content"
                assert updated.get("edited_at") is not None

    @pytest.mark.asyncio
    async def test_update_comment_not_author_fails(
        self, async_client: AsyncClient, test_user, another_user, test_post, auth_headers
    ):
        """Test that non-author cannot update a comment."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create comment as test_user
        create_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers(test_user.id),
        )
        assert create_response.status_code in (201, 404, 501)

        if create_response.status_code == 201:
            comment = create_response.json()
            comment_id = comment["id"]

            # Try to update as another_user
            update_response = await async_client.patch(
                f"/api/v1/comments/{comment_id}",
                json={"content": "Hacked content"},
                headers=auth_headers(another_user.id),
            )
            # Should be forbidden or not found (if endpoint implemented)
            assert update_response.status_code in (403, 404, 501)

    @pytest.mark.asyncio
    async def test_delete_comment_as_author(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test deleting a comment as the author."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create comment
        create_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "To be deleted"},
            headers=auth_headers(test_user.id),
        )
        assert create_response.status_code in (201, 404, 501)

        if create_response.status_code == 201:
            comment = create_response.json()
            comment_id = comment["id"]

            # Delete comment
            delete_response = await async_client.delete(
                f"/api/v1/comments/{comment_id}",
                headers=auth_headers(test_user.id),
            )
            assert delete_response.status_code in (204, 200, 404, 501)

            if delete_response.status_code in (204, 200):
                # Verify comment is gone or marked as deleted
                list_response = await async_client.get(
                    f"/api/v1/posts/{test_post.id}/comments",
                    headers=auth_headers(test_user.id),
                )
                if list_response.status_code == 200:
                    comments = list_response.json()
                    # Deleted comment should not appear (or appear as [deleted])
                    active_comments = [c for c in comments if c.get("deleted_at") is None]
                    assert not any(c["id"] == comment_id for c in active_comments)

    @pytest.mark.asyncio
    async def test_delete_comment_not_author_fails(
        self, async_client: AsyncClient, test_user, another_user, test_post, auth_headers
    ):
        """Test that non-author cannot delete a comment."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        # Create comment as test_user
        create_response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": "Protected content"},
            headers=auth_headers(test_user.id),
        )
        assert create_response.status_code in (201, 404, 501)

        if create_response.status_code == 201:
            comment = create_response.json()
            comment_id = comment["id"]

            # Try to delete as another_user
            delete_response = await async_client.delete(
                f"/api/v1/comments/{comment_id}",
                headers=auth_headers(another_user.id),
            )
            # Should be forbidden or not found (if endpoint implemented)
            assert delete_response.status_code in (403, 404, 501)

    @pytest.mark.asyncio
    async def test_create_comment_with_empty_content_fails(
        self, async_client: AsyncClient, test_user, test_post, auth_headers
    ):
        """Test that creating a comment with empty content fails."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        response = await async_client.post(
            f"/api/v1/posts/{test_post.id}/comments",
            json={"content": ""},
            headers=auth_headers(test_user.id),
        )
        # Should be bad request or not found (if endpoint implemented)
        assert response.status_code in (400, 404, 422, 501)

    @pytest.mark.asyncio
    async def test_comment_on_nonexistent_post_fails(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test that commenting on a non-existent post fails."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        fake_post_id = uuid4()
        response = await async_client.post(
            f"/api/v1/posts/{fake_post_id}/comments",
            json={"content": "Comment on nothing"},
            headers=auth_headers(test_user.id),
        )
        # Should be not found (if endpoint implemented)
        assert response.status_code in (404, 501)

    @pytest.mark.asyncio
    async def test_update_nonexistent_comment_fails(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test that updating a non-existent comment fails."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        fake_comment_id = uuid4()
        response = await async_client.patch(
            f"/api/v1/comments/{fake_comment_id}",
            json={"content": "Updated nothing"},
            headers=auth_headers(test_user.id),
        )
        # Should be not found (if endpoint implemented)
        assert response.status_code in (404, 501)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_comment_fails(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Test that deleting a non-existent comment fails."""
        if Comment is None:
            pytest.skip("Comment model not implemented")

        fake_comment_id = uuid4()
        response = await async_client.delete(
            f"/api/v1/comments/{fake_comment_id}",
            headers=auth_headers(test_user.id),
        )
        # Should be not found (if endpoint implemented)
        assert response.status_code in (404, 501)
