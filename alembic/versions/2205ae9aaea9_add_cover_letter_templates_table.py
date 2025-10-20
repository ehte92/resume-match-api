"""add_cover_letter_templates_table

Revision ID: 2205ae9aaea9
Revises: 0e9a78b9950f
Create Date: 2025-10-21 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '2205ae9aaea9'
down_revision: Union[str, None] = '0e9a78b9950f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cover_letter_templates table for template system."""
    op.create_table(
        'cover_letter_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('tone', sa.String(20), nullable=False),
        sa.Column('length', sa.String(20), nullable=False),
        sa.Column('template_text', sa.Text, nullable=False),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for better query performance
    op.create_index('ix_cover_letter_templates_user_id', 'cover_letter_templates', ['user_id'])
    op.create_index('ix_cover_letter_templates_category', 'cover_letter_templates', ['category'])
    op.create_index('ix_cover_letter_templates_is_system', 'cover_letter_templates', ['is_system'])
    op.create_index('ix_cover_letter_templates_tone', 'cover_letter_templates', ['tone'])


def downgrade() -> None:
    """Drop cover_letter_templates table."""
    op.drop_index('ix_cover_letter_templates_tone', table_name='cover_letter_templates')
    op.drop_index('ix_cover_letter_templates_is_system', table_name='cover_letter_templates')
    op.drop_index('ix_cover_letter_templates_category', table_name='cover_letter_templates')
    op.drop_index('ix_cover_letter_templates_user_id', table_name='cover_letter_templates')
    op.drop_table('cover_letter_templates')
