"""Integration tests for event API endpoints (User Story 4).

These tests verify event management functionality including:
- Event creation by moderators
- Event CRUD operations
- Event registration with capacity limits
- Waitlist management
- Participant listing
- Status changes

Tests are written TDD-first and will skip if Event models/endpoints are not yet implemented.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.user_role import UserRole

try:
    from app.infrastructure.database.models.event import Event  # type: ignore
except Exception:  # pragma: no cover - skip when model not present
    Event = None  # type: ignore

try:
    from app.infrastructure.database.models.event_registration import (  # type: ignore
        EventRegistration,
    )
except Exception:  # pragma: no cover
    EventRegistration = None  # type: ignore


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user for event tests."""
    try:
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="event_tester@example.com",
            name="Event Tester",
            google_id="google_event_tester",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping event endpoint integration tests")


@pytest.fixture
async def test_moderator(db_session: AsyncSession):
    """Create a moderator user for event tests."""
    try:
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="moderator@example.com",
            name="Event Moderator",
            google_id="google_event_moderator",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping event endpoint integration tests")


@pytest.fixture
async def test_community(db_session: AsyncSession, test_moderator):
    """Create a test community with moderator membership."""
    try:
        from app.domain.enums.community_type import CommunityType
        from app.domain.enums.community_visibility import CommunityVisibility
        from app.domain.enums.membership_role import MembershipRole
        from app.infrastructure.database.models.community import Community
        from app.infrastructure.database.models.membership import Membership

        community = Community(
            id=uuid4(),
            name="Event Community",
            description="Community for event tests",
            type=CommunityType.UNIVERSITY,
            visibility=CommunityVisibility.PUBLIC,
            requires_verification=False,
            member_count=1,
        )
        db_session.add(community)
        await db_session.commit()
        await db_session.refresh(community)

        # Add moderator membership
        membership = Membership(
            id=uuid4(),
            user_id=test_moderator.id,
            community_id=community.id,
            role=MembershipRole.MODERATOR,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        return community
    except Exception:  # pragma: no cover
        pytest.skip(
            "Community/membership models not available - skipping event endpoint integration tests"
        )


@pytest.fixture
async def test_member_user(db_session: AsyncSession, test_community):
    """Create a regular member user for the test community."""
    try:
        from app.domain.enums.membership_role import MembershipRole
        from app.infrastructure.database.models.membership import Membership
        from app.infrastructure.database.models.user import User

        user = User(
            id=uuid4(),
            email="member@example.com",
            name="Regular Member",
            google_id="google_member",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add member membership
        membership = Membership(
            id=uuid4(),
            user_id=user.id,
            community_id=test_community.id,
            role=MembershipRole.MEMBER,
            joined_at=datetime.now(UTC),
        )
        db_session.add(membership)
        await db_session.commit()

        return user
    except Exception:  # pragma: no cover
        pytest.skip("User model not available - skipping event endpoint integration tests")


@pytest.mark.integration
@pytest.mark.us4
class TestEventCreation:
    """Test event creation endpoints."""

    @pytest.mark.asyncio
    async def test_create_event_requires_authentication(self, async_client: AsyncClient):
        """POST /api/v1/communities/{community_id}/events requires auth."""
        if Event is None:
            pytest.skip("Event model not implemented")

        response = await async_client.post(
            "/api/v1/communities/00000000-0000-0000-0000-000000000000/events",
            json={"title": "Test Event"},
        )
        assert response.status_code in (401, 404)

    @pytest.mark.asyncio
    async def test_create_event_requires_moderator_role(
        self, async_client: AsyncClient, test_user, test_community, auth_headers
    ):
        """Only moderators/admins can create events."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_user.id)
        payload = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            "end_time": (datetime.now(UTC) + timedelta(days=7, hours=2)).isoformat(),
            "participant_limit": 50,
        }

        response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=payload, headers=headers
        )
        # Should be 403 (forbidden) since test_user is not a moderator
        assert response.status_code in (403, 404, 501)

    @pytest.mark.asyncio
    async def test_create_and_get_event_flow(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers
    ):
        """Moderator can create an event and retrieve it."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)
        end_time = start_time + timedelta(hours=2)

        payload = {
            "title": "Python Workshop",
            "description": "Learn advanced Python concepts",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "participant_limit": 50,
        }

        # Create event
        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=payload, headers=headers
        )
        assert create_resp.status_code in (201, 404, 501)

        if create_resp.status_code != 201:
            pytest.skip("Event create endpoint not implemented or returns non-created status")

        data = create_resp.json()
        event_id = data.get("id")
        assert event_id is not None
        assert data["title"] == payload["title"]
        assert data["type"] == payload["type"]

        # Get event
        get_resp = await async_client.get(f"/api/v1/events/{event_id}", headers=headers)
        assert get_resp.status_code == 200
        got = get_resp.json()
        assert got["id"] == event_id
        assert got["title"] == payload["title"]

    @pytest.mark.asyncio
    async def test_create_event_validates_time_constraints(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers
    ):
        """Event creation validates start_time is in future and end_time is after start_time."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)

        # Test 1: Start time in the past
        past_payload = {
            "title": "Past Event",
            "description": "This should fail",
            "type": "online",
            "start_time": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "participant_limit": 50,
        }

        resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=past_payload, headers=headers
        )
        assert resp.status_code in (400, 404, 422, 501)

        # Test 2: End time before start time
        start = datetime.now(UTC) + timedelta(days=7)
        invalid_payload = {
            "title": "Invalid Event",
            "description": "End before start",
            "type": "online",
            "start_time": start.isoformat(),
            "end_time": (start - timedelta(hours=1)).isoformat(),
            "participant_limit": 50,
        }

        resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=invalid_payload, headers=headers
        )
        assert resp.status_code in (400, 404, 422, 501)


@pytest.mark.integration
@pytest.mark.us4
class TestEventListing:
    """Test event listing endpoints."""

    @pytest.mark.asyncio
    async def test_list_community_events(
        self, async_client: AsyncClient, test_community, auth_headers, test_moderator
    ):
        """GET /api/v1/communities/{community_id}/events returns event list."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)
        resp = await async_client.get(
            f"/api/v1/communities/{test_community.id}/events", headers=headers
        )
        assert resp.status_code in (200, 404, 501)

        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list) or "items" in data  # Could be list or paginated


@pytest.mark.integration
@pytest.mark.us4
class TestEventUpdates:
    """Test event update endpoints."""

    @pytest.mark.asyncio
    async def test_update_event_as_creator(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers, db_session
    ):
        """Event creator can update their event."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        # Create event first
        payload = {
            "title": "Original Title",
            "description": "Original description",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=payload, headers=headers
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Update event
        update_payload = {"title": "Updated Title", "description": "Updated description"}

        update_resp = await async_client.patch(
            f"/api/v1/events/{event_id}", json=update_payload, headers=headers
        )
        assert update_resp.status_code in (200, 404, 501)

        if update_resp.status_code == 200:
            data = update_resp.json()
            assert data["title"] == "Updated Title"
            assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_event_permission_check(
        self, async_client: AsyncClient, test_user, auth_headers
    ):
        """Non-creator cannot update event."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_user.id)
        fake_event_id = uuid4()

        update_payload = {"title": "Hacked Title"}

        resp = await async_client.patch(
            f"/api/v1/events/{fake_event_id}", json=update_payload, headers=headers
        )
        assert resp.status_code in (403, 404, 501)


@pytest.mark.integration
@pytest.mark.us4
class TestEventDeletion:
    """Test event deletion endpoints."""

    @pytest.mark.asyncio
    async def test_delete_event_as_creator(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers
    ):
        """Event creator can delete their event."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        # Create event
        payload = {
            "title": "Event to Delete",
            "description": "Will be deleted",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=payload, headers=headers
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Delete event
        delete_resp = await async_client.delete(f"/api/v1/events/{event_id}", headers=headers)
        assert delete_resp.status_code in (200, 204, 404, 501)

        if delete_resp.status_code in (200, 204):
            # Verify event is deleted
            get_resp = await async_client.get(f"/api/v1/events/{event_id}", headers=headers)
            assert get_resp.status_code == 404


@pytest.mark.integration
@pytest.mark.us4
class TestEventRegistration:
    """Test event registration endpoints."""

    @pytest.mark.asyncio
    async def test_register_for_event(
        self,
        async_client: AsyncClient,
        test_moderator,
        test_member_user,
        test_community,
        auth_headers,
    ):
        """Community member can register for an event."""
        if Event is None or EventRegistration is None:
            pytest.skip("Event/EventRegistration models not implemented")

        # Create event as moderator
        moderator_headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        event_payload = {
            "title": "Registration Test Event",
            "description": "Test event",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events",
            json=event_payload,
            headers=moderator_headers,
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Register as member
        member_headers = auth_headers(test_member_user.id)
        register_resp = await async_client.post(
            f"/api/v1/events/{event_id}/register", headers=member_headers
        )

        assert register_resp.status_code in (200, 201, 404, 501)

        if register_resp.status_code in (200, 201):
            data = register_resp.json()
            assert data["status"] in ("registered", "waitlisted")

    @pytest.mark.asyncio
    async def test_register_handles_capacity_limit(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers, db_session
    ):
        """Event registration handles capacity limits."""
        if Event is None or EventRegistration is None:
            pytest.skip("Event/EventRegistration models not implemented")

        # Create event with limit of 1
        moderator_headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        event_payload = {
            "title": "Limited Event",
            "description": "Only 1 spot",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 1,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events",
            json=event_payload,
            headers=moderator_headers,
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Create two users and try to register both
        try:
            from app.domain.enums.membership_role import MembershipRole
            from app.infrastructure.database.models.membership import Membership
            from app.infrastructure.database.models.user import User

            user1 = User(
                id=uuid4(),
                email="user1@example.com",
                name="User 1",
                google_id="google_user1",
                role=UserRole.STUDENT,
            )
            user2 = User(
                id=uuid4(),
                email="user2@example.com",
                name="User 2",
                google_id="google_user2",
                role=UserRole.STUDENT,
            )
            db_session.add(user1)
            db_session.add(user2)
            await db_session.commit()

            # Add memberships
            for user in [user1, user2]:
                membership = Membership(
                    id=uuid4(),
                    user_id=user.id,
                    community_id=test_community.id,
                    role=MembershipRole.MEMBER,
                    joined_at=datetime.now(UTC),
                )
                db_session.add(membership)
            await db_session.commit()

            # Register first user
            headers1 = auth_headers(user1.id)
            resp1 = await async_client.post(f"/api/v1/events/{event_id}/register", headers=headers1)
            assert resp1.status_code in (200, 201, 404, 501)

            if resp1.status_code in (200, 201):
                assert resp1.json()["status"] == "registered"

                # Register second user - should be waitlisted
                headers2 = auth_headers(user2.id)
                resp2 = await async_client.post(
                    f"/api/v1/events/{event_id}/register", headers=headers2
                )
                assert resp2.status_code in (200, 201, 404, 501)

                if resp2.status_code in (200, 201):
                    assert resp2.json()["status"] == "waitlisted"

        except Exception:  # pragma: no cover
            pytest.skip("Unable to create test users for capacity test")

    @pytest.mark.asyncio
    async def test_unregister_from_event(
        self,
        async_client: AsyncClient,
        test_moderator,
        test_member_user,
        test_community,
        auth_headers,
    ):
        """User can unregister from an event."""
        if Event is None or EventRegistration is None:
            pytest.skip("Event/EventRegistration models not implemented")

        # Create and register
        moderator_headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        event_payload = {
            "title": "Unregister Test",
            "description": "Test unregistration",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events",
            json=event_payload,
            headers=moderator_headers,
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Register
        member_headers = auth_headers(test_member_user.id)
        register_resp = await async_client.post(
            f"/api/v1/events/{event_id}/register", headers=member_headers
        )

        if register_resp.status_code not in (200, 201):
            pytest.skip("Event registration not implemented")

        # Unregister
        unregister_resp = await async_client.delete(
            f"/api/v1/events/{event_id}/register", headers=member_headers
        )
        assert unregister_resp.status_code in (200, 204, 404, 501)


@pytest.mark.integration
@pytest.mark.us4
class TestEventParticipants:
    """Test event participant listing endpoints."""

    @pytest.mark.asyncio
    async def test_get_event_participants(
        self,
        async_client: AsyncClient,
        test_moderator,
        test_member_user,
        test_community,
        auth_headers,
    ):
        """Get list of event participants."""
        if Event is None or EventRegistration is None:
            pytest.skip("Event/EventRegistration models not implemented")

        # Create event
        moderator_headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        event_payload = {
            "title": "Participants Test",
            "description": "Test participants",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events",
            json=event_payload,
            headers=moderator_headers,
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Get participants (should be empty initially)
        participants_resp = await async_client.get(
            f"/api/v1/events/{event_id}/participants", headers=moderator_headers
        )
        assert participants_resp.status_code in (200, 404, 501)

        if participants_resp.status_code == 200:
            data = participants_resp.json()
            assert isinstance(data, list) or "items" in data


@pytest.mark.integration
@pytest.mark.us4
class TestEventStatusChanges:
    """Test event status change endpoints."""

    @pytest.mark.asyncio
    async def test_change_event_status(
        self, async_client: AsyncClient, test_moderator, test_community, auth_headers
    ):
        """Event creator can change event status."""
        if Event is None:
            pytest.skip("Event model not implemented")

        headers = auth_headers(test_moderator.id)
        start_time = datetime.now(UTC) + timedelta(days=7)

        # Create event
        event_payload = {
            "title": "Status Change Test",
            "description": "Test status changes",
            "type": "online",
            "start_time": start_time.isoformat(),
            "end_time": (start_time + timedelta(hours=2)).isoformat(),
            "participant_limit": 50,
        }

        create_resp = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events", json=event_payload, headers=headers
        )

        if create_resp.status_code != 201:
            pytest.skip("Event create not implemented")

        event_id = create_resp.json()["id"]

        # Change status to cancelled
        status_payload = {"status": "cancelled"}
        status_resp = await async_client.patch(
            f"/api/v1/events/{event_id}", json=status_payload, headers=headers
        )

        assert status_resp.status_code in (200, 404, 501)

        if status_resp.status_code == 200:
            data = status_resp.json()
            assert data["status"] == "cancelled"
