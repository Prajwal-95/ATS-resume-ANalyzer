"""add label to quality_issues

Revision ID: 8f2d73147941
Revises: f26c57d10d3f
Create Date: 2026-10-13 22:06:17.930245

"""
from alembic import op
import sqlalchemy as sa


revision = '8f2d73147941'
down_revision = 'f26c57d10d3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('quality_issues', sa.Column('label', sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column('quality_issues', 'label')
