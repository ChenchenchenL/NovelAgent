from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import AppState, require_session
from ...application.services import kg_service, project_service
from ..schemas.search import KGEdgeView, KGNodeView, KGPathQueryRequest

router = APIRouter(tags=["Knowledge Graph Projections"])


@router.get("/api/kg/nodes", response_model=list[KGNodeView])
def list_kg_nodes_endpoint(
    node_type: str | None = None,
    state: AppState = Depends(require_session),
) -> list[KGNodeView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        nodes = kg_service.list_kg_nodes(db, project.id, node_type=node_type)
        return [
            KGNodeView(
                id=n.id,
                project_id=n.project_id,
                node_type=n.node_type,
                entity_id=n.entity_id,
                name=n.name,
                narrative_time=n.narrative_time,
                modality=n.modality,
                confirmed=n.confirmed,
            )
            for n in nodes
        ]


@router.get("/api/kg/edges", response_model=list[KGEdgeView])
def list_kg_edges_endpoint(
    edge_type: str | None = None,
    state: AppState = Depends(require_session),
) -> list[KGEdgeView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        edges = kg_service.list_kg_edges(db, project.id, edge_type=edge_type)
        return [
            KGEdgeView(
                id=e.id,
                project_id=e.project_id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                edge_type=e.edge_type,
                narrative_time=e.narrative_time,
                modality=e.modality,
                confirmed=e.confirmed,
                source_scene_id=e.source_scene_id,
                weight=e.weight,
            )
            for e in edges
        ]


@router.post("/api/kg/path")
def query_kg_path_endpoint(
    payload: KGPathQueryRequest,
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return kg_service.find_relationship_path(
            db,
            project_id=project.id,
            source_node_id=payload.source_node_id,
            target_node_id=payload.target_node_id,
            max_hops=payload.max_hops,
            edge_types=payload.edge_types,
        )


@router.get("/api/kg/neighbors")
def query_kg_neighbors_endpoint(
    node_id: int = Query(...),
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return kg_service.find_neighbors(db, project.id, node_id)
