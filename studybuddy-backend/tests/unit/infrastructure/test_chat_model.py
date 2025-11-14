"""Unit tests for Chat database model.

Tests the Chat SQLAlchemy model structure, fields, constraints, and relationships.
Following TDD - these tests will fail until implementation is complete.
"""

from uuid import uuid4

from sqlalchemy import inspect

from app.domain.enums.chat_type import ChatType
from app.infrastructure.database.base import Base, TimestampMixin
from app.infrastructure.database.models.chat import Chat


class TestChatModel:
    """Test Chat database model structure and behavior."""

    def test_chat_inherits_from_base(self):
        """Test that Chat inherits from SQLAlchemy Base."""
        assert issubclass(Chat, Base)

    def test_chat_inherits_from_timestamp_mixin(self):
        """Test that Chat inherits from TimestampMixin for timestamps."""
        assert issubclass(Chat, TimestampMixin)

    def test_chat_has_correct_tablename(self):
        """Test that Chat maps to 'chats' table."""
        assert Chat.__tablename__ == "chats"

    def test_chat_has_id_column(self):
        """Test that Chat has id column as UUID primary key."""
        mapper = inspect(Chat)
        id_col = mapper.columns["id"]

        assert id_col.primary_key is True
        assert id_col.nullable is False
        # Column type should be UUID
        assert "UUID" in str(id_col.type)

    def test_chat_has_type_column(self):
        """Test that Chat has type column."""
        mapper = inspect(Chat)
        type_col = mapper.columns["type"]

        assert type_col.nullable is False
        assert str(type_col.type) == "String"

    def test_chat_has_name_column(self):
        """Test that Chat has name column."""
        mapper = inspect(Chat)
        name_col = mapper.columns["name"]

        assert name_col.nullable is False
        assert str(name_col.type) == "String"

    def test_chat_has_community_id_column(self):
        """Test that Chat has community_id column as nullable foreign key."""
        mapper = inspect(Chat)
        community_id_col = mapper.columns["community_id"]

        assert community_id_col.nullable is True
        # Column type should be UUID
        assert "UUID" in str(community_id_col.type)

    def test_chat_has_created_at_column(self):
        """Test that Chat has created_at column from TimestampMixin."""
        mapper = inspect(Chat)
        created_at_col = mapper.columns["created_at"]

        assert created_at_col.nullable is False
        assert str(created_at_col.type) == "DateTime(timezone=True)"

    def test_chat_has_updated_at_column(self):
        """Test that Chat has updated_at column from TimestampMixin."""
        mapper = inspect(Chat)
        updated_at_col = mapper.columns["updated_at"]

        assert updated_at_col.nullable is False
        assert str(updated_at_col.type) == "DateTime(timezone=True)"

    def test_chat_can_be_created_with_required_fields(self):
        """Test that Chat can be instantiated with required fields."""
        chat_id = uuid4()
        chat = Chat(
            id=chat_id,
            type=ChatType.DIRECT,
            name="Test Direct Chat",
        )

        assert chat.id == chat_id
        assert chat.type == ChatType.DIRECT
        assert chat.name == "Test Direct Chat"
        assert chat.community_id is None

    def test_chat_can_be_created_with_community_id(self):
        """Test that Chat can be instantiated with community_id."""
        chat_id = uuid4()
        community_id = uuid4()
        chat = Chat(
            id=chat_id,
            type=ChatType.COMMUNITY,
            name="Community Chat",
            community_id=community_id,
        )

        assert chat.id == chat_id
        assert chat.type == ChatType.COMMUNITY
        assert chat.name == "Community Chat"
        assert chat.community_id == community_id

    def test_chat_type_default_value(self):
        """Test that Chat type defaults to DIRECT."""
        chat = Chat(
            id=uuid4(),
            name="Test Chat",
        )

        assert chat.type == ChatType.DIRECT.value  # Should be the string value

    def test_chat_relationships(self):
        """Test that Chat has proper foreign key relationships."""
        mapper = inspect(Chat)
        community_id_col = mapper.columns["community_id"]

        # Check if foreign key exists
        foreign_keys = list(community_id_col.foreign_keys)
        assert len(foreign_keys) == 1
        fk = foreign_keys[0]
        assert fk.column.table.name == "communities"
        assert fk.column.name == "id"
