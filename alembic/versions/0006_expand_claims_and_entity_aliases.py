"""Expand claim_candidates and canon_claims, add entity_aliases table.

Revision ID: 0006_expand_claims_and_aliases
Revises: 0005_expand_generation_runs
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005_expand_generation_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Expand claim_candidates
    with op.batch_alter_table("claim_candidates") as batch_op:
        batch_op.add_column(sa.Column("cognitive_subject", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("paragraph_index", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("content_hash", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("hypothesis_tags", sa.JSON(), nullable=True))

    # 2. Expand canon_claims
    with op.batch_alter_table("canon_claims") as batch_op:
        batch_op.add_column(sa.Column("source_candidate_id", sa.Integer(), sa.ForeignKey("claim_candidates.id", name="fk_canon_claims_candidate_id", ondelete="SET NULL"), nullable=True))
        batch_op.add_column(sa.Column("auto_confirmed", sa.Boolean(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("author_decision_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    # 3. Create entity_aliases
    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=False),
        sa.Column("alias_name", sa.String(255), nullable=False),
        sa.Column("alias_type", sa.String(32), nullable=False, server_default="informal"),
        sa.Column("confirmed_by", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("project_id", "canonical_name", "alias_name", name="uq_project_canonical_alias"),
    )
    op.create_index("idx_entity_aliases_project", "entity_aliases", ["project_id"])
    op.create_index("idx_entity_aliases_alias", "entity_aliases", ["alias_name"])


def downgrade() -> None:
    op.drop_index("idx_entity_aliases_alias", table_name="entity_aliases")
    op.drop_index("idx_entity_aliases_project", table_name="entity_aliases")
    op.drop_table("entity_aliases")

    with op.batch_alter_table("canon_claims") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("author_decision_notes")
        batch_op.drop_column("auto_confirmed")
        batch_op.drop_column("source_candidate_id")

    with op.batch_alter_table("claim_candidates") as batch_op:
        batch_op.drop_column("hypothesis_tags")
        batch_op.drop_column("content_hash")
        batch_op.drop_column("paragraph_index")
        batch_op.drop_column("cognitive_subject")
