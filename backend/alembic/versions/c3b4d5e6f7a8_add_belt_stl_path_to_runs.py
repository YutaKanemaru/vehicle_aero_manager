"""add belt_stl_path to runs

Revision ID: c3b4d5e6f7a8
Revises: 0601bb149381
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3b4d5e6f7a8"
down_revision: Union[str, None] = "0c0f562f6ba5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("belt_stl_path", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "belt_stl_path")
