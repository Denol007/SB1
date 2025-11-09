"""User factory for generating test user instances.

This module provides Factory Boy factories for creating User model instances
with realistic fake data for testing purposes.
"""

from datetime import UTC, datetime
from uuid import uuid4

import factory
from faker import Faker

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating User model instances with realistic test data.

    Uses Factory Boy and Faker to generate users with random but realistic
    data. Supports both build() for unsaved instances and create() when
    integrated with database session.

    Attributes:
        id: UUID primary key (auto-generated).
        google_id: Unique Google OAuth ID.
        email: Valid email address.
        name: Full name of the user.
        bio: Short biography text (optional).
        avatar_url: URL to user's avatar image (optional).
        role: User role enum (default: 'student').
        created_at: Timestamp when user was created.
        updated_at: Timestamp when user was last updated.
        deleted_at: Soft delete timestamp (None for active users).

    Example:
        >>> # Build a user instance (not persisted)
        >>> user = UserFactory.build()
        >>> print(user.email)
        'jane.smith@example.com'

        >>> # Build with specific attributes
        >>> admin = UserFactory.build(role='admin', email='admin@test.edu')
        >>> print(admin.role)
        'admin'

        >>> # Create user with custom data
        >>> verified_user = UserFactory.build(
        ...     email='student@university.edu',
        ...     name='John Doe'
        ... )
        >>> print(verified_user.name)
        'John Doe'

    Note:
        This factory uses the Factory pattern. To persist to database,
        you'll need to use a SQLAlchemyModelFactory subclass once the
        User model is created.
    """

    class Meta:
        """Factory configuration."""

        model = dict  # Temporary: will be replaced with actual User model

    # Primary Key
    id = factory.LazyFunction(uuid4)

    # OAuth & Authentication
    google_id = factory.LazyAttribute(lambda _: f"google_{fake.numerify('####################')}")

    # User Profile
    email = factory.LazyAttribute(lambda _: fake.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    bio = factory.LazyAttribute(
        lambda _: fake.text(max_nb_chars=200) if fake.boolean(chance_of_getting_true=70) else None
    )
    avatar_url = factory.LazyAttribute(
        lambda _: fake.image_url() if fake.boolean(chance_of_getting_true=60) else None
    )

    # Role
    role = "student"  # Default role; can be 'student', 'prospective_student', or 'admin'

    # Timestamps
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
    deleted_at = None  # None for active users; set to datetime for soft-deleted users


class AdminUserFactory(UserFactory):
    """Factory for creating admin user instances.

    Convenience factory that pre-configures role='admin'.

    Example:
        >>> admin = AdminUserFactory.build()
        >>> print(admin.role)
        'admin'
    """

    role = "admin"


class ProspectiveStudentFactory(UserFactory):
    """Factory for creating prospective student user instances.

    Convenience factory that pre-configures role='prospective_student'.
    These are users who haven't verified their university email yet.

    Example:
        >>> prospect = ProspectiveStudentFactory.build()
        >>> print(prospect.role)
        'prospective_student'
    """

    role = "prospective_student"


class VerifiedStudentFactory(UserFactory):
    """Factory for creating verified student user instances.

    Convenience factory for students with university email domains.
    Generates university email addresses for realistic testing.

    Example:
        >>> student = VerifiedStudentFactory.build()
        >>> print(student.email)
        'john.doe@university.edu'
        >>> print(student.role)
        'student'
    """

    role = "student"
    email = factory.LazyAttribute(
        lambda _: f"{fake.user_name()}@{fake.random_element(['stanford.edu', 'mit.edu', 'berkeley.edu', 'harvard.edu'])}"
    )


class DeletedUserFactory(UserFactory):
    """Factory for creating soft-deleted user instances.

    Convenience factory for testing soft delete functionality.

    Example:
        >>> deleted_user = DeletedUserFactory.build()
        >>> assert deleted_user.deleted_at is not None
    """

    deleted_at = factory.LazyFunction(lambda: datetime.now(UTC))
