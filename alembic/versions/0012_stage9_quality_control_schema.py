"""Stage 9 Quality control, cliche blacklist, voice fingerprints, and author feedback schema.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-21 14:50:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0012'
down_revision: str | None = '0011'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. beat_contracts
    op.create_table(
        'beat_contracts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('generation_run_id', sa.Integer(), nullable=True),
        sa.Column('required_advancements', sa.JSON(), nullable=True),
        sa.Column('stop_conditions', sa.JSON(), nullable=True),
        sa.Column('target_word_count', sa.Integer(), nullable=True),
        sa.Column('max_word_count', sa.Integer(), nullable=True),
        sa.Column('forbidden_patterns', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('advancements_achieved', sa.JSON(), nullable=True),
        sa.Column('actual_word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id']),
        sa.ForeignKeyConstraint(['generation_run_id'], ['generation_runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_beat_contracts_project', 'beat_contracts', ['project_id'])
    op.create_index('idx_beat_contracts_scene', 'beat_contracts', ['scene_id'])

    # 2. cliche_blacklist
    op.create_table(
        'cliche_blacklist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pattern', sa.String(length=500), nullable=False),
        sa.Column('pattern_type', sa.String(length=16), nullable=False, server_default='EXACT'),
        sa.Column('category', sa.String(length=32), nullable=False, server_default='GENERAL'),
        sa.Column('genre', sa.String(length=32), nullable=True),
        sa.Column('severity', sa.String(length=16), nullable=False, server_default='WARNING'),
        sa.Column('suggestion', sa.String(length=255), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_cliche_blacklist_project', 'cliche_blacklist', ['project_id'])

    # 3. voice_lexicons
    op.create_table(
        'voice_lexicons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('lexicon_type', sa.String(length=16), nullable=False),
        sa.Column('entry_type', sa.String(length=32), nullable=False),
        sa.Column('pattern', sa.String(length=500), nullable=False),
        sa.Column('pattern_type', sa.String(length=16), nullable=False, server_default='EXACT'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_voice_lexicons_project', 'voice_lexicons', ['project_id'])
    op.create_index('idx_voice_lexicons_character', 'voice_lexicons', ['character_id'])

    # 4. voice_fingerprints
    op.create_table(
        'voice_fingerprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('character_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('avg_sentence_length', sa.Float(), nullable=False, server_default='15.0'),
        sa.Column('sentence_length_std', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('colloquial_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('classical_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('honorific_level', sa.String(length=16), nullable=False, server_default='MEDIUM'),
        sa.Column('common_patterns', sa.JSON(), nullable=True),
        sa.Column('preferred_particles', sa.JSON(), nullable=True),
        sa.Column('preferred_address_terms', sa.JSON(), nullable=True),
        sa.Column('preferred_perception_verbs', sa.JSON(), nullable=True),
        sa.Column('forbidden_expressions', sa.JSON(), nullable=True),
        sa.Column('source_revision_ids', sa.JSON(), nullable=True),
        sa.Column('source_text_sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_voice_fingerprints_project', 'voice_fingerprints', ['project_id'])
    op.create_index('idx_voice_fingerprints_character', 'voice_fingerprints', ['character_id'])

    # 5. quality_reports
    op.create_table(
        'quality_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('revision_id', sa.Integer(), nullable=True),
        sa.Column('issues', sa.JSON(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id']),
        sa.ForeignKeyConstraint(['revision_id'], ['scene_revisions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_quality_reports_project', 'quality_reports', ['project_id'])
    op.create_index('idx_quality_reports_scene', 'quality_reports', ['scene_id'])

    # 6. author_feedback
    op.create_table(
        'author_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('issue_type', sa.String(length=32), nullable=False),
        sa.Column('decision', sa.String(length=16), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=True),
        sa.Column('expiry_scene_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('scene_id', sa.Integer(), nullable=True),
        sa.Column('revision_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['expiry_scene_id'], ['scenes.id']),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id']),
        sa.ForeignKeyConstraint(['revision_id'], ['scene_revisions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_author_feedback_project', 'author_feedback', ['project_id'])
    op.create_index('idx_author_feedback_type', 'author_feedback', ['issue_type', 'decision'])


def downgrade() -> None:
    op.drop_table('author_feedback')
    op.drop_table('quality_reports')
    op.drop_table('voice_fingerprints')
    op.drop_table('voice_lexicons')
    op.drop_table('cliche_blacklist')
    op.drop_table('beat_contracts')
