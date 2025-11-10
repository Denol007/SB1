#!/usr/bin/env python3
"""Seed database with initial data for development and testing.

This script populates the database with:
- Universities (Stanford, MIT, Harvard, etc.)
- Test users (verified students, unverified users, admin)
- Verifications linking users to universities

Usage:
    python scripts/seed_data.py

Requirements:
    - Database must be running and migrated (alembic upgrade head)
    - Run from project root directory
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

# Add project root to path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.domain.enums.user_role import UserRole  # noqa: E402
from app.domain.enums.verification_status import VerificationStatus  # noqa: E402
from app.domain.value_objects.verification_token import VerificationToken  # noqa: E402
from app.infrastructure.database.models.university import University  # noqa: E402
from app.infrastructure.database.models.user import User  # noqa: E402
from app.infrastructure.database.models.verification import Verification  # noqa: E402
from app.infrastructure.database.session import get_async_session_factory  # noqa: E402

# Universities to seed
UNIVERSITIES = [
    {
        "name": "Stanford University",
        "domain": "stanford.edu",
        "country": "United States",
        "logo_url": "https://identity.stanford.edu/wp-content/uploads/sites/3/2020/07/block-s-right.png",
    },
    {
        "name": "Massachusetts Institute of Technology",
        "domain": "mit.edu",
        "country": "United States",
        "logo_url": "https://web.mit.edu/graphicidentity/logo/mit-logo.png",
    },
    {
        "name": "Harvard University",
        "domain": "harvard.edu",
        "country": "United States",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Harvard_University_coat_of_arms.svg/200px-Harvard_University_coat_of_arms.svg.png",
    },
    {
        "name": "University of California, Berkeley",
        "domain": "berkeley.edu",
        "country": "United States",
        "logo_url": "https://brand.berkeley.edu/wp-content/uploads/2023/09/ucbseal_139_540.png",
    },
    {
        "name": "California Institute of Technology",
        "domain": "caltech.edu",
        "country": "United States",
        "logo_url": "https://www.caltech.edu/img/logo.svg",
    },
    {
        "name": "University of Oxford",
        "domain": "ox.ac.uk",
        "country": "United Kingdom",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Oxford-University-Circlet.svg/200px-Oxford-University-Circlet.svg.png",
    },
    {
        "name": "University of Cambridge",
        "domain": "cam.ac.uk",
        "country": "United Kingdom",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/University_of_Cambridge_logo.svg/200px-University_of_Cambridge_logo.svg.png",
    },
    {
        "name": "ETH Zurich",
        "domain": "ethz.ch",
        "country": "Switzerland",
        "logo_url": "https://ethz.ch/etc/designs/ethz/img/header/ethz_logo_black.svg",
    },
    {
        "name": "National University of Singapore",
        "domain": "nus.edu.sg",
        "country": "Singapore",
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b9/NUS_coat_of_arms.svg/200px-NUS_coat_of_arms.svg.png",
    },
    {
        "name": "University of Toronto",
        "domain": "utoronto.ca",
        "country": "Canada",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/University_of_Toronto_coat_of_arms.svg/200px-University_of_Toronto_coat_of_arms.svg.png",
    },
]

# Test users to seed
TEST_USERS = [
    {
        "google_id": "google-verified-student-1",
        "email": "alice@stanford.edu",
        "name": "Alice Johnson",
        "bio": "CS major interested in AI and machine learning. Love hiking and coffee!",
        "role": UserRole.STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=1",
        "verified_university": "stanford.edu",
    },
    {
        "google_id": "google-verified-student-2",
        "email": "bob@mit.edu",
        "name": "Bob Smith",
        "bio": "Physics PhD candidate researching quantum computing.",
        "role": UserRole.STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=12",
        "verified_university": "mit.edu",
    },
    {
        "google_id": "google-verified-student-3",
        "email": "carol@harvard.edu",
        "name": "Carol Williams",
        "bio": "Pre-med student passionate about global health.",
        "role": UserRole.STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=5",
        "verified_university": "harvard.edu",
    },
    {
        "google_id": "google-verified-student-4",
        "email": "david@berkeley.edu",
        "name": "David Brown",
        "bio": "Business major and entrepreneur. Building the next unicorn startup!",
        "role": UserRole.STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=13",
        "verified_university": "berkeley.edu",
    },
    {
        "google_id": "google-unverified-user-1",
        "email": "eve.martinez@gmail.com",
        "name": "Eve Martinez",
        "bio": "High school senior exploring universities. Interested in engineering!",
        "role": UserRole.PROSPECTIVE_STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=9",
        "verified_university": None,
    },
    {
        "google_id": "google-unverified-user-2",
        "email": "frank.lee@outlook.com",
        "name": "Frank Lee",
        "bio": "Recent graduate looking to connect with university communities.",
        "role": UserRole.PROSPECTIVE_STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=14",
        "verified_university": None,
    },
    {
        "google_id": "google-admin-user-1",
        "email": "admin@studybuddy.app",
        "name": "Admin User",
        "bio": "Platform administrator. Contact me for support or moderation issues.",
        "role": UserRole.ADMIN,
        "avatar_url": "https://i.pravatar.cc/150?img=60",
        "verified_university": None,
    },
    {
        "google_id": "google-multi-verified-1",
        "email": "grace@caltech.edu",
        "name": "Grace Chen",
        "bio": "Transfer student. Previously at MIT, now at Caltech. Double major in Math and CS.",
        "role": UserRole.STUDENT,
        "avatar_url": "https://i.pravatar.cc/150?img=44",
        "verified_university": "caltech.edu",
        "additional_verifications": ["mit.edu"],
    },
]


async def clear_existing_data(session: AsyncSession) -> None:
    """Clear existing seed data from the database.

    Args:
        session: Async database session
    """
    print("🗑️  Clearing existing seed data...")

    # Delete in correct order to respect foreign key constraints
    # Verifications first (depends on users and universities)
    result = await session.execute(select(Verification))
    verifications = result.scalars().all()
    for verification in verifications:
        await session.delete(verification)

    # Users second
    result = await session.execute(select(User))
    users = result.scalars().all()
    for user in users:
        await session.delete(user)

    # Universities last
    result = await session.execute(select(University))
    universities = result.scalars().all()
    for university in universities:
        await session.delete(university)

    await session.commit()
    print(
        f"   Deleted {len(verifications)} verifications, {len(users)} users, {len(universities)} universities"
    )


async def seed_universities(session: AsyncSession) -> dict[str, University]:
    """Seed universities into the database.

    Args:
        session: Async database session

    Returns:
        Dictionary mapping domain to University instance
    """
    print("\n🎓 Seeding universities...")

    universities_map: dict[str, University] = {}

    for uni_data in UNIVERSITIES:
        university = University(
            id=uuid4(),
            name=uni_data["name"],
            domain=uni_data["domain"],
            country=uni_data["country"],
            logo_url=uni_data.get("logo_url"),
        )
        session.add(university)
        universities_map[uni_data["domain"]] = university
        print(f"   ✓ {uni_data['name']} ({uni_data['domain']})")

    await session.commit()
    print(f"   Seeded {len(universities_map)} universities")

    return universities_map


async def seed_users_and_verifications(
    session: AsyncSession, universities_map: dict[str, University]
) -> None:
    """Seed test users and their verifications.

    Args:
        session: Async database session
        universities_map: Dictionary mapping domain to University instance
    """
    print("\n👥 Seeding users and verifications...")

    verified_count = 0
    unverified_count = 0
    admin_count = 0
    verification_count = 0

    for user_data in TEST_USERS:
        user_dict = cast(dict[str, Any], user_data)  # Type cast for dict access

        # Create user
        user = User(
            id=uuid4(),
            google_id=user_dict["google_id"],
            email=user_dict["email"],
            name=user_dict["name"],
            bio=user_dict.get("bio"),
            avatar_url=user_dict.get("avatar_url"),
            role=user_dict["role"],
        )
        session.add(user)

        # Create verification if user is verified
        verified_domain = user_dict.get("verified_university")
        if verified_domain:
            university = universities_map.get(verified_domain)
            if university:
                # Create verified verification
                token = VerificationToken.generate()
                verification = Verification(
                    id=uuid4(),
                    user_id=user.id,
                    university_id=university.id,
                    email=user_dict["email"],
                    token_hash=token.get_hash(),
                    status=VerificationStatus.VERIFIED,
                    verified_at=datetime.now(UTC) - timedelta(days=30),  # Verified 30 days ago
                    expires_at=datetime.now(UTC) + timedelta(days=335),  # Expires in ~1 year
                )
                session.add(verification)
                verification_count += 1

                # Add additional verifications if specified
                additional_domains = user_dict.get("additional_verifications", [])
                for domain in additional_domains:
                    additional_university = universities_map.get(domain)
                    if additional_university:
                        additional_token = VerificationToken.generate()
                        additional_verification = Verification(
                            id=uuid4(),
                            user_id=user.id,
                            university_id=additional_university.id,
                            email=f"{user_dict['name'].lower().replace(' ', '.')}@{domain}",
                            token_hash=additional_token.get_hash(),
                            status=VerificationStatus.VERIFIED,
                            verified_at=datetime.now(UTC)
                            - timedelta(days=60),  # Verified 60 days ago
                            expires_at=datetime.now(UTC)
                            + timedelta(days=305),  # Expires in ~1 year
                        )
                        session.add(additional_verification)
                        verification_count += 1

        # Count by role
        if user_dict["role"] == UserRole.STUDENT:
            verified_count += 1
            print(f"   ✓ {user_dict['name']} - Verified Student at {verified_domain or 'N/A'}")
        elif user_dict["role"] == UserRole.PROSPECTIVE_STUDENT:
            unverified_count += 1
            print(f"   ✓ {user_dict['name']} - Prospective Student (Unverified)")
        elif user_dict["role"] == UserRole.ADMIN:
            admin_count += 1
            print(f"   ✓ {user_dict['name']} - Admin")

    await session.commit()
    print(
        f"\n   Seeded {verified_count} verified students, {unverified_count} prospective students, {admin_count} admins"
    )
    print(f"   Created {verification_count} verifications")


async def display_summary(session: AsyncSession) -> None:
    """Display summary of seeded data.

    Args:
        session: Async database session
    """
    print("\n" + "=" * 70)
    print("📊 SEED DATA SUMMARY")
    print("=" * 70)

    # Count universities
    result = await session.execute(select(University))
    universities = result.scalars().all()
    print(f"\n🎓 Universities: {len(universities)}")
    for uni in universities:
        print(f"   • {uni.name} ({uni.domain})")

    # Count users by role
    user_result = await session.execute(select(User))
    users_sequence = user_result.scalars().all()
    users: list[User] = list(users_sequence)
    students: list[User] = [u for u in users if u.role == UserRole.STUDENT]
    prospective: list[User] = [u for u in users if u.role == UserRole.PROSPECTIVE_STUDENT]
    admins: list[User] = [u for u in users if u.role == UserRole.ADMIN]

    print(f"\n👥 Users: {len(users)}")
    print(f"   • Verified Students: {len(students)}")
    print(f"   • Prospective Students: {len(prospective)}")
    print(f"   • Admins: {len(admins)}")

    # Count verifications
    verification_result = await session.execute(select(Verification))
    verifications_sequence = verification_result.scalars().all()
    verifications: list[Verification] = list(verifications_sequence)
    verified: list[Verification] = [
        v for v in verifications if v.status == VerificationStatus.VERIFIED
    ]
    pending: list[Verification] = [
        v for v in verifications if v.status == VerificationStatus.PENDING
    ]

    print(f"\n✅ Verifications: {len(verifications)}")
    print(f"   • Verified: {len(verified)}")
    print(f"   • Pending: {len(pending)}")

    print("\n" + "=" * 70)
    print("\n✨ Seed data successfully created!")
    print("\n📝 Sample Login Credentials (Google OAuth):")
    print("   • Verified Student: alice@stanford.edu")
    print("   • Unverified User: eve.martinez@gmail.com")
    print("   • Admin: admin@studybuddy.app")
    print("\n💡 Tip: Use these accounts for testing the API endpoints")
    print("=" * 70 + "\n")


async def main() -> None:
    """Main function to run the seed script."""
    print("\n" + "=" * 70)
    print("🌱 STUDYBUDDY SEED DATA SCRIPT")
    print("=" * 70 + "\n")

    # Create session factory
    SessionFactory = get_async_session_factory()

    async with SessionFactory() as session:
        try:
            # Clear existing data
            await clear_existing_data(session)

            # Seed universities
            universities_map = await seed_universities(session)

            # Seed users and verifications
            await seed_users_and_verifications(session, universities_map)

            # Display summary
            await display_summary(session)

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
