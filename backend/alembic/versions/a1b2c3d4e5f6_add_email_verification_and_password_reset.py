"""add email verification and password reset fields to users

Revision ID: a1b2c3d4e5f6
Revises: 8f2d73147941
Create Date: 2026-10-19T11:27:55.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '8f2d73147941'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('verification_token_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_reset_token_expires_at')
    op.drop_column('users', 'password_reset_token_hash')
    op.drop_column('users', 'verification_token_expires_at')
    op.drop_column('users', 'verification_token_hash')
    op.drop_column('users', 'email_verified')