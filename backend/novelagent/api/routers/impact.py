from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import AppState, require_session
from ...application.services import impact_service, project_service
from ..schemas.plot import (
    ImpactEdgeCreate,
    ImpactEdgeView,
    ImpactNodeCreate,
    ImpactNodeView,
    ImpactPropagateRequest,
)

router = APIRouter(tags=["Impact Graph"])


@router.get("/api/impact-graph/nodes", response_model=list[ImpactNodeView])
def list_impact_nodes_endpoint(
    scene_id: int | None = None, state: AppState = Depends(require_session)
) -> list[ImpactNodeView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        nodes = impact_service.list_impact_nodes(db, project.id, scene_id=scene_id)
        return [
            ImpactNodeView(
                id=n.id,
                project_id=n.project_id,
                node_type=n.node_type,
                entity_type=n.entity_type,
                entity_id=n.entity_id,
                scene_id=n.scene_id,
                revision_id=n.revision_id,
                narrative_time=n.narrative_time,
                content_hash=n.content_hash,
                created_at=n.created_at.isoformat() if n.created_at else None,
            )
            for n in nodes
        ]


@router.post("/api/impact-graph/nodes", response_model=ImpactNodeView)
def create_impact_node_endpoint(payload: ImpactNodeCreate, state: AppState = Depends(require_session)) -> ImpactNodeView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        n = impact_service.create_impact_node(
            db,
            project.id,
            node_type=payload.node_type,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            scene_id=payload.scene_id,
            revision_id=payload.revision_id,
            narrative_time=payload.narrative_time,
            content_hash=payload.content_hash,
        )
        return ImpactNodeView(
            id=n.id,
            project_id=n.project_id,
            node_type=n.node_type,
            entity_type=n.entity_type,
            entity_id=n.entity_id,
            scene_id=n.scene_id,
            revision_id=n.revision_id,
            narrative_time=n.narrative_time,
            content_hash=n.content_hash,
            created_at=n.created_at.isoformat() if n.created_at else None,
        )


@router.get("/api/impact-graph/edges", response_model=list[ImpactEdgeView])
def list_impact_edges_endpoint(state: AppState = Depends(require_session)) -> list[ImpactEdgeView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        edges = impact_service.list_impact_edges(db, project.id)
        return [
            ImpactEdgeView(
                id=e.id,
                project_id=e.project_id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                edge_type=e.edge_type,
                weight=e.weight,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
            for e in edges
        ]


@router.post("/api/impact-graph/edges", response_model=ImpactEdgeView)
def create_impact_edge_endpoint(payload: ImpactEdgeCreate, state: AppState = Depends(require_session)) -> ImpactEdgeView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            e = impact_service.create_impact_edge(
                db, project.id, payload.source_node_id, payload.target_node_id, payload.edge_type, payload.weight
            )
            return ImpactEdgeView(
                id=e.id,
                project_id=e.project_id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                edge_type=e.edge_type,
                weight=e.weight,
                created_at=e.created_at.isoformat() if e.created_at else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/impact-graph/propagate")
def propagate_impact_endpoint(payload: ImpactPropagateRequest, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return impact_service.propagate_impact(db, project.id, payload.changed_node_id, payload.change_type)


@router.get("/api/scenes/{scene_id}/impact-report")
def get_scene_impact_report_endpoint(scene_id: int, state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return impact_service.get_scene_impact_report(db, project.id, scene_id)


@router.get("/api/projects/current/impact-summary")
def get_project_impact_summary_endpoint(state: AppState = Depends(require_session)) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        nodes = impact_service.list_impact_nodes(db, project.id)
        edges = impact_service.list_impact_edges(db, project.id)
        return {
            "project_id": project.id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types_distribution": {t: sum(1 for n in nodes if n.node_type == t) for t in set(n.node_type for n in nodes)},
            "edge_types_distribution": {e: sum(1 for ed in edges if ed.edge_type == e) for e in set(ed.edge_type for ed in edges)},
        }
