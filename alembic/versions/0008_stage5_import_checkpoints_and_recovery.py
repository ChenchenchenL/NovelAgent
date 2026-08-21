"""Stage 5 import checkpoints and cross media recovery schema.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batch_index", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("batch_info", sa.JSON(), nullable=True),
        sa.Column("items_imported", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("job_id", "batch_index", name="uq_import_checkpoints_job_batch"),
    )
    op.create_index("ix_import_checkpoints_job_id", "import_checkpoints", ["job_id"])

    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.add_column(sa.Column("total_files", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("total_batches", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("batch_size", sa.Integer(), server_default="10", nullable=False))
        batch_op.add_column(sa.Column("auto_extract", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
        batch_op.add_column(sa.Column("error_summary", sa.Text(), nullable=True))

    with op.batch_alter_table("commit_journal") as batch_op:
        batch_op.add_column(sa.Column("file_size", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("encoding", sa.String(32), server_default="utf-8", nullable=False))
        batch_op.add_column(sa.Column("recovery_attempts", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("commit_journal") as batch_op:
        batch_op.drop_column("recovery_attempts")
        batch_op.drop_column("encoding")
        batch_op.drop_column("file_size")

    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.drop_column("error_summary")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("completed_at")
        batch_op.drop_column("started_at")
        batch_op.drop_column("auto_extract")
        batch_op.drop_column("batch_size")
        batch_op.drop_column("total_batches")
        batch_op.drop_column("total_files")

    op.drop_index("ix_import_checkpoints_job_id", table_name="import_checkpoints")
    op.drop_table("import_checkpoints")
