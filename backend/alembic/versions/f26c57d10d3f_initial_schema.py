"""initial schema

Revision ID: f26c57d10d3f
Revises:
Create Date: 2026-10-13 21:57:31.649451

"""
from alembic import op
import sqlalchemy as sa


revision = 'f26c57d10d3f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Analysis table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('resume_filename', sa.String(length=500), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=True),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('job_title', sa.String(length=500), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('structured_resume', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_analyses_user_id', 'analyses', ['user_id'])
    op.create_index('ix_analyses_created_at', 'analyses', ['created_at'])
    op.create_index('ix_analyses_user_created', 'analyses', ['user_id', 'created_at'])

    # Analysis scores
    op.create_table(
        'analysis_scores',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('max_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_analysis_scores_analysis_id', 'analysis_scores', ['analysis_id'])

    # Matched keywords
    op.create_table(
        'matched_keywords',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_matched_kw_analysis', 'matched_keywords', ['analysis_id'])

    # Missing keywords
    op.create_table(
        'missing_keywords',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=255), nullable=False),
        sa.Column('importance', sa.String(length=50), nullable=False, server_default="'medium'"),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_missing_kw_analysis', 'missing_keywords', ['analysis_id'])

    # Skill matches
    op.create_table(
        'skill_matches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=255), nullable=False),
        sa.Column('match_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_skill_matches_analysis_id', 'skill_matches', ['analysis_id'])

    # Suggestions
    op.create_table(
        'suggestions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default="'medium'"),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_suggestions_analysis_id', 'suggestions', ['analysis_id'])

    # Quality issues
    op.create_table(
        'quality_issues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quality_issues_analysis_id', 'quality_issues', ['analysis_id'])


def downgrade() -> None:
    op.drop_table('quality_issues')
    op.drop_table('suggestions')
    op.drop_table('skill_matches')
    op.drop_table('missing_keywords')
    op.drop_table('matched_keywords')
    op.drop_table('analysis_scores')
    op.drop_table('analyses')
    op.drop_table('users')
