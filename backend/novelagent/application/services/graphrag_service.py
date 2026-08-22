from __future__ import annotations

import time
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.graphrag_models import Community, CommunitySummary, GraphRAGQuery
from ...domain.rules import estimate_tokens
from ...domain.search_models import KGEdge, KGNode


def execute_graphrag_query(
    session: Session,
    project_id: int,
    query_type: str,
    query_text: str,
    parameters: dict[str, Any] | None = None,
) -> GraphRAGQuery:
    """Execute cross-volume, multi-hop or global theme GraphRAG queries."""
    start_t = time.perf_counter()
    params = parameters or {}
    max_hops = params.get("max_hops", 3)
    inc_communities = params.get("include_communities", [])

    # 1. Fetch relevant community summaries
    stmt = select(CommunitySummary).where(CommunitySummary.project_id == project_id)
    if inc_communities:
        stmt = stmt.where(CommunitySummary.community_id.in_(inc_communities))
    summaries = list(session.scalars(stmt).all())

    used_community_ids = list({s.community_id for s in summaries})
    summary_texts = [s.content for s in summaries[:5]]

    # 2. Gather top matching KG paths/nodes for cross-volume/multi-hop queries
    kg_nodes = list(session.scalars(select(KGNode).where(KGNode.project_id == project_id)).all())
    matched_nodes = [n.name for n in kg_nodes if any(token in query_text for token in n.name)]

    # 3. Assemble structured GraphRAG result
    ans_text = (
        f"【GraphRAG 响应 ({query_type})】: 基于 {len(used_community_ids)} 个社区上下文分析:\n"
        f"查询目标: {query_text}\n"
        f"关联正典实体: {', '.join(matched_nodes) or '全局图谱'}\n"
        f"社区上下文提炼: {' '.join(summary_texts) or '无相关社区摘要缓存'}"
    )

    duration = int((time.perf_counter() - start_t) * 1000)
    token_cost = estimate_tokens(ans_text) + estimate_tokens(query_text)

    result_payload = {
        "answer": ans_text,
        "matched_entities": matched_nodes,
        "communities_count": len(used_community_ids),
        "query_type": query_type,
    }

    query_obj = GraphRAGQuery(
        project_id=project_id,
        query_type=query_type,
        query_text=query_text.strip(),
        parameters=params,
        result=result_payload,
        communities_used=used_community_ids,
        token_cost=token_cost,
        duration_ms=duration,
        status="COMPLETED",
    )
    session.add(query_obj)
    session.commit()
    session.refresh(query_obj)
    return query_obj


def list_graphrag_queries(
    session: Session,
    project_id: int,
    query_type: str | None = None,
) -> list[GraphRAGQuery]:
    stmt = select(GraphRAGQuery).where(GraphRAGQuery.project_id == project_id)
    if query_type:
        stmt = stmt.where(GraphRAGQuery.query_type == query_type)
    return list(session.scalars(stmt.order_by(GraphRAGQuery.id.desc())).all())


def get_graphrag_query(session: Session, query_id: int, project_id: int) -> GraphRAGQuery:
    query_obj = session.scalar(
        select(GraphRAGQuery).where(GraphRAGQuery.id == query_id, GraphRAGQuery.project_id == project_id)
    )
    if not query_obj:
        raise KeyError(f"GraphRAG 查询不存在: ID {query_id}")
    return query_obj
