"""Test factories for verification and university models using Factory Boy.

This module provides test data factories for:
- Verification: Student verification records
- University: Educational institutions

Usage:
    from tests.factories import VerificationFactory, UniversityFactory

    # Create a pending verification
    verification = VerificationFactory.build()

    # Create a verified verification
    verified = VerifiedVerificationFactory.build()

    # Create with custom attributes
    custom = VerificationFactory.build(
        email="student@stanford.edu",
        status="verified"
    )

    # Create a university
    university = UniversityFactory.build()
"""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import factory
from faker import Faker

fake = Faker()


class UniversityFactory(factory.Factory):
    """Factory for creating test university data.

    Generates realistic university data with .edu domains.

    Attributes:
        id: Unique university identifier (UUID)
        name: University name (e.g., "Stanford University")
        domain: Email domain for verification (e.g., "stanford.edu")
        logo_url: University logo URL (optional)
        country: University country code (e.g., "US")
        created_at: Timestamp when university was added
        updated_at: Timestamp of last update
    """

    class Meta:
        model = dict  # Temporary until University model exists (T074)

    id = factory.LazyFunction(uuid4)
    name = factory.LazyAttribute(lambda _: f"{fake.company()} University")
    domain = factory.LazyAttribute(lambda obj: f"{obj.name.lower().split()[0]}.edu")
    logo_url = factory.LazyAttribute(
        lambda _: fake.image_url() if fake.boolean(chance_of_getting_true=80) else None
    )
    country = factory.LazyAttribute(lambda _: fake.country_code())
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class VerificationFactory(factory.Factory):
    """Factory for creating test verification data.

    Generates student verification records with realistic data.

    Attributes:
        id: Unique verification identifier (UUID)
        user_id: Foreign key to user (UUID)
        university_id: Foreign key to university (UUID)
        email: Student email for verification
        token_hash: SHA-256 hash of verification token
        status: Verification status (pending, verified, expired)
        verified_at: Timestamp when verification was confirmed (nullable)
        expires_at: Token expiration timestamp (24 hours from creation)
        created_at: Timestamp when verification was requested
        updated_at: Timestamp of last update
    """

    class Meta:
        model = dict  # Temporary until Verification model exists (T075)

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    university_id = factory.LazyFunction(uuid4)
    email = factory.LazyAttribute(lambda _: fake.email(domain=f"{fake.word()}.edu"))
    token_hash = factory.LazyAttribute(lambda _: sha256(fake.uuid4().encode()).hexdigest())
    status = "pending"
    verified_at = None
    expires_at = factory.LazyFunction(lambda: datetime.now(UTC) + timedelta(hours=24))
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))


class VerifiedVerificationFactory(VerificationFactory):
    """Factory for creating verified student verifications.

    Inherits from VerificationFactory with status='verified' and verified_at set.
    """

    status = "verified"
    verified_at = factory.LazyFunction(lambda: datetime.now(UTC))


class ExpiredVerificationFactory(VerificationFactory):
    """Factory for creating expired verifications.

    Inherits from VerificationFactory with status='expired' and past expiration.
    """

    status = "expired"
    expires_at = factory.LazyFunction(lambda: datetime.now(UTC) - timedelta(hours=1))


class PendingVerificationFactory(VerificationFactory):
    """Factory for creating pending verifications.

    Inherits from VerificationFactory with status='pending' (default).
    Useful for explicit test clarity.
    """

    status = "pending"
