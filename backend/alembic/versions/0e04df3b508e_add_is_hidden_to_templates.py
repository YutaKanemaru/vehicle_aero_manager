"""add_is_hidden_to_templates

Revision ID: 0e04df3b508e
Revises: b6662ad9ba21
Create Date: 2026-04-09 20:13:20.051859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e04df3b508e'
down_revision: Union[str, Sequence[str], None] = 'b6662ad9ba21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('templates', sa.Column('is_hidden', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('templates', 'is_hidden')
