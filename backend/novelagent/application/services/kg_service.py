from __future__ import annotations

from collections import deque
from typing import Any, Optional
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from ...domain.continuity_models import (
    Character,
    LocationEntity,
    MovementEvent,
    NarrativeSecret,
    RelationshipEvent,
)
from ...domain.models import ItemEntity, ItemEvent
from ...domain.plot_models import Foreshadowing
from ...domain.search_models import KGEdge, KGNode


def get_or_create_kg_node(
    session: Session,
    project_id: int,
    node_type: str,
    entity_id: int,
    name: str,
    narrative_time: str | None = None,
    modality: str = "ACTUAL",
    confirmed: bool = False,
    flush_only: bool = False,
) -> KGNode:
    node = session.scalar(
        select(KGNode).where(
            KGNode.project_id == project_id,
            KGNode.node_type == node_type,
            KGNode.entity_id == entity_id,
        )
    )
    if not node:
        node = KGNode(
            project_id=project_id,
            node_type=node_type,
            entity_id=entity_id,
            name=name.strip(),
            narrative_time=narrative_time,
            modality=modality,
            confirmed=confirmed,
        )
        session.add(node)
        session.flush()
        if not flush_only:
            session.commit()
            session.refresh(node)
    else:
        if name and node.name != name.strip():
            node.name = name.strip()
            session.flush()
            if not flush_only:
                session.commit()
                session.refresh(node)
    return node


def create_kg_edge(
    session: Session,
    project_id: int,
    source_node_id: int,
    target_node_id: int,
    edge_type: str,
    narrative_time: str | None = None,
    modality: str = "ACTUAL",
    confirmed: bool = False,
    source_scene_id: int | None = None,
    weight: float = 1.0,
    flush_only: bool = False,
) -> KGEdge:
    src = session.get(KGNode, source_node_id)
    if not src or src.project_id != project_id:
        raise KeyError(f"源节点不存在或不属于项目: ID {source_node_id}")
    dst = session.get(KGNode, target_node_id)
    if not dst or dst.project_id != project_id:
        raise KeyError(f"目标节点不存在或不属于项目: ID {target_node_id}")

    edge = session.scalar(
        select(KGEdge).where(
            KGEdge.project_id == project_id,
            KGEdge.source_node_id == source_node_id,
            KGEdge.target_node_id == target_node_id,
            KGEdge.edge_type == edge_type,
            KGEdge.narrative_time == narrative_time,
        )
    )
    if not edge:
        edge = KGEdge(
            project_id=project_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            narrative_time=narrative_time,
            modality=modality,
            confirmed=confirmed,
            source_scene_id=source_scene_id,
            weight=weight,
        )
        session.add(edge)
        session.flush()
        if not flush_only:
            session.commit()
            session.refresh(edge)
    return edge


def find_relationship_path(
    session: Session,
    project_id: int,
    source_node_id: int,
    target_node_id: int,
    max_hops: int = 3,
    edge_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    if source_node_id == target_node_id:
        return []

    src = session.get(KGNode, source_node_id)
    dst = session.get(KGNode, target_node_id)
    if not src or not dst or src.project_id != project_id or dst.project_id != project_id:
        return []

    queue: deque[tuple[int, list[dict[str, Any]]]] = deque([(source_node_id, [])])
    visited: set[int] = {source_node_id}

    while queue:
        curr_node, path = queue.popleft()
        if len(path) >= max_hops:
            continue

        stmt = select(KGEdge).where(
            KGEdge.project_id == project_id,
            or_(KGEdge.source_node_id == curr_node, KGEdge.target_node_id == curr_node),
        )
        if edge_types:
            stmt = stmt.where(KGEdge.edge_type.in_(edge_types))
        edges = session.scalars(stmt).all()

        for e in edges:
            neighbor = e.target_node_id if e.source_node_id == curr_node else e.source_node_id
            step = {
                "from_node_id": curr_node,
                "to_node_id": neighbor,
                "edge_type": e.edge_type,
                "weight": e.weight,
                "source_scene_id": e.source_scene_id,
            }
            new_path = path + [step]
            if neighbor == target_node_id:
                return new_path
            if neighbor not in visited and len(new_path) < max_hops:
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    return []


def query_neighbors(
    session: Session,
    project_id: int,
    node_id: int,
    edge_type: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(KGEdge).where(
        KGEdge.project_id == project_id,
        or_(KGEdge.source_node_id == node_id, KGEdge.target_node_id == node_id),
    )
    if edge_type:
        stmt = stmt.where(KGEdge.edge_type == edge_type)
    edges = session.scalars(stmt).all()

    neighbors: list[dict[str, Any]] = []
    for e in edges:
        n_id = e.target_node_id if e.source_node_id == node_id else e.source_node_id
        node = session.get(KGNode, n_id)
        if node:
            neighbors.append({
                "node_id": node.id,
                "node_type": node.node_type,
                "entity_id": node.entity_id,
                "name": node.name,
                "edge_type": e.edge_type,
                "modality": e.modality,
                "confirmed": e.confirmed,
            })
    return neighbors


def list_kg_nodes(session: Session, project_id: int, node_type: str | None = None) -> list[KGNode]:
    stmt = select(KGNode).where(KGNode.project_id == project_id)
    if node_type:
        stmt = stmt.where(KGNode.node_type == node_type)
    return list(session.scalars(stmt.order_by(KGNode.id.asc())).all())


def list_kg_edges(session: Session, project_id: int, edge_type: str | None = None) -> list[KGEdge]:
    stmt = select(KGEdge).where(KGEdge.project_id == project_id)
    if edge_type:
        stmt = stmt.where(KGEdge.edge_type == edge_type)
    return list(session.scalars(stmt.order_by(KGEdge.id.asc())).all())


def count_kg_nodes(session: Session, project_id: int) -> int:
    return session.scalar(select(func.count()).select_from(KGNode).where(KGNode.project_id == project_id)) or 0


def count_kg_edges(session: Session, project_id: int) -> int:
    return session.scalar(select(func.count()).select_from(KGEdge).where(KGEdge.project_id == project_id)) or 0


def rebuild_kg_projection(session: Session, project_id: int) -> dict[str, int]:
    # 1. Clear existing edges and nodes
    session.execute(delete(KGEdge).where(KGEdge.project_id == project_id))
    session.execute(delete(KGNode).where(KGNode.project_id == project_id))
    session.flush()

    node_count = 0
    edge_count = 0

    # 2. Characters
    characters = session.scalars(select(Character).where(Character.project_id == project_id)).all()
    char_node_map = {}
    for c in characters:
        n = get_or_create_kg_node(session, project_id, "CHARACTER", c.id, c.name, confirmed=True, flush_only=True)
        char_node_map[c.id] = n.id
        node_count += 1

    # 3. Locations
    locations = session.scalars(select(LocationEntity).where(LocationEntity.project_id == project_id)).all()
    for loc in locations:
        get_or_create_kg_node(session, project_id, "LOCATION", loc.id, loc.name, confirmed=True, flush_only=True)
        node_count += 1

    # 4. Items
    items = session.scalars(select(ItemEntity).where(ItemEntity.project_id == project_id)).all()
    for itm in items:
        get_or_create_kg_node(session, project_id, "ITEM", itm.id, itm.name, confirmed=True, flush_only=True)
        node_count += 1

    # 5. Secrets
    secrets = session.scalars(select(NarrativeSecret).where(NarrativeSecret.project_id == project_id)).all()
    for sec in secrets:
        sec_n = get_or_create_kg_node(session, project_id, "SECRET", sec.id, sec.title, confirmed=True, flush_only=True)
        node_count += 1
        for cid in (sec.known_by_characters or []):
            if cid in char_node_map:
                create_kg_edge(session, project_id, char_node_map[cid], sec_n.id, "KNOWS", confirmed=True, flush_only=True)
                edge_count += 1

    # 6. Relationship events
    rel_events = session.scalars(select(RelationshipEvent).where(RelationshipEvent.project_id == project_id)).all()
    for rel in rel_events:
        if rel.subject_character_id in char_node_map and rel.object_character_id in char_node_map:
            create_kg_edge(
                session,
                project_id,
                char_node_map[rel.subject_character_id],
                char_node_map[rel.object_character_id],
                "RELATIONSHIP",
                narrative_time=rel.narrative_time,
                confirmed=rel.confirmed,
                source_scene_id=rel.scene_id,
                flush_only=True,
            )
            edge_count += 1

    session.commit()
    return {"nodes": node_count, "edges": edge_count}
