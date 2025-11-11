"""Real-world integration test for Event API endpoints.

This test demonstrates a complete real-world scenario:
Computer Science Club organizing an Advanced Python Workshop
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def test_moderator(db_session: AsyncSession):
    """Create a moderator user for event tests."""
    from app.domain.enums.user_role import UserRole
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


@pytest.fixture
async def test_community(db_session: AsyncSession, test_moderator):
    """Create a test community with moderator membership."""
    from app.domain.enums.community_type import CommunityType
    from app.domain.enums.community_visibility import CommunityVisibility
    from app.domain.enums.membership_role import MembershipRole
    from app.infrastructure.database.models.community import Community
    from app.infrastructure.database.models.membership import Membership

    community = Community(
        id=uuid4(),
        name="Computer Science Club",
        description="A community for CS students",
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


@pytest.fixture
async def test_alice(db_session: AsyncSession, test_community):
    """Create Alice, a test student."""
    from app.domain.enums.membership_role import MembershipRole
    from app.domain.enums.user_role import UserRole
    from app.infrastructure.database.models.membership import Membership
    from app.infrastructure.database.models.user import User

    user = User(
        id=uuid4(),
        email="alice@example.com",
        name="Alice Johnson",
        google_id="google_alice",
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


@pytest.fixture
async def test_bob(db_session: AsyncSession, test_community):
    """Create Bob, a test student."""
    from app.domain.enums.membership_role import MembershipRole
    from app.domain.enums.user_role import UserRole
    from app.infrastructure.database.models.membership import Membership
    from app.infrastructure.database.models.user import User

    user = User(
        id=uuid4(),
        email="bob@example.com",
        name="Bob Williams",
        google_id="google_bob",
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


@pytest.fixture
async def test_charlie(db_session: AsyncSession, test_community):
    """Create Charlie, a test student."""
    from app.domain.enums.membership_role import MembershipRole
    from app.domain.enums.user_role import UserRole
    from app.infrastructure.database.models.membership import Membership
    from app.infrastructure.database.models.user import User

    user = User(
        id=uuid4(),
        email="charlie@example.com",
        name="Charlie Brown",
        google_id="google_charlie",
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


@pytest.mark.integration
@pytest.mark.asyncio
class TestEventRealWorldScenario:
    """Complete real-world event management scenario."""

    async def test_complete_event_lifecycle(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_moderator,
        test_community,
        test_alice,
        test_bob,
        test_charlie,
    ):
        """
        Real-world scenario: Computer Science Club organizes an Advanced Python Workshop

        This test demonstrates:
        1. Creating an event with capacity limits
        2. Students registering for the event
        3. Waitlist management when capacity is full
        4. Auto-promotion from waitlist when someone unregisters
        5. Viewing participants
        6. Updating event details
        7. Listing community events
        8. Deleting an event
        """

        # Get auth header for the moderator (who will create the event)
        moderator_headers = auth_headers(test_moderator.id)

        # ============================================================
        # STEP 1: Create an Advanced Python Workshop Event
        # ============================================================
        print("\n=== Creating Advanced Python Workshop Event ===")
        event_start = datetime.now(UTC) + timedelta(days=7)
        event_end = event_start + timedelta(hours=3)

        create_response = await async_client.post(
            f"/api/v1/communities/{test_community.id}/events",
            json={
                "title": "Advanced Python Workshop: Async & Decorators",
                "description": "Deep dive into Python async/await patterns and decorator best practices. Hands-on coding session with real-world examples.",
                "type": "offline",  # In-person workshop
                "start_time": event_start.isoformat(),
                "end_time": event_end.isoformat(),
                "location": "Computer Lab 301",
                "participant_limit": 2,  # Limited capacity to test waitlist
                "tags": ["python", "async", "advanced", "workshop"],
            },
            headers=moderator_headers,
        )

        print(f"Create event response status: {create_response.status_code}")
        print(f"Create event response: {create_response.json()}")
        assert create_response.status_code == 201

        event = create_response.json()
        event_id = event["id"]
        assert event["title"] == "Advanced Python Workshop: Async & Decorators"
        assert event["participant_limit"] == 2
        assert event["registered_count"] == 0
        print(f"✓ Event created successfully: {event['title']}")

        # ============================================================
        # STEP 2: Get auth headers for our three students
        # ============================================================
        print("\n=== Setting up student auth headers ===")
        alice_headers = auth_headers(test_alice.id)
        bob_headers = auth_headers(test_bob.id)
        charlie_headers = auth_headers(test_charlie.id)
        print(
            f"✓ Created auth headers for {test_alice.name}, {test_bob.name}, and {test_charlie.name}"
        )

        # ============================================================
        # STEP 3: Alice registers for the event (1/2 capacity)
        # ============================================================
        print("\n=== Alice Registers for Workshop ===")
        alice_register = await async_client.post(
            f"/api/v1/events/{event_id}/register", headers=alice_headers
        )

        print(f"Alice registration status: {alice_register.status_code}")
        if alice_register.status_code != 201:
            print(f"Alice registration error: {alice_register.json()}")

        assert alice_register.status_code == 201
        alice_registration = alice_register.json()
        assert alice_registration["status"] == "registered"
        print("✓ Alice successfully registered (1/2 spots filled)")

        # ============================================================
        # STEP 4: Bob registers for the event (2/2 capacity FULL)
        # ============================================================
        print("\n=== Bob Registers for Workshop ===")
        bob_register = await async_client.post(
            f"/api/v1/events/{event_id}/register", headers=bob_headers
        )

        print(f"Bob registration status: {bob_register.status_code}")
        assert bob_register.status_code == 201
        bob_registration = bob_register.json()
        assert bob_registration["status"] == "registered"
        print("✓ Bob successfully registered (2/2 spots filled - EVENT FULL)")

        # ============================================================
        # STEP 5: Charlie registers but gets waitlisted
        # ============================================================
        print("\n=== Charlie Registers for Full Event ===")
        charlie_register = await async_client.post(
            f"/api/v1/events/{event_id}/register", headers=charlie_headers
        )

        print(f"Charlie registration status: {charlie_register.status_code}")
        assert charlie_register.status_code == 201
        charlie_registration = charlie_register.json()
        assert charlie_registration["status"] == "waitlisted"
        print("✓ Charlie waitlisted (event at capacity)")

        # ============================================================
        # STEP 6: View all participants (as moderator)
        # ============================================================
        print("\n=== Viewing All Participants ===")
        participants_response = await async_client.get(
            f"/api/v1/events/{event_id}/participants", headers=moderator_headers
        )

        assert participants_response.status_code == 200
        participants = participants_response.json()

        # Should have 2 registered + 1 waitlisted
        registered = [p for p in participants if p["status"] == "registered"]
        waitlisted = [p for p in participants if p["status"] == "waitlisted"]

        assert len(registered) == 2
        assert len(waitlisted) == 1
        print(f"✓ Participants: {len(registered)} registered, {len(waitlisted)} waitlisted")

        # ============================================================
        # STEP 7: Alice unregisters - Charlie should be auto-promoted
        # ============================================================
        print("\n=== Alice Unregisters from Workshop ===")
        alice_unregister = await async_client.delete(
            f"/api/v1/events/{event_id}/register", headers=alice_headers
        )

        assert alice_unregister.status_code == 204
        print("✓ Alice unregistered successfully")

        # Check that Charlie was auto-promoted
        print("\n=== Verifying Charlie's Auto-Promotion ===")
        participants_after = await async_client.get(
            f"/api/v1/events/{event_id}/participants", headers=moderator_headers
        )

        assert participants_after.status_code == 200
        updated_participants = participants_after.json()

        registered_after = [p for p in updated_participants if p["status"] == "registered"]
        waitlisted_after = [p for p in updated_participants if p["status"] == "waitlisted"]

        assert len(registered_after) == 2  # Bob + Charlie
        assert len(waitlisted_after) == 0
        print("✓ Charlie auto-promoted to registered (2/2 spots filled)")

        # ============================================================
        # STEP 8: Update event details (increase capacity)
        # ============================================================
        print("\n=== Updating Event Details ===")
        update_response = await async_client.patch(
            f"/api/v1/events/{event_id}",
            json={
                "participant_limit": 5,  # Increase capacity
                "description": "Deep dive into Python async/await patterns and decorator best practices. NOW WITH MORE SEATS! Hands-on coding session.",
            },
            headers=moderator_headers,
        )

        assert update_response.status_code == 200
        updated_event = update_response.json()
        assert updated_event["participant_limit"] == 5
        assert "NOW WITH MORE SEATS!" in updated_event["description"]
        print("✓ Event updated: capacity increased to 5")

        # ============================================================
        # STEP 9: List all community events
        # ============================================================
        print("\n=== Listing All Community Events ===")
        list_response = await async_client.get(
            f"/api/v1/communities/{test_community.id}/events?page=1&per_page=10",
            headers=moderator_headers,
        )

        assert list_response.status_code == 200
        events_data = list_response.json()
        assert "data" in events_data
        assert len(events_data["data"]) >= 1

        # Find our workshop
        workshop = next((e for e in events_data["data"] if e["id"] == event_id), None)
        assert workshop is not None
        print(f"✓ Found workshop in community events: '{workshop['title']}'")

        # ============================================================
        # STEP 10: Get event details
        # ============================================================
        print("\n=== Getting Event Details ===")
        detail_response = await async_client.get(
            f"/api/v1/events/{event_id}", headers=moderator_headers
        )

        assert detail_response.status_code == 200
        event_details = detail_response.json()
        assert event_details["title"] == "Advanced Python Workshop: Async & Decorators"
        assert event_details["registered_count"] == 2  # Bob + Charlie
        print(
            f"✓ Event details retrieved: {event_details['registered_count']}/{event_details['participant_limit']} registered"
        )

        # ============================================================
        # STEP 11: Delete the event (cleanup)
        # ============================================================
        print("\n=== Deleting Event ===")
        delete_response = await async_client.delete(
            f"/api/v1/events/{event_id}", headers=moderator_headers
        )

        assert delete_response.status_code == 204
        print("✓ Event deleted successfully")

        # Verify it's gone
        verify_deleted = await async_client.get(
            f"/api/v1/events/{event_id}", headers=moderator_headers
        )
        assert verify_deleted.status_code == 404
        print("✓ Verified event no longer exists")

        print("\n" + "=" * 60)
        print("✓✓✓ COMPLETE LIFECYCLE TEST PASSED ✓✓✓")
        print("=" * 60)
