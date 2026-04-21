"""add template, map, and case folders

Revision ID: a1b2c3d4e5f6
Revises: ff0265eeeb01
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ff0265eeeb01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── template_folders ───────────────────────────────────────────────────
    op.create_table(
        "template_folders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── condition_map_folders ──────────────────────────────────────────────
    op.create_table(
        "condition_map_folders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── case_folders ───────────────────────────────────────────────────────
    op.create_table(
        "case_folders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── templates: add folder_id ───────────────────────────────────────────
    with op.batch_alter_table("templates") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_templates_folder_id", ["folder_id"])

    # condition_maps: add folder_id
    with op.batch_alter_table("condition_maps") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_condition_maps_folder_id", ["folder_id"])

    # cases: add folder_id
    with op.batch_alter_table("cases") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_cases_folder_id", ["folder_id"])


def downgrade() -> None:
    with op.batch_alter_table("cases") as batch_op:
        batch_op.drop_index("ix_cases_folder_id")
        batch_op.drop_column("folder_id")

    with op.batch_alter_table("condition_maps") as batch_op:
        batch_op.drop_index("ix_condition_maps_folder_id")
        batch_op.drop_column("folder_id")

    with op.batch_alter_table("templates") as batch_op:
        batch_op.drop_index("ix_templates_folder_id")
        batch_op.drop_column("folder_id")

    op.drop_table("case_folders")
    op.drop_table("condition_map_folders")
    op.drop_table("template_folders")
