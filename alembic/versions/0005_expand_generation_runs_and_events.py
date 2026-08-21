"""Expand generation_runs and model_invocations, add generation_run_events table.

Revision ID: 0005_expand_generation_runs
Revises: 0004_expand_generation_workspace
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_expand_generation_runs"
down_revision = "0004_expand_generation_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Expand model_invocations
    with op.batch_alter_table("model_invocations") as batch_op:
        batch_op.add_column(sa.Column("endpoint", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("token_usage", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("duration_ms", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("degraded_to", sa.String(8), nullable=True))

    # 2. Expand generation_runs
    with op.batch_alter_table("generation_runs") as batch_op:
        batch_op.add_column(sa.Column("task_type", sa.String(64), nullable=False, server_default="paragraph_generation"))
        batch_op.add_column(sa.Column("request_snapshot", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("response_snapshot", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("model_tier", sa.String(8), nullable=False, server_default="T3"))
        batch_op.add_column(sa.Column("actual_model", sa.String(255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("context_manifest", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("token_usage", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("error_message", sa.String(1024), nullable=True))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("retries", sa.Integer(), nullable=False, server_default="0"))

    # 3. Create generation_run_events table
    op.create_table(
        "generation_run_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("run_id", "sequence_number", name="uq_generation_run_events_seq"),
    )
    op.create_index("idx_gre_run_id", "generation_run_events", ["run_id"])


def downgrade() -> None:
    op.drop_index("idx_gre_run_id", table_name="generation_run_events")
    op.drop_table("generation_run_events")

    with op.batch_alter_table("generation_runs") as batch_op:
        batch_op.drop_column("retries")
        batch_op.drop_column("completed_at")
        batch_op.drop_column("started_at")
        batch_op.drop_column("error_message")
        batch_op.drop_column("token_usage")
        batch_op.drop_column("context_manifest")
        batch_op.drop_column("actual_model")
        batch_op.drop_column("model_tier")
        batch_op.drop_column("response_snapshot")
        batch_op.drop_column("request_snapshot")
        batch_op.drop_column("task_type")

    with op.batch_alter_table("model_invocations") as batch_op:
        batch_op.drop_column("degraded_to")
        batch_op.drop_column("duration_ms")
        batch_op.drop_column("token_usage")
        batch_op.drop_column("endpoint")
