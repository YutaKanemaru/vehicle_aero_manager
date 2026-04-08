"""add_geometry_folders_and_folder_id_to_geometries

Revision ID: d4be3f102eac
Revises: f46197300d43
Create Date: 2026-04-08 20:49:03.611904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4be3f102eac'
down_revision: Union[str, Sequence[str], None] = 'f46197300d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('geometry_folders',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_by', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # SQLite では ALTER TABLE で FK 制約を追加できないため batch モードを使用
    with op.batch_alter_table('geometries') as batch_op:
        batch_op.add_column(sa.Column('folder_id', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key('fk_geometries_folder_id', 'geometry_folders', ['folder_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('geometries') as batch_op:
        batch_op.drop_constraint('fk_geometries_folder_id', type_='foreignkey')
        batch_op.drop_column('folder_id')
    op.drop_table('geometry_folders')
