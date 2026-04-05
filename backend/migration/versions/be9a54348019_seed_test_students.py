"""seed_test_students

Revision ID: be9a54348019
Revises: b85fb8d56670
Create Date: 2026-04-05 22:25:15.704841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be9a54348019'
down_revision: Union[str, Sequence[str], None] = 'b85fb8d56670'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO student(student_id, first_name, last_name, patronymic, "group")
        VALUES 
            ('285a1389-be7c-43eb-9d76-9afbfb715458', 'Максим', 'Берлет', 'Валерьевич', '3385'),
            ('1de37e3f-1a66-44a7-8bb3-adf1c5565dd5', 'Александр', 'Рудаков', 'Леонидович', '3384')
        ON CONFLICT (student_id) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM student 
        WHERE student_id IN (
            '285a1389-be7c-43eb-9d76-9afbfb715458',
            '1de37e3f-1a66-44a7-8bb3-adf1c5565dd5'
        )
    """)