"""add created_at to chapters

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("chapters") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))
    
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))


def downgrade() -> None:
    with op.batch_alter_table("scenes") as batch_op:
        batch_op.drop_column("created_at")
    
    with op.batch_alter_table("chapters") as batch_op:
        batch_op.drop_column("created_at")
