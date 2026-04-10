"""add_is_linked_to_geometries

Revision ID: b6662ad9ba21
Revises: bd293b1f57fc
Create Date: 2026-04-09 19:32:33.405993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6662ad9ba21'
down_revision: Union[str, Sequence[str], None] = 'bd293b1f57fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('geometries') as batch_op:
        batch_op.add_column(sa.Column('is_linked', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('geometries') as batch_op:
        batch_op.drop_column('is_linked')
