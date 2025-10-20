"""add_tags_to_cover_letters

Revision ID: 0e9a78b9950f
Revises: 78cc40ddbbaa
Create Date: 2025-10-21 00:11:09.935640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '0e9a78b9950f'
down_revision: Union[str, None] = '78cc40ddbbaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tags column to cover_letters table for categorization."""
    # Add tags column as JSONB array (nullable for existing records, default to empty array)
    op.add_column(
        'cover_letters',
        sa.Column('tags', JSONB, nullable=True, server_default='[]')
    )


def downgrade() -> None:
    """Remove tags column from cover_letters table."""
    op.drop_column('cover_letters', 'tags')
