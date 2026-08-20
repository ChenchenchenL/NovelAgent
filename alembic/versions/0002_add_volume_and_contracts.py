"""Add Volume model and Chapter/Scene contracts.

Revision ID: 0002_add_volume_and_contracts
Revises: 0001_initial
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_volume_and_contracts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "volumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_volumes_project_id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="IDEA"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    with op.batch_alter_table("volumes") as batch_op:
        batch_op.create_index("ix_volumes_project_id", ["project_id"])

    with op.batch_alter_table("chapters") as batch_op:
        batch_op.add_column(sa.Column("volume_id", sa.Integer(), sa.ForeignKey("volumes.id", name="fk_chapters_volume_id"), nullable=True))
        batch_op.add_column(sa.Column("contract", sa.JSON(), nullable=True))
        batch_op.create_index("ix_chapters_volume_id", ["volume_id"])

    with op.batch_alter_table("scenes") as batch_op:
        batch_op.add_column(sa.Column("entry_contract", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("exit_state", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.drop_column("exit_state")
        batch_op.drop_column("entry_contract")

    with op.batch_alter_table("chapters") as batch_op:
        batch_op.drop_index("ix_chapters_volume_id")
        batch_op.drop_constraint("fk_chapters_volume_id", type_="foreignkey")
        batch_op.drop_column("contract")
        batch_op.drop_column("volume_id")

    op.drop_table("volumes")
