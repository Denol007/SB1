"""Tests for email background tasks.

This module tests the Celery email tasks for:
- Sending verification emails
- Error handling and retry logic
- Database integration
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundException
from app.tasks.email_tasks import _send_verification_email_async


class TestSendVerificationEmail:
    """Test suite for send_verification_email Celery task."""

    @pytest.mark.asyncio
    async def test_sends_verification_email_successfully(self):
        """Should send verification email with correct parameters."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"
        verification_email = "student@stanford.edu"
        university_name = "Stanford University"

        mock_verification = MagicMock()
        mock_verification.id = uuid4()
        mock_verification.email = verification_email
        mock_verification.university_id = uuid4()

        mock_university = MagicMock()
        mock_university.id = mock_verification.university_id
        mock_university.name = university_name

        with (
            patch("app.tasks.email_tasks.SessionFactory") as mock_session_factory,
            patch(
                "app.tasks.email_tasks.SQLAlchemyVerificationRepository"
            ) as mock_verification_repo_class,
            patch(
                "app.tasks.email_tasks.SQLAlchemyUniversityRepository"
            ) as mock_university_repo_class,
            patch("app.tasks.email_tasks.SMTPEmail") as mock_email_class,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_verification_repo = AsyncMock()
            mock_verification_repo.get_by_id.return_value = mock_verification
            mock_verification_repo_class.return_value = mock_verification_repo

            mock_university_repo = AsyncMock()
            mock_university_repo.get_by_id.return_value = mock_university
            mock_university_repo_class.return_value = mock_university_repo

            mock_email_service = AsyncMock()
            mock_email_class.return_value = mock_email_service

            # Act
            result = await _send_verification_email_async(verification_id, token)

            # Assert
            assert result["status"] == "success"
            assert result["verification_id"] == verification_id
            assert result["university_name"] == university_name
            assert verification_email in result["message"]

            mock_verification_repo.get_by_id.assert_called_once()
            mock_university_repo.get_by_id.assert_called_once_with(mock_verification.university_id)
            mock_email_service.send_verification_email.assert_called_once_with(
                to=verification_email,
                token=token,
                university_name=university_name,
            )

    @pytest.mark.asyncio
    async def test_raises_not_found_when_verification_missing(self):
        """Should raise NotFoundException when verification doesn't exist."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"

        with (
            patch("app.tasks.email_tasks.SessionFactory") as mock_session_factory,
            patch(
                "app.tasks.email_tasks.SQLAlchemyVerificationRepository"
            ) as mock_verification_repo_class,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_verification_repo = AsyncMock()
            mock_verification_repo.get_by_id.return_value = None
            mock_verification_repo_class.return_value = mock_verification_repo

            # Act & Assert
            with pytest.raises(NotFoundException) as exc_info:
                await _send_verification_email_async(verification_id, token)

            assert verification_id in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_university_missing(self):
        """Should raise NotFoundException when university doesn't exist."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"

        mock_verification = MagicMock()
        mock_verification.id = uuid4()
        mock_verification.email = "student@stanford.edu"
        mock_verification.university_id = uuid4()

        with (
            patch("app.tasks.email_tasks.SessionFactory") as mock_session_factory,
            patch(
                "app.tasks.email_tasks.SQLAlchemyVerificationRepository"
            ) as mock_verification_repo_class,
            patch(
                "app.tasks.email_tasks.SQLAlchemyUniversityRepository"
            ) as mock_university_repo_class,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_verification_repo = AsyncMock()
            mock_verification_repo.get_by_id.return_value = mock_verification
            mock_verification_repo_class.return_value = mock_verification_repo

            mock_university_repo = AsyncMock()
            mock_university_repo.get_by_id.return_value = None
            mock_university_repo_class.return_value = mock_university_repo

            # Act & Assert
            with pytest.raises(NotFoundException) as exc_info:
                await _send_verification_email_async(verification_id, token)

            assert str(mock_verification.university_id) in str(exc_info.value)

    def test_task_retries_on_email_failure(self):
        """Should retry task when email sending fails."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"

        with (
            patch("asyncio.run") as mock_asyncio_run,
            patch("app.tasks.email_tasks.send_verification_email.retry") as mock_retry,
        ):
            mock_asyncio_run.side_effect = Exception("Email service error")
            mock_retry.side_effect = Exception("Retry scheduled")

            # Act & Assert
            with pytest.raises(Exception):  # noqa: B017
                from app.tasks.email_tasks import send_verification_email as task

                # Call the underlying function, not through Celery
                task.run(verification_id, token)

            # Verify retry was called
            mock_retry.assert_called_once()

    def test_task_does_not_retry_on_not_found(self):
        """Should not retry task when verification not found."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"

        with (
            patch("asyncio.run") as mock_asyncio_run,
            patch("app.tasks.email_tasks.send_verification_email.retry") as mock_retry,
        ):
            mock_asyncio_run.side_effect = NotFoundException(message="Verification not found")

            # Act & Assert
            with pytest.raises(NotFoundException):
                from app.tasks.email_tasks import send_verification_email as task

                task.run(verification_id, token)

            # Verify retry was NOT called
            mock_retry.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetches_correct_verification_from_database(self):
        """Should fetch verification by ID from database."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"

        mock_verification = MagicMock()
        mock_verification.id = uuid4()
        mock_verification.email = "student@mit.edu"
        mock_verification.university_id = uuid4()

        mock_university = MagicMock()
        mock_university.id = mock_verification.university_id
        mock_university.name = "MIT"

        with (
            patch("app.tasks.email_tasks.SessionFactory") as mock_session_factory,
            patch(
                "app.tasks.email_tasks.SQLAlchemyVerificationRepository"
            ) as mock_verification_repo_class,
            patch(
                "app.tasks.email_tasks.SQLAlchemyUniversityRepository"
            ) as mock_university_repo_class,
            patch("app.tasks.email_tasks.SMTPEmail") as mock_email_class,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_verification_repo = AsyncMock()
            mock_verification_repo.get_by_id.return_value = mock_verification
            mock_verification_repo_class.return_value = mock_verification_repo

            mock_university_repo = AsyncMock()
            mock_university_repo.get_by_id.return_value = mock_university
            mock_university_repo_class.return_value = mock_university_repo

            mock_email_service = AsyncMock()
            mock_email_class.return_value = mock_email_service

            # Act
            await _send_verification_email_async(verification_id, token)

            # Assert - verify verification was fetched
            mock_verification_repo.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_university_name_in_email(self):
        """Should include university name when sending email."""
        # Arrange
        verification_id = str(uuid4())
        token = "test_token_123"
        university_name = "Harvard University"

        mock_verification = MagicMock()
        mock_verification.id = uuid4()
        mock_verification.email = "student@harvard.edu"
        mock_verification.university_id = uuid4()

        mock_university = MagicMock()
        mock_university.id = mock_verification.university_id
        mock_university.name = university_name

        with (
            patch("app.tasks.email_tasks.SessionFactory") as mock_session_factory,
            patch(
                "app.tasks.email_tasks.SQLAlchemyVerificationRepository"
            ) as mock_verification_repo_class,
            patch(
                "app.tasks.email_tasks.SQLAlchemyUniversityRepository"
            ) as mock_university_repo_class,
            patch("app.tasks.email_tasks.SMTPEmail") as mock_email_class,
        ):
            # Setup mocks
            mock_session = AsyncMock()
            mock_session_factory.return_value.__aenter__.return_value = mock_session

            mock_verification_repo = AsyncMock()
            mock_verification_repo.get_by_id.return_value = mock_verification
            mock_verification_repo_class.return_value = mock_verification_repo

            mock_university_repo = AsyncMock()
            mock_university_repo.get_by_id.return_value = mock_university
            mock_university_repo_class.return_value = mock_university_repo

            mock_email_service = AsyncMock()
            mock_email_class.return_value = mock_email_service

            # Act
            await _send_verification_email_async(verification_id, token)

            # Assert
            call_args = mock_email_service.send_verification_email.call_args
            assert call_args[1]["university_name"] == university_name
