"""make geometries.decimation_ratio nullable (None = skip GLB)

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-03

"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("geometries") as batch_op:
        batch_op.alter_column(
            "decimation_ratio",
            existing_type=sa.Float(),
            nullable=True,
            server_default=None,
        )


def downgrade() -> None:
    # Restore NOT NULL; fill any nulls with 0.05 first
    op.execute("UPDATE geometries SET decimation_ratio = 0.05 WHERE decimation_ratio IS NULL")
    with op.batch_alter_table("geometries") as batch_op:
        batch_op.alter_column(
            "decimation_ratio",
            existing_type=sa.Float(),
            nullable=False,
            server_default="0.05",
        )
