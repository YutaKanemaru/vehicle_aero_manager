"""add system_id to runs

Revision ID: d1e2f3a4b5c6
Revises: 0c0f562f6ba5
Create Date: 2026-05-03

"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c3b4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(
            sa.Column("system_id", sa.String(36), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("system_id")
