"""Unit tests for User database model.

Tests the User SQLAlchemy model structure, fields, constraints, and relationships.
Following TDD - these tests will fail until implementation is complete.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import inspect

from app.domain.enums.user_role import UserRole
from app.infrastructure.database.base import Base, TimestampMixin
from app.infrastructure.database.models.user import User


class TestUserModel:
    """Test User database model structure and behavior."""

    def test_user_inherits_from_base(self):
        """Test that User inherits from SQLAlchemy Base."""
        assert issubclass(User, Base)

    def test_user_inherits_from_timestamp_mixin(self):
        """Test that User inherits from TimestampMixin for timestamps."""
        assert issubclass(User, TimestampMixin)

    def test_user_has_correct_tablename(self):
        """Test that User maps to 'users' table."""
        assert User.__tablename__ == "users"

    def test_user_has_id_column(self):
        """Test that User has id column as UUID primary key."""
        mapper = inspect(User)
        id_col = mapper.columns["id"]

        assert id_col.primary_key is True
        assert id_col.nullable is False
        # Column type should be UUID
        assert "UUID" in str(id_col.type)

    def test_user_has_google_id_column(self):
        """Test that User has google_id column."""
        mapper = inspect(User)
        google_id_col = mapper.columns["google_id"]

        assert google_id_col.unique is True
        assert google_id_col.nullable is False
        assert google_id_col.index is True

    def test_user_has_email_column(self):
        """Test that User has email column."""
        mapper = inspect(User)
        email_col = mapper.columns["email"]

        assert email_col.unique is True
        assert email_col.nullable is False
        assert email_col.index is True

    def test_user_has_name_column(self):
        """Test that User has name column."""
        mapper = inspect(User)
        name_col = mapper.columns["name"]

        assert name_col.nullable is False

    def test_user_has_bio_column(self):
        """Test that User has bio column (nullable)."""
        mapper = inspect(User)
        bio_col = mapper.columns["bio"]

        assert bio_col.nullable is True

    def test_user_has_avatar_url_column(self):
        """Test that User has avatar_url column (nullable)."""
        mapper = inspect(User)
        avatar_url_col = mapper.columns["avatar_url"]

        assert avatar_url_col.nullable is True

    def test_user_has_role_column(self):
        """Test that User has role column with default."""
        mapper = inspect(User)
        role_col = mapper.columns["role"]

        assert role_col.nullable is False
        # Should have a default value
        assert role_col.default is not None

    def test_user_has_deleted_at_column(self):
        """Test that User has deleted_at column for soft deletes."""
        mapper = inspect(User)
        deleted_at_col = mapper.columns["deleted_at"]

        assert deleted_at_col.nullable is True
        assert deleted_at_col.index is True

    def test_user_has_created_at_from_mixin(self):
        """Test that User has created_at from TimestampMixin."""
        mapper = inspect(User)
        created_at_col = mapper.columns["created_at"]

        assert created_at_col.nullable is False
        assert created_at_col.default is not None

    def test_user_has_updated_at_from_mixin(self):
        """Test that User has updated_at from TimestampMixin."""
        mapper = inspect(User)
        updated_at_col = mapper.columns["updated_at"]

        assert updated_at_col.nullable is False
        assert updated_at_col.default is not None
        assert updated_at_col.onupdate is not None

    def test_user_instance_can_be_created(self):
        """Test that User instance can be created with required fields."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        assert user.id is not None
        assert user.google_id == "google-123456"
        assert user.email == "test@stanford.edu"
        assert user.name == "Test User"
        assert user.role == UserRole.STUDENT

    def test_user_instance_with_optional_fields(self):
        """Test that User instance can be created with optional fields."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
            bio="I am a student",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert user.bio == "I am a student"
        assert user.avatar_url == "https://example.com/avatar.jpg"

    def test_user_deleted_at_defaults_to_none(self):
        """Test that deleted_at defaults to None (not soft deleted)."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        assert user.deleted_at is None

    def test_user_can_be_soft_deleted(self):
        """Test that User can be soft deleted by setting deleted_at."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        # Soft delete
        user.deleted_at = datetime.now(UTC)

        assert user.deleted_at is not None
        assert isinstance(user.deleted_at, datetime)

    def test_user_role_is_enum(self):
        """Test that role field accepts UserRole enum."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.PROSPECTIVE_STUDENT,
        )

        assert user.role == UserRole.PROSPECTIVE_STUDENT
        assert isinstance(user.role, UserRole)

    def test_user_has_repr(self):
        """Test that User has a useful string representation."""
        user = User(
            id=uuid4(),
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        repr_str = repr(user)
        assert "User" in repr_str
        assert "test@stanford.edu" in repr_str

    def test_user_id_is_uuid_type(self):
        """Test that user.id is a UUID instance."""
        user_id = uuid4()
        user = User(
            id=user_id,
            google_id="google-123456",
            email="test@stanford.edu",
            name="Test User",
            role=UserRole.STUDENT,
        )

        assert isinstance(user.id, UUID)
        assert user.id == user_id

    def test_user_all_required_columns_exist(self):
        """Test that all required columns exist on User model."""
        mapper = inspect(User)
        column_names = {col.name for col in mapper.columns}

        required_columns = {
            "id",
            "google_id",
            "email",
            "name",
            "bio",
            "avatar_url",
            "role",
            "deleted_at",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(column_names)
