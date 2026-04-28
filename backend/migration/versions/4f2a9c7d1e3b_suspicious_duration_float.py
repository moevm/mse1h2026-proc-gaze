"""suspicious_duration_float

Revision ID: 4f2a9c7d1e3b
Revises: a0bde7075dd7
Create Date: 2026-04-27 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f2a9c7d1e3b'
down_revision: Union[str, Sequence[str], None] = 'a0bde7075dd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'suspicious_interval',
        'duration',
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
        schema='public',
    )


def downgrade() -> None:
    op.alter_column(
        'suspicious_interval',
        'duration',
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
        schema='public',
    )
