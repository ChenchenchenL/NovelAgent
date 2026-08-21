"""Stage 8 FTS, vector embeddings, KG projection, and summary artifacts schema.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. FTS Documents
    op.create_table(
        "fts_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_fts_docs_project_id"), nullable=False),
        sa.Column("doc_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("modality", sa.String(32), server_default="ACTUAL", nullable=False),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_fts_documents_project", "fts_documents", ["project_id"])
    op.create_index("idx_fts_documents_source", "fts_documents", ["doc_type", "source_id"])

    # Create FTS5 Virtual Table if supported by SQLite
    try:
        op.execute(sa.text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_documents_fts USING fts5(
                content,
                content='fts_documents',
                content_rowid='id',
                tokenize='unicode61'
            )
        """))
    except Exception as exc:
        import logging
        logging.getLogger("alembic.runtime.migration").info("FTS5 virtual table skipped: %s", exc)

    # 2. Vector Documents
    op.create_table(
        "vector_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_vector_docs_project_id"), nullable=False),
        sa.Column("doc_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("modality", sa.String(32), server_default="ACTUAL", nullable=False),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_vector_documents_project", "vector_documents", ["project_id"])

    # 3. Vector Embeddings
    op.create_table(
        "vector_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("vector_documents.id", name="fk_vector_emb_doc_id"), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("vector_data", sa.LargeBinary(), nullable=False),
        sa.Column("vector_dim", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_vector_embeddings_doc", "vector_embeddings", ["document_id"])

    # 4. KG Nodes
    op.create_table(
        "kg_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_kg_nodes_project_id"), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("modality", sa.String(32), server_default="ACTUAL", nullable=False),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_kg_nodes_project", "kg_nodes", ["project_id"])
    op.create_index("idx_kg_nodes_entity", "kg_nodes", ["node_type", "entity_id"])

    # 5. KG Edges
    op.create_table(
        "kg_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_kg_edges_project_id"), nullable=False),
        sa.Column("source_node_id", sa.Integer(), sa.ForeignKey("kg_nodes.id", name="fk_kg_edges_src_id"), nullable=False),
        sa.Column("target_node_id", sa.Integer(), sa.ForeignKey("kg_nodes.id", name="fk_kg_edges_dst_id"), nullable=False),
        sa.Column("edge_type", sa.String(32), nullable=False),
        sa.Column("narrative_time", sa.String(64), nullable=True),
        sa.Column("modality", sa.String(32), server_default="ACTUAL", nullable=False),
        sa.Column("confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("source_scene_id", sa.Integer(), sa.ForeignKey("scenes.id", name="fk_kg_edges_scene_id"), nullable=True),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("project_id", "source_node_id", "target_node_id", "edge_type", "narrative_time", name="uq_kg_edge"),
    )
    op.create_index("idx_kg_edges_project", "kg_edges", ["project_id"])
    op.create_index("idx_kg_edges_source", "kg_edges", ["source_node_id"])
    op.create_index("idx_kg_edges_target", "kg_edges", ["target_node_id"])

    # 6. Summary Artifacts
    op.create_table(
        "summary_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", name="fk_summary_artifacts_project_id"), nullable=False),
        sa.Column("summary_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("covered_node_ids", sa.JSON(), server_default="[]", nullable=True),
        sa.Column("narrative_time_range", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("idx_summary_artifacts_project", "summary_artifacts", ["project_id"])
    op.create_index("idx_summary_artifacts_type", "summary_artifacts", ["summary_type", "source_id"])


def downgrade() -> None:
    op.drop_table("summary_artifacts")
    op.drop_table("kg_edges")
    op.drop_table("kg_nodes")
    op.drop_table("vector_embeddings")
    op.drop_table("vector_documents")
    try:
        op.execute(sa.text("DROP TABLE IF EXISTS fts_documents_fts"))
    except Exception:
        pass
    op.drop_table("fts_documents")
