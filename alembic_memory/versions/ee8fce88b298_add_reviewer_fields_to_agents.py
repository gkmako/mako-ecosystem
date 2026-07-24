"""add reviewer fields to agents

Revision ID: ee8fce88b298
Revises: 92994bc5c657
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee8fce88b298'
down_revision: Union[str, None] = '92994bc5c657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agents', sa.Column('category', sa.String(), nullable=True))
    op.add_column('agents', sa.Column('schema_type', sa.String(), nullable=True))
    op.add_column('agents', sa.Column('reviewer_model_name', sa.String(), nullable=True))
    op.add_column('agents', sa.Column('reviewer_instructions', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('agents', 'reviewer_instructions')
    op.drop_column('agents', 'reviewer_model_name')
    op.drop_column('agents', 'schema_type')
    op.drop_column('agents', 'category')
