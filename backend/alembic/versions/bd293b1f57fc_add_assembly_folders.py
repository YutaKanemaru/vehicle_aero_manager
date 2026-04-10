"""add_assembly_folders

Revision ID: bd293b1f57fc
Revises: 21095b2b7bda
Create Date: 2026-04-09 18:56:34.377834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd293b1f57fc'
down_revision: Union[str, Sequence[str], None] = '21095b2b7bda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. assembly_folders テーブルを新規作成
    op.create_table(
        'assembly_folders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. geometry_assemblies に folder_id を追加（batch_alter_table — SQLite FK 制約対応）
    with op.batch_alter_table('geometry_assemblies') as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            'fk_geometry_assemblies_folder_id',
            'assembly_folders',
            ['folder_id'], ['id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('geometry_assemblies') as batch_op:
        batch_op.drop_constraint('fk_geometry_assemblies_folder_id', type_='foreignkey')
        batch_op.drop_column('folder_id')

    op.drop_table('assembly_folders')
