"""add_file_hash_to_resumes

Revision ID: 226b0b0920f1
Revises: 814393ea27ff
Create Date: 2025-10-16 00:31:42.808429

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '226b0b0920f1'
down_revision: Union[str, None] = '814393ea27ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add file_hash column and index to resumes table for deduplication."""
    # Add file_hash column (nullable for existing records)
    op.add_column('resumes', sa.Column('file_hash', sa.String(64), nullable=True))

    # Add composite index on (user_id, file_hash) for fast duplicate lookup
    op.create_index(
        'idx_resumes_user_hash',
        'resumes',
        ['user_id', 'file_hash'],
        unique=False
    )


def downgrade() -> None:
    """Remove file_hash column and index from resumes table."""
    # Drop index first
    op.drop_index('idx_resumes_user_hash', 'resumes')

    # Drop column
    op.drop_column('resumes', 'file_hash')
