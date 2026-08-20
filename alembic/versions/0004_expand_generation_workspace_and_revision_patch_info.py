"""Expand generation_workspaces and add patch_info to scene_revisions.

Revision ID: 0004_expand_generation_workspace
Revises: 0003_add_scene_current_revision_fk
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_expand_generation_workspace"
down_revision = "0003_add_scene_current_revision_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scene_revisions") as batch_op:
        batch_op.add_column(sa.Column("patch_info", sa.JSON(), nullable=True))

    with op.batch_alter_table("generation_workspaces") as batch_op:
        batch_op.drop_column("content")
        batch_op.add_column(sa.Column("draft_content", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("cursor_position", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("selection_start", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("selection_end", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("auto_save_snapshot", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("undo_stack", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("redo_stack", sa.JSON(), nullable=True))
        batch_op.create_unique_constraint("uq_generation_workspaces_scene_id", ["scene_id"])


def downgrade() -> None:
    with op.batch_alter_table("generation_workspaces") as batch_op:
        batch_op.drop_constraint("uq_generation_workspaces_scene_id", type_="unique")
        batch_op.drop_column("redo_stack")
        batch_op.drop_column("undo_stack")
        batch_op.drop_column("auto_save_snapshot")
        batch_op.drop_column("selection_end")
        batch_op.drop_column("selection_start")
        batch_op.drop_column("cursor_position")
        batch_op.drop_column("draft_content")
        batch_op.add_column(sa.Column("content", sa.Text(), nullable=False, server_default=""))

    with op.batch_alter_table("scene_revisions") as batch_op:
        batch_op.drop_column("patch_info")
