from __future__ import annotations

import logging
import sqlite3
from typing import Any, Optional
from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.exc import DatabaseError, OperationalError
from sqlalchemy.orm import Session

from ...domain.models import CanonClaim, Chapter, Scene, SceneRevision
from ...domain.search_models import FTSDocument

logger = logging.getLogger(__name__)

FTS_ERRORS = (OperationalError, DatabaseError, sqlite3.OperationalError, sqlite3.DatabaseError)


def _escape_fts5_query(query: str) -> str:
    """Safely escape and quote query string for SQLite FTS5 phrase match."""
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _escape_like(raw: str) -> str:
    """Escape special SQL LIKE wildcards (% and _)."""
    return raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _sync_fts_virtual_table(session: Session, doc: FTSDocument) -> None:
    try:
        session.execute(
            text("INSERT INTO fts_documents_fts(rowid, content) VALUES (:rowid, :content)"),
            {"rowid": doc.id, "content": doc.content},
        )
    except FTS_ERRORS as exc:
        logger.debug("FTS5 table sync skipped or unavailable: %s", exc)


def index_fts_document(
    session: Session,
    project_id: int,
    doc_type: str,
    source_id: int,
    source_version: int,
    content: str,
    narrative_time: str | None = None,
    modality: str = "ACTUAL",
    confirmed: bool = False,
) -> FTSDocument:
    # Remove older document for same source
    old_docs = session.scalars(
        select(FTSDocument).where(
            FTSDocument.project_id == project_id,
            FTSDocument.doc_type == doc_type,
            FTSDocument.source_id == source_id,
        )
    ).all()
    for d in old_docs:
        try:
            session.execute(text("DELETE FROM fts_documents_fts WHERE rowid = :rowid"), {"rowid": d.id})
        except FTS_ERRORS as exc:
            logger.debug("FTS5 row delete skipped: %s", exc)
        session.delete(d)

    doc = FTSDocument(
        project_id=project_id,
        doc_type=doc_type,
        source_id=source_id,
        source_version=source_version,
        content=content.strip(),
        narrative_time=narrative_time,
        modality=modality,
        confirmed=confirmed,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    _sync_fts_virtual_table(session, doc)
    session.commit()
    return doc


def search_fts(
    session: Session,
    project_id: int,
    query: str,
    doc_type: str | None = None,
    modality: str | None = None,
    confirmed_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []

    # 1. Attempt FTS5 virtual table MATCH with properly escaped query
    try:
        sql = """
            SELECT f.id, f.project_id, f.doc_type, f.source_id, f.source_version,
                   f.content, f.narrative_time, f.modality, f.confirmed, fts.rank as score
            FROM fts_documents f
            JOIN fts_documents_fts fts ON f.id = fts.rowid
            WHERE f.project_id = :project_id
        """
        params: dict[str, Any] = {
            "project_id": project_id,
            "query": _escape_fts5_query(q),
            "limit": limit,
            "offset": offset,
        }
        if doc_type:
            sql += " AND f.doc_type = :doc_type"
            params["doc_type"] = doc_type
        if modality:
            sql += " AND f.modality = :modality"
            params["modality"] = modality
        if confirmed_only:
            sql += " AND f.confirmed = 1"
        sql += " AND fts MATCH :query ORDER BY rank LIMIT :limit OFFSET :offset"
        rows = session.execute(text(sql), params).fetchall()
        if rows:
            return [dict(r._mapping) for r in rows]
    except FTS_ERRORS as exc:
        logger.debug("FTS5 MATCH failed or virtual table absent, falling back to LIKE: %s", exc)

    # 2. Fallback to SQL LIKE with escaped wildcards
    escaped_q = _escape_like(q)
    stmt = select(FTSDocument).where(
        FTSDocument.project_id == project_id,
        FTSDocument.content.ilike(f"%{escaped_q}%", escape="\\"),
    )
    if doc_type:
        stmt = stmt.where(FTSDocument.doc_type == doc_type)
    if modality:
        stmt = stmt.where(FTSDocument.modality == modality)
    if confirmed_only:
        stmt = stmt.where(FTSDocument.confirmed.is_(True))
    stmt = stmt.order_by(FTSDocument.id.desc()).offset(offset).limit(limit)
    docs = session.scalars(stmt).all()
    return [
        {
            "id": d.id,
            "project_id": d.project_id,
            "doc_type": d.doc_type,
            "source_id": d.source_id,
            "source_version": d.source_version,
            "content": d.content,
            "narrative_time": d.narrative_time,
            "modality": d.modality,
            "confirmed": d.confirmed,
            "score": 1.0,
        }
        for d in docs
    ]


def count_fts_documents(session: Session, project_id: int) -> int:
    return session.scalar(select(func.count()).select_from(FTSDocument).where(FTSDocument.project_id == project_id)) or 0


def rebuild_fts_index(session: Session, project_id: int) -> int:
    docs = list(session.scalars(select(FTSDocument).where(FTSDocument.project_id == project_id)).all())
    for d in docs:
        try:
            session.execute(text("DELETE FROM fts_documents_fts WHERE rowid = :rowid"), {"rowid": d.id})
        except FTS_ERRORS as exc:
            logger.debug("FTS5 table delete row skipped: %s", exc)
        session.delete(d)
    session.commit()

    count = 0
    scenes = session.scalars(
        select(Scene).join(Chapter).where(Chapter.project_id == project_id)
    ).all()
    for sc in scenes:
        if sc.current_revision_id:
            rev = session.get(SceneRevision, sc.current_revision_id)
            if rev and rev.content:
                index_fts_document(
                    session,
                    project_id=project_id,
                    doc_type="SCENE",
                    source_id=sc.id,
                    source_version=rev.id,
                    content=rev.content,
                    narrative_time=sc.entry_contract.get("narrative_time") if sc.entry_contract else None,
                    modality="ACTUAL",
                    confirmed=True,
                )
                count += 1

    claims = session.scalars(select(CanonClaim).where(CanonClaim.project_id == project_id)).all()
    for clm in claims:
        txt = f"{clm.subject} {clm.predicate} {clm.object_value}"
        index_fts_document(
            session,
            project_id=project_id,
            doc_type="CLAIM",
            source_id=clm.id,
            source_version=1,
            content=txt,
            modality=clm.modality,
            confirmed=True,
        )
        count += 1

    return count
