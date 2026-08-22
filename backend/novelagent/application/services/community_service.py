from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ...domain.graphrag_models import Community, CommunitySummary
from ...domain.graphrag_rules import detect_logical_communities
from ...domain.models import Volume
from ...domain.plot_models import PlotThread
from ...domain.rules import estimate_tokens
from ...domain.search_models import KGEdge, KGNode


def create_community(
    session: Session,
    project_id: int,
    name: str,
    community_type: str,
    source_entity_type: str | None = None,
    source_entity_id: int | None = None,
    tags: list[str] | None = None,
) -> Community:
    comm = Community(
        project_id=project_id,
        name=name.strip(),
        community_type=community_type,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        tags=tags or [],
        status="ACTIVE",
        version=1,
    )
    session.add(comm)
    session.commit()
    session.refresh(comm)
    return comm


def get_community(session: Session, community_id: int, project_id: int) -> Community:
    comm = session.scalar(
        select(Community).where(Community.id == community_id, Community.project_id == project_id)
    )
    if not comm:
        raise KeyError(f"社区不存在: ID {community_id}")
    return comm


def list_communities(
    session: Session,
    project_id: int,
    community_type: str | None = None,
) -> list[Community]:
    stmt = select(Community).where(Community.project_id == project_id)
    if community_type:
        stmt = stmt.where(Community.community_type == community_type)
    return list(session.scalars(stmt.order_by(Community.id.asc())).all())


def update_community(
    session: Session,
    community_id: int,
    project_id: int,
    name: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
) -> Community:
    comm = get_community(session, community_id, project_id)
    if name is not None:
        comm.name = name.strip()
    if tags is not None:
        comm.tags = tags
    if status is not None:
        comm.status = status
    comm.version += 1
    session.commit()
    session.refresh(comm)
    return comm


def delete_community(session: Session, community_id: int, project_id: int) -> None:
    comm = get_community(session, community_id, project_id)
    session.execute(delete(CommunitySummary).where(CommunitySummary.community_id == community_id))
    session.delete(comm)
    session.commit()


def auto_detect_and_sync_communities(session: Session, project_id: int) -> list[Community]:
    """Auto detect volume and plot thread communities and sync with database."""
    vols = session.scalars(select(Volume).where(Volume.project_id == project_id)).all()
    threads = session.scalars(select(PlotThread).where(PlotThread.project_id == project_id)).all()

    vol_dicts = [{"id": v.id, "title": v.title} for v in vols]
    thread_dicts = [{"id": t.id, "name": t.name, "priority": t.priority} for t in threads]

    detected = detect_logical_communities(vol_dicts, thread_dicts)
    created_list: list[Community] = []

    for d in detected:
        existing = session.scalar(
            select(Community).where(
                Community.project_id == project_id,
                Community.community_type == d["community_type"],
                Community.source_entity_type == d["source_entity_type"],
                Community.source_entity_id == d["source_entity_id"],
            )
        )
        if not existing:
            c = create_community(
                session,
                project_id=project_id,
                name=d["name"],
                community_type=d["community_type"],
                source_entity_type=d["source_entity_type"],
                source_entity_id=d["source_entity_id"],
                tags=d["tags"],
            )
            created_list.append(c)

    return list_communities(session, project_id)


def generate_community_summary(
    session: Session,
    community_id: int,
    project_id: int,
    summary_type: str = "OVERVIEW",
) -> CommunitySummary:
    """Generate structured summary for a community from associated KG nodes and edges."""
    comm = get_community(session, community_id, project_id)

    # Gather related nodes/edges
    nodes = list(session.scalars(select(KGNode).where(KGNode.project_id == project_id)).all())
    edges = list(session.scalars(select(KGEdge).where(KGEdge.project_id == project_id)).all())

    covered_nodes = [n.id for n in nodes[:20]]
    covered_edges = [e.id for e in edges[:30]]
    node_names = [n.name for n in nodes[:10]]

    content = f"【{comm.name} ({comm.community_type})】聚合摘要 - 类型: {summary_type}。\n主要实体包含: {', '.join(node_names) or '暂无'}。\n覆盖关系边数: {len(covered_edges)} 条。"
    cost = estimate_tokens(content)

    existing = session.scalar(
        select(CommunitySummary).where(
            CommunitySummary.community_id == community_id,
            CommunitySummary.summary_type == summary_type,
        )
    )
    if existing:
        existing.content = content
        existing.covered_node_ids = covered_nodes
        existing.covered_edge_ids = covered_edges
        existing.token_count = cost
        existing.status = "VALID"
        session.commit()
        session.refresh(existing)
        return existing

    summary = CommunitySummary(
        community_id=community_id,
        project_id=project_id,
        summary_type=summary_type,
        content=content,
        covered_node_ids=covered_nodes,
        covered_edge_ids=covered_edges,
        source_versions={},
        algorithm_version="v1",
        token_count=cost,
        status="VALID",
    )
    session.add(summary)
    session.commit()
    session.refresh(summary)
    return summary


def list_community_summaries(session: Session, community_id: int, project_id: int) -> list[CommunitySummary]:
    stmt = (
        select(CommunitySummary)
        .where(CommunitySummary.community_id == community_id, CommunitySummary.project_id == project_id)
        .order_by(CommunitySummary.id.asc())
    )
    return list(session.scalars(stmt).all())


def invalidate_affected_communities(
    session: Session,
    project_id: int,
    affected_entity_type: str | None = None,
    affected_entity_id: int | None = None,
) -> int:
    """Mark affected communities and their summaries as STALE."""
    stmt = select(Community).where(Community.project_id == project_id)
    if affected_entity_type:
        stmt = stmt.where(Community.source_entity_type == affected_entity_type)
    if affected_entity_id:
        stmt = stmt.where(Community.source_entity_id == affected_entity_id)

    affected = list(session.scalars(stmt).all())
    count = len(affected)
    for c in affected:
        c.status = "STALE"
        sums = session.scalars(select(CommunitySummary).where(CommunitySummary.community_id == c.id)).all()
        for s in sums:
            s.status = "STALE"
    session.commit()
    return count
