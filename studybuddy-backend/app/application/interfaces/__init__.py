"""Application interfaces - Abstract repository interfaces (Ports)."""

from app.application.interfaces.comment_repository import CommentRepository
from app.application.interfaces.community_repository import CommunityRepository
from app.application.interfaces.event_registration_repository import (
    EventRegistrationRepository,
)
from app.application.interfaces.event_repository import EventRepository
from app.application.interfaces.membership_repository import MembershipRepository
from app.application.interfaces.post_repository import PostRepository
from app.application.interfaces.reaction_repository import ReactionRepository
from app.application.interfaces.university_repository import UniversityRepository
from app.application.interfaces.user_repository import UserRepository
from app.application.interfaces.verification_repository import VerificationRepository

__all__ = [
    "CommentRepository",
    "CommunityRepository",
    "EventRegistrationRepository",
    "EventRepository",
    "MembershipRepository",
    "PostRepository",
    "ReactionRepository",
    "UniversityRepository",
    "UserRepository",
    "VerificationRepository",
]
