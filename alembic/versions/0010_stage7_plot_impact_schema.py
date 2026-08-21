"""Stage 7 plot threads, foreshadowing, transition, and impact graph schema.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Plot Threads
    op.create_table(
        "plot_threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_plot_threads_project_id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("thread_type", sa.String(32), server_default="MAIN", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="1", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_plot_threads_start_scene_id"), nullable=True),
        sa.Column("end_scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_plot_threads_end_scene_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_plot_threads_project", "plot_threads", ["project_id"])

    # 2. Plot Events
    op.create_table(
        "plot_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plot_thread_id", sa.Integer(), sa.ForeignKey("plot_threads.id", name="fk_plot_events_plot_thread_id"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_plot_events_scene_id"), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_plot_events_thread", "plot_events", ["plot_thread_id"])
    op.create_index("idx_plot_events_scene", "plot_events", ["scene_id"])

    # 3. Foreshadowings
    op.create_table(
        "foreshadowings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_foreshadowings_project_id"), nullable=False),
        sa.Column("plot_thread_id", sa.Integer(), sa.ForeignKey("plot_threads.id", name="fk_foreshadowings_plot_thread_id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), server_default="SETUP", nullable=False),
        sa.Column("priority", sa.String(16), server_default="SUBPLOT", nullable=False),
        sa.Column("target_chapter_start", sa.Integer(), nullable=True),
        sa.Column("target_chapter_end", sa.Integer(), nullable=True),
        sa.Column("earliest_trigger_chapter", sa.Integer(), nullable=True),
        sa.Column("latest_payoff_chapter", sa.Integer(), nullable=True),
        sa.Column("trigger_condition_type", sa.String(32), nullable=True),
        sa.Column("trigger_condition_params", sa.JSON(), nullable=True),
        sa.Column("visibility", sa.String(32), server_default="AUTHOR", nullable=False),
        sa.Column("visible_to_character_id", sa.Integer(), sa.ForeignKey("characters.id", name="fk_foreshadowings_char_id"), nullable=True),
        sa.Column("anchors", sa.JSON(), server_default="[]", nullable=True),
        sa.Column("setup_scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_foreshadowings_setup_scene_id"), nullable=False),
        sa.Column("payoff_scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_foreshadowings_payoff_scene_id"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_foreshadowings_project", "foreshadowings", ["project_id"])
    op.create_index("idx_foreshadowings_setup_scene", "foreshadowings", ["setup_scene_id"])

    # 4. Impact Nodes
    op.create_table(
        "impact_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_impact_nodes_project_id"), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_impact_nodes_scene_id"), nullable=True),
        sa.Column("revision_id", sa.Integer(), sa.ForeignKey("scene_revisions.id", name="fk_impact_nodes_revision_id"), nullable=True),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_impact_nodes_project", "impact_nodes", ["project_id"])
    op.create_index("idx_impact_nodes_scene", "impact_nodes", ["scene_id"])

    # 5. Impact Edges
    op.create_table(
        "impact_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_impact_edges_project_id"), nullable=False),
        sa.Column("source_node_id", sa.Integer(), sa.ForeignKey("impact_nodes.id", name="fk_impact_edges_source_node_id"), nullable=False),
        sa.Column("target_node_id", sa.Integer(), sa.ForeignKey("impact_nodes.id", name="fk_impact_edges_target_node_id"), nullable=False),
        sa.Column("edge_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("project_id", "source_node_id", "target_node_id", "edge_type", name="uq_impact_edge"),
    )
    op.create_index("idx_impact_edges_project", "impact_edges", ["project_id"])
    op.create_index("idx_impact_edges_source", "impact_edges", ["source_node_id"])
    op.create_index("idx_impact_edges_target", "impact_edges", ["target_node_id"])


def downgrade() -> None:
    op.drop_table("impact_edges")
    op.drop_table("impact_nodes")
    op.drop_table("foreshadowings")
    op.drop_table("plot_events")
    op.drop_table("plot_threads")
