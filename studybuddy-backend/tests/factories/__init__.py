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

    Chat Factories:
        - ChatFactory: Base factory for chats
        - create_direct_chat: Direct one-on-one chats
        - create_group_chat: Group chats
        - create_community_chat: Community chats

    Message Factories:
        - MessageFactory: Base factory for messages
        - create_text_message: Simple text messages
        - create_message_with_attachments: Messages with files
        - create_image_message: Image messages
        - create_conversation: Multi-message conversations

Usage:
    from tests.factories import UserFactory, AdminUserFactory
    from tests.factories import VerificationFactory, UniversityFactory
    from tests.factories import ChatFactory, MessageFactory

    user = UserFactory.build()
    admin = AdminUserFactory.build()
    verification = VerificationFactory.build()
    university = UniversityFactory.build()
    chat = ChatFactory.build()
    message = MessageFactory.build()
"""

from tests.factories.chat_factory import (
    ChatFactory,
    create_chats,
    create_community_chat,
    create_direct_chat,
    create_group_chat,
)
from tests.factories.message_factory import (
    MessageFactory,
    create_conversation,
    create_deleted_message,
    create_image_message,
    create_message_with_attachments,
    create_messages,
    create_text_message,
)
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
    # Chat factories
    "ChatFactory",
    "create_direct_chat",
    "create_group_chat",
    "create_community_chat",
    "create_chats",
    # Message factories
    "MessageFactory",
    "create_text_message",
    "create_message_with_attachments",
    "create_image_message",
    "create_deleted_message",
    "create_messages",
    "create_conversation",
]
