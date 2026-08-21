from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, Scene, SceneRevision
from ...domain.search_models import FTSDocument, VectorDocument
from .fts_service import count_fts_documents, rebuild_fts_index
from .kg_service import count_kg_edges, count_kg_nodes, rebuild_kg_projection
from .summary_service import list_summaries, rebuild_summaries
from .vector_service import count_vector_documents, rebuild_vector_index


def rebuild_all_indexes(session: Session, project_id: int) -> dict[str, Any]:
    fts_count = rebuild_fts_index(session, project_id)
    vector_count = rebuild_vector_index(session, project_id)
    kg_res = rebuild_kg_projection(session, project_id)
    summary_count = rebuild_summaries(session, project_id)

    return {
        "status": "COMPLETED",
        "project_id": project_id,
        "fts_documents": fts_count,
        "vector_documents": vector_count,
        "kg_nodes": kg_res["nodes"],
        "kg_edges": kg_res["edges"],
        "summaries": summary_count,
    }


def get_all_index_statuses(session: Session, project_id: int) -> dict[str, Any]:
    fts_cnt = count_fts_documents(session, project_id)
    vec_cnt = count_vector_documents(session, project_id)
    kg_nodes_cnt = count_kg_nodes(session, project_id)
    kg_edges_cnt = count_kg_edges(session, project_id)
    sum_cnt = len(list_summaries(session, project_id))

    validation = validate_indexes(session, project_id)

    return {
        "project_id": project_id,
        "overall_status": "HEALTHY" if validation["is_healthy"] else "STALE",
        "fts": {
            "count": fts_cnt,
            "status": "HEALTHY" if fts_cnt > 0 and not validation["stale_fts"] else ("MISSING" if fts_cnt == 0 else "STALE"),
        },
        "vector": {
            "count": vec_cnt,
            "status": "HEALTHY" if vec_cnt > 0 and not validation["stale_vectors"] else ("MISSING" if vec_cnt == 0 else "STALE"),
        },
        "kg": {
            "nodes_count": kg_nodes_cnt,
            "edges_count": kg_edges_cnt,
            "status": "HEALTHY" if kg_nodes_cnt > 0 else "MISSING",
        },
        "summaries": {
            "count": sum_cnt,
            "status": "HEALTHY" if sum_cnt > 0 else "MISSING",
        },
        "details": validation,
    }


def validate_indexes(session: Session, project_id: int) -> dict[str, Any]:
    stale_fts = []
    stale_vectors = []

    scenes = session.scalars(
        select(Scene).join(Chapter).where(Chapter.project_id == project_id)
    ).all()

    for sc in scenes:
        curr_rev_id = sc.current_revision_id or 0

        # Check FTS
        fts_doc = session.scalar(
            select(FTSDocument).where(
                FTSDocument.project_id == project_id,
                FTSDocument.doc_type == "SCENE",
                FTSDocument.source_id == sc.id,
            )
        )
        if fts_doc and fts_doc.source_version != curr_rev_id:
            stale_fts.append({"scene_id": sc.id, "indexed_version": fts_doc.source_version, "current_version": curr_rev_id})

        # Check Vector
        vec_doc = session.scalar(
            select(VectorDocument).where(
                VectorDocument.project_id == project_id,
                VectorDocument.doc_type == "SCENE",
                VectorDocument.source_id == sc.id,
            )
        )
        if vec_doc and vec_doc.source_version != curr_rev_id:
            stale_vectors.append({"scene_id": sc.id, "indexed_version": vec_doc.source_version, "current_version": curr_rev_id})

    is_healthy = len(stale_fts) == 0 and len(stale_vectors) == 0
    return {
        "is_healthy": is_healthy,
        "stale_fts": stale_fts,
        "stale_vectors": stale_vectors,
    }
