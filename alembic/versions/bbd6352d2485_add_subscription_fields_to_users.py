"""add_subscription_fields_to_users

Revision ID: bbd6352d2485
Revises: 2205ae9aaea9
Create Date: 2025-10-21 17:59:58.183154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbd6352d2485'
down_revision: Union[str, None] = '2205ae9aaea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
