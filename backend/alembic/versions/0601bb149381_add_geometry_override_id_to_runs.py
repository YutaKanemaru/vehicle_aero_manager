"""add_geometry_override_id_to_runs

Revision ID: 0601bb149381
Revises: bb5b060716b4
Create Date: 2026-04-22 15:39:00.808068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0601bb149381'
down_revision: Union[str, Sequence[str], None] = 'bb5b060716b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(sa.Column("geometry_override_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_runs_geometry_override_id",
            "geometries",
            ["geometry_override_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_constraint("fk_runs_geometry_override_id", type_="foreignkey")
        batch_op.drop_column("geometry_override_id")
