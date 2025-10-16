"""add_performance_indexes

Revision ID: 002879a20a52
Revises: 950fb2789d0d
Create Date: 2025-10-16 02:46:25.953118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002879a20a52'
down_revision: Union[str, None] = '950fb2789d0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for common queries."""
    # Index for listing user's resumes sorted by date (most common query)
    op.create_index(
        'idx_resumes_user_created',
        'resumes',
        ['user_id', sa.text('created_at DESC')],
        unique=False
    )

    # Index for listing user's analyses sorted by date
    op.create_index(
        'idx_analyses_user_created',
        'resume_analyses',
        ['user_id', sa.text('created_at DESC')],
        unique=False
    )

    # Index for getting analyses by resume_id
    op.create_index(
        'idx_analyses_resume',
        'resume_analyses',
        ['resume_id'],
        unique=False
    )

    # Index for duplicate detection by file hash
    op.create_index(
        'idx_resumes_hash',
        'resumes',
        ['file_hash'],
        unique=False
    )

    # Index for email lookup during login (if not already exists)
    op.create_index(
        'idx_users_email',
        'users',
        ['email'],
        unique=True
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_resumes_hash', table_name='resumes')
    op.drop_index('idx_analyses_resume', table_name='resume_analyses')
    op.drop_index('idx_analyses_user_created', table_name='resume_analyses')
    op.drop_index('idx_resumes_user_created', table_name='resumes')
