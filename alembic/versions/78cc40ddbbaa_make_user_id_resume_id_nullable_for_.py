"""make_user_id_resume_id_nullable_for_guest_analyses

Revision ID: 78cc40ddbbaa
Revises: 002879a20a52
Create Date: 2025-10-16 17:04:39.261717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78cc40ddbbaa'
down_revision: Union[str, None] = '002879a20a52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make user_id and resume_id nullable for guest analyses
    op.alter_column('resume_analyses', 'user_id',
               existing_type=sa.UUID(),
               nullable=True)
    op.alter_column('resume_analyses', 'resume_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    # Revert user_id and resume_id to non-nullable
    # Note: This will fail if there are NULL values in the database
    op.alter_column('resume_analyses', 'user_id',
               existing_type=sa.UUID(),
               nullable=False)
    op.alter_column('resume_analyses', 'resume_id',
               existing_type=sa.UUID(),
               nullable=False)
