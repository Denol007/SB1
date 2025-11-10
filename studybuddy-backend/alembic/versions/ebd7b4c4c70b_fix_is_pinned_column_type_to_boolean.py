"""fix is_pinned column type to boolean

Revision ID: ebd7b4c4c70b
Revises: 6ff0160ab230
Create Date: 2025-11-10 18:05:45.947997

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ebd7b4c4c70b"
down_revision: Union[str, Sequence[str], None] = "6ff0160ab230"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change is_pinned column type from VARCHAR to BOOLEAN
    op.alter_column(
        "posts",
        "is_pinned",
        type_=sa.Boolean(),
        existing_type=sa.String(),
        existing_nullable=False,
        existing_server_default=sa.text("false"),
        postgresql_using="is_pinned::boolean",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Change is_pinned column type back to VARCHAR
    op.alter_column(
        "posts",
        "is_pinned",
        type_=sa.String(),
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default=sa.text("false"),
        postgresql_using="is_pinned::text",
    )
