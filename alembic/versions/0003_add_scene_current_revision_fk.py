"""Add foreign key constraint on scenes.current_revision_id.

Revision ID: 0003_add_scene_current_revision_fk
Revises: 0002_add_volume_and_contracts
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_add_scene_current_revision_fk"
down_revision = "0002_add_volume_and_contracts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.create_foreign_key(
            "fk_scenes_current_revision_id",
            "scene_revisions",
            ["current_revision_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.drop_constraint("fk_scenes_current_revision_id", type_="foreignkey")
