"""Stage 10 GraphRAG, communities, global analysis reports and model stats daily schema.

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-21 15:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0013'
down_revision: str | None = '0012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. communities
    op.create_table(
        'communities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('community_type', sa.String(length=32), nullable=False),
        sa.Column('source_entity_type', sa.String(length=32), nullable=True),
        sa.Column('source_entity_id', sa.Integer(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_communities_project', 'communities', ['project_id'])
    op.create_index('idx_communities_type', 'communities', ['community_type'])

    # 2. community_summaries
    op.create_table(
        'community_summaries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('summary_type', sa.String(length=32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('covered_node_ids', sa.JSON(), nullable=True),
        sa.Column('covered_edge_ids', sa.JSON(), nullable=True),
        sa.Column('source_versions', sa.JSON(), nullable=True),
        sa.Column('algorithm_version', sa.String(length=32), nullable=False, server_default='v1'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='VALID'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_community_summaries_community', 'community_summaries', ['community_id'])
    op.create_index('idx_community_summaries_project', 'community_summaries', ['project_id'])

    # 3. graphrag_queries
    op.create_table(
        'graphrag_queries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('query_type', sa.String(length=32), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('communities_used', sa.JSON(), nullable=True),
        sa.Column('token_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_graphrag_queries_project', 'graphrag_queries', ['project_id'])

    # 4. global_analysis_reports
    op.create_table(
        'global_analysis_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('report_type', sa.String(length=32), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('affected_entities', sa.JSON(), nullable=True),
        sa.Column('severity_counts', sa.JSON(), nullable=True),
        sa.Column('token_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_global_analysis_reports_project', 'global_analysis_reports', ['project_id'])
    op.create_index('idx_global_analysis_reports_type', 'global_analysis_reports', ['report_type'])

    # 5. model_stats_daily
    op.create_table(
        'model_stats_daily',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=8), nullable=False),
        sa.Column('task_type', sa.String(length=64), nullable=False),
        sa.Column('total_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('degraded_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('p90_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'date', 'model_name', 'task_type', name='uq_model_stats_daily'),
    )
    op.create_index('idx_model_stats_daily_project', 'model_stats_daily', ['project_id'])
    op.create_index('idx_model_stats_daily_date', 'model_stats_daily', ['date'])


def downgrade() -> None:
    op.drop_table('model_stats_daily')
    op.drop_table('global_analysis_reports')
    op.drop_table('graphrag_queries')
    op.drop_table('community_summaries')
    op.drop_table('communities')
