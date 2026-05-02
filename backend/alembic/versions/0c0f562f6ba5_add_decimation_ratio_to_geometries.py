"""add_decimation_ratio_to_geometries

Revision ID: 0c0f562f6ba5
Revises: 100503ac21a7
Create Date: 2026-05-02 12:02:18.701904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c0f562f6ba5'
down_revision: Union[str, Sequence[str], None] = '100503ac21a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('geometries', sa.Column('decimation_ratio', sa.Float(), server_default='0.05', nullable=False))


def downgrade() -> None:
    op.drop_column('geometries', 'decimation_ratio')
