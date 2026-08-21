from __future__ import annotations

from collections import deque
from typing import Any, Optional
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from ...domain.plot_models import ImpactEdge, ImpactNode


def create_impact_node(
    session: Session,
    project_id: int,
    node_type: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    scene_id: int | None = None,
    revision_id: int | None = None,
    narrative_time: str | None = None,
    content_hash: str | None = None,
) -> ImpactNode:
    node = ImpactNode(
        project_id=project_id,
        node_type=node_type,
        entity_type=entity_type,
        entity_id=entity_id,
        scene_id=scene_id,
        revision_id=revision_id,
        narrative_time=narrative_time,
        content_hash=content_hash,
    )
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def create_impact_edge(
    session: Session,
    project_id: int,
    source_node_id: int,
    target_node_id: int,
    edge_type: str,
    weight: float = 1.0,
) -> ImpactEdge:
    src = session.get(ImpactNode, source_node_id)
    if not src or src.project_id != project_id:
        raise KeyError(f"源节点不存在或不属于当前项目: ID {source_node_id}")

    dst = session.get(ImpactNode, target_node_id)
    if not dst or dst.project_id != project_id:
        raise KeyError(f"目标节点不存在或不属于当前项目: ID {target_node_id}")

    edge = session.scalar(
        select(ImpactEdge).where(
            ImpactEdge.project_id == project_id,
            ImpactEdge.source_node_id == source_node_id,
            ImpactEdge.target_node_id == target_node_id,
            ImpactEdge.edge_type == edge_type,
        )
    )
    if not edge:
        edge = ImpactEdge(
            project_id=project_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            weight=weight,
        )
        session.add(edge)
        session.commit()
        session.refresh(edge)
    return edge


def list_impact_nodes(session: Session, project_id: int, scene_id: int | None = None) -> list[ImpactNode]:
    stmt = select(ImpactNode).where(ImpactNode.project_id == project_id)
    if scene_id is not None:
        stmt = stmt.where(ImpactNode.scene_id == scene_id)
    stmt = stmt.order_by(ImpactNode.id.asc())
    return list(session.scalars(stmt).all())


def list_impact_edges(session: Session, project_id: int) -> list[ImpactEdge]:
    stmt = select(ImpactEdge).where(ImpactEdge.project_id == project_id).order_by(ImpactEdge.id.asc())
    return list(session.scalars(stmt).all())


def propagate_impact(
    session: Session,
    project_id: int,
    changed_node_id: int,
    change_type: str = "MODIFIED",
) -> dict[str, Any]:
    start_node = session.get(ImpactNode, changed_node_id)
    if not start_node or start_node.project_id != project_id:
        return {"affected_scenes": [], "stale_nodes": [], "dependency_paths": [], "total_affected": 0}

    affected_scenes: set[int] = set()
    stale_nodes: list[int] = []
    dependency_paths: list[dict[str, Any]] = []

    queue = deque([changed_node_id])
    visited = set()

    while queue:
        curr_id = queue.popleft()
        if curr_id in visited:
            continue
        visited.add(curr_id)

        edges = session.scalars(
            select(ImpactEdge).where(ImpactEdge.project_id == project_id, ImpactEdge.source_node_id == curr_id)
        ).all()

        for edge in edges:
            target = session.get(ImpactNode, edge.target_node_id)
            if not target:
                continue

            dependency_paths.append({
                "from_node_id": edge.source_node_id,
                "to_node_id": edge.target_node_id,
                "edge_type": edge.edge_type,
            })

            if edge.edge_type == "CONTINUES" and target.node_type == "SCENE_REVISION":
                if target.scene_id:
                    affected_scenes.add(target.scene_id)
                stale_nodes.append(target.id)
            elif edge.edge_type in ["DERIVED_FROM", "AFFECTS", "FORESHADOWS"]:
                stale_nodes.append(target.id)
                if target.scene_id:
                    affected_scenes.add(target.scene_id)
                queue.append(target.id)

    suggestions = []
    if affected_scenes:
        suggestions.append(f"建议重检下游场景: {sorted(list(affected_scenes))}")
    if stale_nodes:
        suggestions.append(f"待复核派生主张与快照节点数: {len(stale_nodes)}")

    return {
        "changed_node_id": changed_node_id,
        "change_type": change_type,
        "affected_scenes": sorted(list(affected_scenes)),
        "stale_nodes": stale_nodes,
        "dependency_paths": dependency_paths,
        "suggestions": suggestions,
        "total_affected": len(affected_scenes) + len(stale_nodes),
    }


def get_scene_impact_report(session: Session, project_id: int, scene_id: int) -> dict[str, Any]:
    nodes = list(session.scalars(select(ImpactNode).where(ImpactNode.project_id == project_id, ImpactNode.scene_id == scene_id)).all())
    node_ids = [n.id for n in nodes]
    edges = list(
        session.scalars(
            select(ImpactEdge).where(
                ImpactEdge.project_id == project_id,
                or_(ImpactEdge.source_node_id.in_(node_ids), ImpactEdge.target_node_id.in_(node_ids)),
            )
        ).all()
    ) if node_ids else []

    is_stale = any(n.node_type == "SCENE_REVISION" for n in nodes) and len(edges) > 0
    return {
        "scene_id": scene_id,
        "status": "LOCALLY_STALE" if is_stale else "OK",
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "nodes": [{"id": n.id, "node_type": n.node_type, "entity_type": n.entity_type, "entity_id": n.entity_id} for n in nodes],
        "suggestions": ["当前场景存在上游依赖变更，建议复核" if is_stale else "场景状态同步正常"],
    }
