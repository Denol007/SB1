"""Unit tests for Verification database model.

Following TDD principles - these tests are written FIRST and should FAIL
until the Verification model is implemented.
"""

from datetime import UTC, datetime

from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from app.domain.enums.verification_status import VerificationStatus
from app.infrastructure.database.base import Base, TimestampMixin

# Import related models to register them in SQLAlchemy metadata
from app.infrastructure.database.models.university import University  # noqa: F401
from app.infrastructure.database.models.user import User  # noqa: F401


def test_verification_model_exists():
    """Test that Verification model can be imported."""
    from app.infrastructure.database.models.verification import Verification

    assert Verification is not None


def test_verification_inherits_from_base():
    """Test that Verification inherits from Base."""
    from app.infrastructure.database.models.verification import Verification

    assert issubclass(Verification, Base)


def test_verification_inherits_from_timestamp_mixin():
    """Test that Verification inherits from TimestampMixin."""
    from app.infrastructure.database.models.verification import Verification

    assert issubclass(Verification, TimestampMixin)


def test_verification_table_name():
    """Test that table name is 'verifications'."""
    from app.infrastructure.database.models.verification import Verification

    assert Verification.__tablename__ == "verifications"


def test_verification_has_id_column():
    """Test that Verification has id column as UUID primary key."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    id_col = mapper.columns.get("id")

    assert id_col is not None
    assert isinstance(id_col.type, postgresql.UUID)
    assert id_col.primary_key is True
    assert id_col.nullable is False


def test_verification_has_user_id_column():
    """Test that Verification has user_id foreign key column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    user_id_col = mapper.columns.get("user_id")

    assert user_id_col is not None
    assert isinstance(user_id_col.type, postgresql.UUID)
    assert user_id_col.nullable is False

    # Check foreign key constraint
    foreign_keys = list(user_id_col.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "users"


def test_verification_has_university_id_column():
    """Test that Verification has university_id foreign key column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    university_id_col = mapper.columns.get("university_id")

    assert university_id_col is not None
    assert isinstance(university_id_col.type, postgresql.UUID)
    assert university_id_col.nullable is False

    # Check foreign key constraint
    foreign_keys = list(university_id_col.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "universities"


def test_verification_has_email_column():
    """Test that Verification has email column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    email_col = mapper.columns.get("email")

    assert email_col is not None
    assert email_col.type.python_type is str
    assert email_col.nullable is False


def test_verification_has_token_hash_column():
    """Test that Verification has token_hash column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    token_hash_col = mapper.columns.get("token_hash")

    assert token_hash_col is not None
    assert token_hash_col.type.python_type is str
    assert token_hash_col.nullable is False


def test_verification_has_status_column():
    """Test that Verification has status column with VerificationStatus enum."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    status_col = mapper.columns.get("status")

    assert status_col is not None
    assert status_col.nullable is False

    # Check default value
    assert status_col.default is not None


def test_verification_has_verified_at_column():
    """Test that Verification has verified_at timestamp column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    verified_at_col = mapper.columns.get("verified_at")

    assert verified_at_col is not None
    assert verified_at_col.nullable is True


def test_verification_has_expires_at_column():
    """Test that Verification has expires_at timestamp column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    expires_at_col = mapper.columns.get("expires_at")

    assert expires_at_col is not None
    assert expires_at_col.nullable is False


def test_verification_has_index_on_token_hash():
    """Test that Verification has an index on token_hash column."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    token_hash_col = mapper.columns.get("token_hash")

    # Check if column is indexed
    assert token_hash_col.index is True or token_hash_col.unique is True


def test_verification_has_composite_index_on_user_university():
    """Test that Verification has a composite index on (user_id, university_id)."""
    from app.infrastructure.database.models.verification import Verification

    # Check table-level indexes
    indexes = Verification.__table__.indexes
    index_columns = []

    for idx in indexes:
        cols = [col.name for col in idx.columns]
        index_columns.append(tuple(cols))

    # Should have an index on (user_id, university_id)
    assert ("user_id", "university_id") in index_columns


def test_verification_has_created_at_from_mixin():
    """Test that Verification has created_at from TimestampMixin."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    created_at_col = mapper.columns.get("created_at")

    assert created_at_col is not None
    assert created_at_col.nullable is False


def test_verification_has_updated_at_from_mixin():
    """Test that Verification has updated_at from TimestampMixin."""
    from app.infrastructure.database.models.verification import Verification

    mapper = inspect(Verification)
    updated_at_col = mapper.columns.get("updated_at")

    assert updated_at_col is not None
    assert updated_at_col.nullable is False


def test_verification_instance_creation():
    """Test that Verification instance can be created."""
    from uuid import uuid4

    from app.infrastructure.database.models.verification import Verification

    user_id = uuid4()
    university_id = uuid4()
    expires_at = datetime.now(UTC)

    verification = Verification(
        user_id=user_id,
        university_id=university_id,
        email="student@stanford.edu",
        token_hash="abc123hash",
        status=VerificationStatus.PENDING,
        expires_at=expires_at,
    )

    assert verification.user_id == user_id
    assert verification.university_id == university_id
    assert verification.email == "student@stanford.edu"
    assert verification.token_hash == "abc123hash"
    assert verification.status == VerificationStatus.PENDING
    assert verification.expires_at == expires_at
    assert verification.verified_at is None


def test_verification_instance_creation_with_verified_at():
    """Test that Verification instance can be created with verified_at."""
    from uuid import uuid4

    from app.infrastructure.database.models.verification import Verification

    user_id = uuid4()
    university_id = uuid4()
    expires_at = datetime.now(UTC)
    verified_at = datetime.now(UTC)

    verification = Verification(
        user_id=user_id,
        university_id=university_id,
        email="student@mit.edu",
        token_hash="xyz789hash",
        status=VerificationStatus.VERIFIED,
        expires_at=expires_at,
        verified_at=verified_at,
    )

    assert verification.user_id == user_id
    assert verification.university_id == university_id
    assert verification.email == "student@mit.edu"
    assert verification.token_hash == "xyz789hash"
    assert verification.status == VerificationStatus.VERIFIED
    assert verification.expires_at == expires_at
    assert verification.verified_at == verified_at


def test_verification_repr():
    """Test Verification __repr__ method."""
    from uuid import uuid4

    from app.infrastructure.database.models.verification import Verification

    user_id = uuid4()
    university_id = uuid4()
    expires_at = datetime.now(UTC)

    verification = Verification(
        user_id=user_id,
        university_id=university_id,
        email="test@example.edu",
        token_hash="hash123",
        status=VerificationStatus.PENDING,
        expires_at=expires_at,
    )

    repr_str = repr(verification)
    assert "Verification" in repr_str
    assert str(user_id) in repr_str
    assert str(university_id) in repr_str
