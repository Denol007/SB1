"""Test data factories for StudyBuddy platform.

This package provides Factory Boy factories for generating test data.
All factories use Faker for realistic data generation.

Available Factories:
    User Factories:
        - UserFactory: Base factory for users
        - AdminUserFactory: Admin users
        - ProspectiveStudentFactory: Prospective students
        - VerifiedStudentFactory: Students with .edu emails
        - DeletedUserFactory: Soft-deleted users

    Verification Factories:
        - VerificationFactory: Base factory for verifications
        - VerifiedVerificationFactory: Verified verifications
        - ExpiredVerificationFactory: Expired verifications
        - PendingVerificationFactory: Pending verifications

    University Factories:
        - UniversityFactory: Educational institutions

Usage:
    from tests.factories import UserFactory, AdminUserFactory
    from tests.factories import VerificationFactory, UniversityFactory

    user = UserFactory.build()
    admin = AdminUserFactory.build()
    verification = VerificationFactory.build()
    university = UniversityFactory.build()
"""

from tests.factories.user_factory import (
    AdminUserFactory,
    DeletedUserFactory,
    ProspectiveStudentFactory,
    UserFactory,
    VerifiedStudentFactory,
)
from tests.factories.verification_factory import (
    ExpiredVerificationFactory,
    PendingVerificationFactory,
    UniversityFactory,
    VerificationFactory,
    VerifiedVerificationFactory,
)

__all__ = [
    # User factories
    "UserFactory",
    "AdminUserFactory",
    "ProspectiveStudentFactory",
    "VerifiedStudentFactory",
    "DeletedUserFactory",
    # Verification factories
    "VerificationFactory",
    "VerifiedVerificationFactory",
    "ExpiredVerificationFactory",
    "PendingVerificationFactory",
    # University factories
    "UniversityFactory",
]
