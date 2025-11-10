"""Unit tests for University database model.

Following TDD principles - these tests are written FIRST and should FAIL
until the University model is implemented.
"""

from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

from app.infrastructure.database.base import Base, TimestampMixin


def test_university_model_exists():
    """Test that University model can be imported."""
    from app.infrastructure.database.models.university import University

    assert University is not None


def test_university_inherits_from_base():
    """Test that University inherits from Base."""
    from app.infrastructure.database.models.university import University

    assert issubclass(University, Base)


def test_university_inherits_from_timestamp_mixin():
    """Test that University inherits from TimestampMixin."""
    from app.infrastructure.database.models.university import University

    assert issubclass(University, TimestampMixin)


def test_university_table_name():
    """Test that table name is 'universities'."""
    from app.infrastructure.database.models.university import University

    assert University.__tablename__ == "universities"


def test_university_has_id_column():
    """Test that University has id column as UUID primary key."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    id_col = mapper.columns.get("id")

    assert id_col is not None
    assert isinstance(id_col.type, postgresql.UUID)
    assert id_col.primary_key is True
    assert id_col.nullable is False


def test_university_has_name_column():
    """Test that University has name column."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    name_col = mapper.columns.get("name")

    assert name_col is not None
    assert name_col.type.python_type is str
    assert name_col.nullable is False
    assert name_col.unique is not True


def test_university_has_domain_column():
    """Test that University has domain column."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    domain_col = mapper.columns.get("domain")

    assert domain_col is not None
    assert domain_col.type.python_type is str
    assert domain_col.nullable is False
    assert domain_col.unique is True


def test_university_has_logo_url_column():
    """Test that University has logo_url column."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    logo_url_col = mapper.columns.get("logo_url")

    assert logo_url_col is not None
    assert logo_url_col.type.python_type is str
    assert logo_url_col.nullable is True


def test_university_has_country_column():
    """Test that University has country column."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    country_col = mapper.columns.get("country")

    assert country_col is not None
    assert country_col.type.python_type is str
    assert country_col.nullable is True


def test_university_has_index_on_domain():
    """Test that University has an index on domain column."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    domain_col = mapper.columns.get("domain")

    # Check if column is indexed
    assert domain_col.index is True or domain_col.unique is True


def test_university_has_created_at_from_mixin():
    """Test that University has created_at from TimestampMixin."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    created_at_col = mapper.columns.get("created_at")

    assert created_at_col is not None
    assert created_at_col.nullable is False


def test_university_has_updated_at_from_mixin():
    """Test that University has updated_at from TimestampMixin."""
    from app.infrastructure.database.models.university import University

    mapper = inspect(University)
    updated_at_col = mapper.columns.get("updated_at")

    assert updated_at_col is not None
    assert updated_at_col.nullable is False


def test_university_instance_creation():
    """Test that University instance can be created."""
    from app.infrastructure.database.models.university import University

    university = University(
        name="Stanford University",
        domain="stanford.edu",
        logo_url="https://example.com/stanford-logo.png",
        country="United States",
    )

    assert university.name == "Stanford University"
    assert university.domain == "stanford.edu"
    assert university.logo_url == "https://example.com/stanford-logo.png"
    assert university.country == "United States"


def test_university_instance_creation_minimal():
    """Test that University instance can be created with minimal fields."""
    from app.infrastructure.database.models.university import University

    university = University(
        name="MIT",
        domain="mit.edu",
    )

    assert university.name == "MIT"
    assert university.domain == "mit.edu"
    assert university.logo_url is None
    assert university.country is None


def test_university_repr():
    """Test University __repr__ method."""
    from app.infrastructure.database.models.university import University

    university = University(
        name="Harvard University",
        domain="harvard.edu",
    )

    repr_str = repr(university)
    assert "University" in repr_str
    assert "harvard.edu" in repr_str
