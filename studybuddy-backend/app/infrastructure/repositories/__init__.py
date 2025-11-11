"""Repository implementations - Concrete implementations of repository interfaces."""

from app.infrastructure.repositories.comment_repository import SQLAlchemyCommentRepository
from app.infrastructure.repositories.community_repository import (
    SQLAlchemyCommunityRepository,
)
from app.infrastructure.repositories.event_registration_repository import (
    SQLAlchemyEventRegistrationRepository,
)
from app.infrastructure.repositories.event_repository import SQLAlchemyEventRepository
from app.infrastructure.repositories.membership_repository import (
    SQLAlchemyMembershipRepository,
)
from app.infrastructure.repositories.post_repository import SQLAlchemyPostRepository
from app.infrastructure.repositories.reaction_repository import (
    SQLAlchemyReactionRepository,
)
from app.infrastructure.repositories.university_repository import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.repositories.verification_repository import (
    SQLAlchemyVerificationRepository,
)

__all__ = [
    "SQLAlchemyCommentRepository",
    "SQLAlchemyCommunityRepository",
    "SQLAlchemyEventRegistrationRepository",
    "SQLAlchemyEventRepository",
    "SQLAlchemyMembershipRepository",
    "SQLAlchemyPostRepository",
    "SQLAlchemyReactionRepository",
    "SQLAlchemyUniversityRepository",
    "SQLAlchemyUserRepository",
    "SQLAlchemyVerificationRepository",
]
