"""add_parent_case_id_to_cases

Revision ID: 100503ac21a7
Revises: 0601bb149381
Create Date: 2026-04-23 13:27:15.662570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '100503ac21a7'
down_revision: Union[str, Sequence[str], None] = '0601bb149381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add parent_case_id (nullable self-FK) to cases table."""
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(sa.Column("parent_case_id", sa.String(36), nullable=True))
        batch_op.create_foreign_key(
            "fk_cases_parent_case_id",
            "cases",
            ["parent_case_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_constraint("fk_cases_parent_case_id", type_="foreignkey")
        batch_op.drop_column("parent_case_id")
