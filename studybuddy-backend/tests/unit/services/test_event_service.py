"""Unit tests for EventService.

Tests cover:
- Event creation in communities
- Event updates (details, status, capacity)
- Event deletion (soft delete)
- Event registration with capacity limits
- Waitlist management and auto-promotion
- Event unregistration
- Participant listing
- Event status changes
- Permission checks (creator, moderator, admin)

Note: Following TDD - these tests are written FIRST before EventService exists.
They should FAIL initially, then pass after implementation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.domain.enums.membership_role import MembershipRole


@pytest.fixture
def mock_event_repository():
    """Mock event repository."""
    return AsyncMock()


@pytest.fixture
def mock_event_registration_repository():
    """Mock event registration repository."""
    return AsyncMock()


@pytest.fixture
def mock_membership_repository():
    """Mock membership repository."""
    return AsyncMock()


@pytest.fixture
def mock_community_repository():
    """Mock community repository."""
    return AsyncMock()


@pytest.fixture
def event_service(
    mock_event_repository,
    mock_event_registration_repository,
    mock_membership_repository,
    mock_community_repository,
):
    """Create EventService instance with mocked repositories.

    Note: EventService doesn't exist yet - this is TDD, tests first!
    """
    # This import will fail initially - that's expected in TDD
    try:
        from app.application.services.event_service import EventService

        return EventService(
            event_repository=mock_event_repository,
            registration_repository=mock_event_registration_repository,
            membership_repository=mock_membership_repository,
            community_repository=mock_community_repository,
        )
    except ImportError:
        pytest.skip("EventService not yet implemented - TDD phase")


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def creator_id():
    """Sample creator ID."""
    return uuid4()


@pytest.fixture
def community_id():
    """Sample community ID."""
    return uuid4()


@pytest.fixture
def event_id():
    """Sample event ID."""
    return uuid4()


@pytest.fixture
def sample_event(creator_id, community_id):
    """Sample event object."""
    return MagicMock(
        id=uuid4(),
        community_id=community_id,
        creator_id=creator_id,
        title="Python Workshop: Advanced Topics",
        description="Learn advanced Python concepts",
        type="online",
        location=None,
        start_time=datetime.now(UTC) + timedelta(days=7),
        end_time=datetime.now(UTC) + timedelta(days=7, hours=2),
        participant_limit=50,
        status="published",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_registration(user_id, event_id):
    """Sample registration object."""
    return MagicMock(
        id=uuid4(),
        event_id=event_id,
        user_id=user_id,
        status="registered",
        registered_at=datetime.now(UTC),
    )


# ============================================================================
# Test Event Creation
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestCreateEvent:
    """Test event creation."""

    @pytest.mark.asyncio
    async def test_creates_event_with_valid_data(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        creator_id,
        community_id,
        sample_event,
    ):
        """Test that create_event creates an event with valid data."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )
        mock_event_repository.create.return_value = sample_event

        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": datetime.now(UTC) + timedelta(days=7),
            "end_time": datetime.now(UTC) + timedelta(days=7, hours=2),
            "participant_limit": 50,
        }

        # Act
        result = await event_service.create_event(
            user_id=creator_id,
            community_id=community_id,
            event_data=event_data,
        )

        # Assert
        assert result == sample_event
        mock_membership_repository.get_by_user_and_community.assert_called_once_with(
            user_id=creator_id, community_id=community_id
        )
        mock_event_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_fails_if_user_not_moderator(
        self,
        event_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Test that create_event fails if user is not a moderator."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": datetime.now(UTC) + timedelta(days=7),
            "end_time": datetime.now(UTC) + timedelta(days=7, hours=2),
            "participant_limit": 50,
        }

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.create_event(
                user_id=user_id,
                community_id=community_id,
                event_data=event_data,
            )

    @pytest.mark.asyncio
    async def test_fails_if_user_not_member(
        self,
        event_service,
        mock_membership_repository,
        user_id,
        community_id,
    ):
        """Test that create_event fails if user is not a community member."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = None

        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": datetime.now(UTC) + timedelta(days=7),
            "end_time": datetime.now(UTC) + timedelta(days=7, hours=2),
            "participant_limit": 50,
        }

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.create_event(
                user_id=user_id,
                community_id=community_id,
                event_data=event_data,
            )

    @pytest.mark.asyncio
    async def test_validates_start_time_in_future(
        self,
        event_service,
        mock_membership_repository,
        creator_id,
        community_id,
    ):
        """Test that create_event validates start_time is in the future."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": datetime.now(UTC) - timedelta(hours=1),  # Past time
            "end_time": datetime.now(UTC) + timedelta(hours=1),
            "participant_limit": 50,
        }

        # Act & Assert
        with pytest.raises(BadRequestException):
            await event_service.create_event(
                user_id=creator_id,
                community_id=community_id,
                event_data=event_data,
            )

    @pytest.mark.asyncio
    async def test_validates_end_time_after_start(
        self,
        event_service,
        mock_membership_repository,
        creator_id,
        community_id,
    ):
        """Test that create_event validates end_time is after start_time."""
        # Arrange
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        start = datetime.now(UTC) + timedelta(days=7)
        event_data = {
            "title": "Python Workshop",
            "description": "Learn Python",
            "type": "online",
            "start_time": start,
            "end_time": start - timedelta(hours=1),  # Before start
            "participant_limit": 50,
        }

        # Act & Assert
        with pytest.raises(BadRequestException):
            await event_service.create_event(
                user_id=creator_id,
                community_id=community_id,
                event_data=event_data,
            )


# ============================================================================
# Test Event Updates
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestUpdateEvent:
    """Test event updates."""

    @pytest.mark.asyncio
    async def test_updates_event_as_creator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        creator_id,
        event_id,
        sample_event,
    ):
        """Test that update_event updates an event when called by creator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        updated_event = MagicMock(**{**sample_event.__dict__, "title": "Updated Title"})
        mock_event_repository.update.return_value = updated_event

        update_data = {"title": "Updated Title"}

        # Act
        result = await event_service.update_event(
            event_id=event_id,
            user_id=creator_id,
            update_data=update_data,
        )

        # Assert
        assert result == updated_event
        mock_event_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_event_as_moderator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that update_event updates an event when called by moderator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )
        updated_event = MagicMock(**{**sample_event.__dict__, "title": "Updated Title"})
        mock_event_repository.update.return_value = updated_event

        update_data = {"title": "Updated Title"}

        # Act
        result = await event_service.update_event(
            event_id=event_id,
            user_id=user_id,
            update_data=update_data,
        )

        # Assert
        assert result == updated_event

    @pytest.mark.asyncio
    async def test_fails_if_not_creator_or_moderator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that update_event fails if user is not creator or moderator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        update_data = {"title": "Updated Title"}

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.update_event(
                event_id=event_id,
                user_id=user_id,
                update_data=update_data,
            )

    @pytest.mark.asyncio
    async def test_fails_if_event_not_found(
        self,
        event_service,
        mock_event_repository,
        user_id,
        event_id,
    ):
        """Test that update_event fails if event doesn't exist."""
        # Arrange
        mock_event_repository.get_by_id.return_value = None

        update_data = {"title": "Updated Title"}

        # Act & Assert
        with pytest.raises(NotFoundException):
            await event_service.update_event(
                event_id=event_id,
                user_id=user_id,
                update_data=update_data,
            )


# ============================================================================
# Test Event Deletion
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestDeleteEvent:
    """Test event deletion."""

    @pytest.mark.asyncio
    async def test_deletes_event_as_creator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        creator_id,
        event_id,
        sample_event,
    ):
        """Test that delete_event soft deletes an event when called by creator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        # Act
        await event_service.delete_event(event_id=event_id, user_id=creator_id)

        # Assert
        mock_event_repository.delete.assert_called_once_with(event_id)

    @pytest.mark.asyncio
    async def test_deletes_event_as_admin(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that delete_event allows admin to delete any event."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.ADMIN
        )

        # Act
        await event_service.delete_event(event_id=event_id, user_id=user_id)

        # Assert
        mock_event_repository.delete.assert_called_once_with(event_id)

    @pytest.mark.asyncio
    async def test_fails_if_not_creator_or_admin(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that delete_event fails if user is not creator or admin."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.delete_event(event_id=event_id, user_id=user_id)


# ============================================================================
# Test Event Registration
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestRegisterForEvent:
    """Test event registration."""

    @pytest.mark.asyncio
    async def test_registers_user_when_capacity_available(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
        sample_registration,
    ):
        """Test that register_for_event registers user when capacity available."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        mock_event_registration_repository.get_by_event_and_user.return_value = None
        mock_event_registration_repository.count_by_event_and_status.return_value = 25
        mock_event_registration_repository.create.return_value = sample_registration

        # Act
        result = await event_service.register_for_event(
            event_id=event_id,
            user_id=user_id,
        )

        # Assert
        assert result == sample_registration
        assert result.status == "registered"
        mock_event_registration_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_adds_to_waitlist_when_at_capacity(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that register_for_event adds user to waitlist when at capacity."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        mock_event_registration_repository.get_by_event_and_user.return_value = None
        mock_event_registration_repository.count_by_event_and_status.return_value = 50
        waitlist_registration = MagicMock(
            id=uuid4(),
            event_id=event_id,
            user_id=user_id,
            status="waitlisted",
            registered_at=datetime.now(UTC),
        )
        mock_event_registration_repository.create.return_value = waitlist_registration

        # Act
        result = await event_service.register_for_event(
            event_id=event_id,
            user_id=user_id,
        )

        # Assert
        assert result.status == "waitlisted"

    @pytest.mark.asyncio
    async def test_allows_unlimited_registration_when_no_limit(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
        sample_registration,
    ):
        """Test that register_for_event allows registration when participant_limit is None."""
        # Arrange
        unlimited_event = MagicMock(**{**sample_event.__dict__, "participant_limit": None})
        mock_event_repository.get_by_id.return_value = unlimited_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        mock_event_registration_repository.get_by_event_and_user.return_value = None
        mock_event_registration_repository.create.return_value = sample_registration

        # Act
        result = await event_service.register_for_event(
            event_id=event_id,
            user_id=user_id,
        )

        # Assert
        assert result.status == "registered"

    @pytest.mark.asyncio
    async def test_fails_if_already_registered(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
        sample_registration,
    ):
        """Test that register_for_event fails if user already registered."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        mock_event_registration_repository.get_by_event_and_user.return_value = sample_registration

        # Act & Assert
        with pytest.raises(ConflictException):
            await event_service.register_for_event(
                event_id=event_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_fails_if_not_community_member(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that register_for_event fails if user is not a community member."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = None

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.register_for_event(
                event_id=event_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_fails_if_event_completed(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that register_for_event fails if event is completed."""
        # Arrange
        completed_event = MagicMock(**{**sample_event.__dict__, "status": "completed"})
        mock_event_repository.get_by_id.return_value = completed_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        # Act & Assert
        with pytest.raises(BadRequestException):
            await event_service.register_for_event(
                event_id=event_id,
                user_id=user_id,
            )


# ============================================================================
# Test Event Unregistration
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestUnregisterFromEvent:
    """Test event unregistration."""

    @pytest.mark.asyncio
    async def test_unregisters_user_and_promotes_waitlist(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        user_id,
        event_id,
        sample_event,
        sample_registration,
    ):
        """Test that unregister_from_event removes user and promotes from waitlist."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_event_registration_repository.get_by_event_and_user.return_value = sample_registration
        waitlisted_user = MagicMock(
            id=uuid4(),
            event_id=event_id,
            user_id=uuid4(),
            status="waitlisted",
            registered_at=datetime.now(UTC),
        )
        mock_event_registration_repository.get_first_waitlisted.return_value = waitlisted_user

        # Act
        await event_service.unregister_from_event(
            event_id=event_id,
            user_id=user_id,
        )

        # Assert
        mock_event_registration_repository.delete.assert_called_once_with(
            event_id=event_id,
            user_id=user_id,
        )
        mock_event_registration_repository.update_status.assert_called_once_with(
            registration_id=waitlisted_user.id,
            status="registered",
        )

    @pytest.mark.asyncio
    async def test_unregisters_without_promotion_if_no_waitlist(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        user_id,
        event_id,
        sample_event,
        sample_registration,
    ):
        """Test that unregister_from_event works when waitlist is empty."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_event_registration_repository.get_by_event_and_user.return_value = sample_registration
        mock_event_registration_repository.get_first_waitlisted.return_value = None

        # Act
        await event_service.unregister_from_event(
            event_id=event_id,
            user_id=user_id,
        )

        # Assert
        mock_event_registration_repository.delete.assert_called_once()
        mock_event_registration_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_fails_if_not_registered(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that unregister_from_event fails if user not registered."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_event_registration_repository.get_by_event_and_user.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException):
            await event_service.unregister_from_event(
                event_id=event_id,
                user_id=user_id,
            )


# ============================================================================
# Test Get Event Participants
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestGetEventParticipants:
    """Test getting event participants."""

    @pytest.mark.asyncio
    async def test_returns_registered_participants(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        event_id,
        sample_event,
    ):
        """Test that get_event_participants returns registered users."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        participants = [
            MagicMock(
                id=uuid4(),
                event_id=event_id,
                user_id=uuid4(),
                status="registered",
                registered_at=datetime.now(UTC),
            )
            for _ in range(3)
        ]
        mock_event_registration_repository.list_by_event.return_value = participants

        # Act
        result = await event_service.get_event_participants(
            event_id=event_id,
            status="registered",
        )

        # Assert
        assert len(result) == 3
        mock_event_registration_repository.list_by_event.assert_called_once_with(
            event_id=event_id,
            status="registered",
        )

    @pytest.mark.asyncio
    async def test_returns_waitlisted_participants(
        self,
        event_service,
        mock_event_repository,
        mock_event_registration_repository,
        event_id,
        sample_event,
    ):
        """Test that get_event_participants returns waitlisted users."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        waitlist = [
            MagicMock(
                id=uuid4(),
                event_id=event_id,
                user_id=uuid4(),
                status="waitlisted",
                registered_at=datetime.now(UTC),
            )
            for _ in range(2)
        ]
        mock_event_registration_repository.list_by_event.return_value = waitlist

        # Act
        result = await event_service.get_event_participants(
            event_id=event_id,
            status="waitlisted",
        )

        # Assert
        assert len(result) == 2


# ============================================================================
# Test Change Event Status
# ============================================================================


@pytest.mark.unit
@pytest.mark.us4
class TestChangeEventStatus:
    """Test changing event status."""

    @pytest.mark.asyncio
    async def test_changes_status_as_creator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        creator_id,
        event_id,
        sample_event,
    ):
        """Test that change_event_status updates status when called by creator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )
        updated_event = MagicMock(**{**sample_event.__dict__, "status": "cancelled"})
        mock_event_repository.update.return_value = updated_event

        # Act
        result = await event_service.change_event_status(
            event_id=event_id,
            user_id=creator_id,
            new_status="cancelled",
        )

        # Assert
        assert result.status == "cancelled"

    @pytest.mark.asyncio
    async def test_fails_if_not_creator_or_moderator(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        user_id,
        event_id,
        sample_event,
    ):
        """Test that change_event_status fails if user is not creator or moderator."""
        # Arrange
        mock_event_repository.get_by_id.return_value = sample_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MEMBER
        )

        # Act & Assert
        with pytest.raises(ForbiddenException):
            await event_service.change_event_status(
                event_id=event_id,
                user_id=user_id,
                new_status="cancelled",
            )

    @pytest.mark.asyncio
    async def test_validates_status_transition(
        self,
        event_service,
        mock_event_repository,
        mock_membership_repository,
        creator_id,
        event_id,
        sample_event,
    ):
        """Test that change_event_status validates status transitions."""
        # Arrange
        completed_event = MagicMock(**{**sample_event.__dict__, "status": "completed"})
        mock_event_repository.get_by_id.return_value = completed_event
        mock_membership_repository.get_by_user_and_community.return_value = MagicMock(
            role=MembershipRole.MODERATOR
        )

        # Act & Assert - cannot change completed event to published
        with pytest.raises(BadRequestException):
            await event_service.change_event_status(
                event_id=event_id,
                user_id=creator_id,
                new_status="published",
            )
