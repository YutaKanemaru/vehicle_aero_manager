"""add_case_number_and_run_number

Revision ID: abc6185bae8f
Revises: 8949ff1689b0
Create Date: 2026-04-21 19:00:11.866202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc6185bae8f'
down_revision: Union[str, Sequence[str], None] = '8949ff1689b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)

    # Add case_number to cases if not already present
    cases_cols = {c['name'] for c in inspector.get_columns('cases')}
    if 'case_number' not in cases_cols:
        op.add_column('cases', sa.Column('case_number', sa.String(length=20), nullable=False, server_default=''))

    # Add run_number to runs if not already present
    runs_cols = {c['name'] for c in inspector.get_columns('runs')}
    if 'run_number' not in runs_cols:
        op.add_column('runs', sa.Column('run_number', sa.String(length=20), nullable=False, server_default=''))

    # SQLite does not support ALTER COLUMN directly — use batch_alter_table
    with op.batch_alter_table('runs', recreate='auto') as batch_op:
        batch_op.alter_column('condition_id',
            existing_type=sa.VARCHAR(length=36),
            nullable=False)
        batch_op.create_index('ix_runs_case_id', ['case_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('runs', recreate='auto') as batch_op:
        batch_op.drop_index('ix_runs_case_id')
        batch_op.alter_column('condition_id',
            existing_type=sa.VARCHAR(length=36),
            nullable=True)
    op.drop_column('runs', 'run_number')
    op.drop_column('cases', 'case_number')
