"""remove_template_id_from_geometry_assemblies

Revision ID: bb5b060716b4
Revises: a1b2c3d4e5f6
Create Date: 2026-04-21 21:33:57.093106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb5b060716b4'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite requires batch mode to drop columns / foreign keys
    with op.batch_alter_table('geometry_assemblies', schema=None) as batch_op:
        batch_op.drop_column('template_id')


def downgrade() -> None:
    with op.batch_alter_table('geometry_assemblies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('template_id', sa.VARCHAR(length=36), nullable=True))
