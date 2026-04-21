"""add_on_delete_cascade_to_runs_case_id

Revision ID: dfbd88e1bf8d
Revises: 4a08074381f4
Create Date: 2026-04-21 11:44:36.403962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfbd88e1bf8d'
down_revision: Union[str, Sequence[str], None] = '4a08074381f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite does not support ALTER COLUMN or named FK constraints.
    # batch_alter_table with recreate="always" rebuilds the table with the new FK.
    with op.batch_alter_table('runs', schema=None, recreate='always') as batch_op:
        batch_op.create_foreign_key(
            'fk_runs_case_id', 'cases', ['case_id'], ['id'], ondelete='CASCADE'
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('runs', schema=None, recreate='always') as batch_op:
        batch_op.drop_constraint('fk_runs_case_id', type_='foreignkey')
        batch_op.create_foreign_key(
            None, 'cases', ['case_id'], ['id']
        )
