from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.quality_models import ClicheBlacklist
from ...domain.quality_rules import detect_cliche_patterns


def create_cliche_entry(
    session: Session,
    project_id: int,
    pattern: str,
    pattern_type: str = "EXACT",
    category: str = "GENERAL",
    genre: str | None = None,
    severity: str = "WARNING",
    suggestion: str | None = None,
    enabled: bool = True,
) -> ClicheBlacklist:
    entry = ClicheBlacklist(
        project_id=project_id,
        pattern=pattern.strip(),
        pattern_type=pattern_type.upper(),
        category=category,
        genre=genre,
        severity=severity,
        suggestion=suggestion,
        enabled=enabled,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_cliche_entries(
    session: Session,
    project_id: int,
    genre: str | None = None,
    category: str | None = None,
    enabled_only: bool = False,
) -> list[ClicheBlacklist]:
    stmt = select(ClicheBlacklist).where(ClicheBlacklist.project_id == project_id)
    if genre:
        stmt = stmt.where((ClicheBlacklist.genre == genre) | (ClicheBlacklist.genre.is_(None)))
    if category:
        stmt = stmt.where(ClicheBlacklist.category == category)
    if enabled_only:
        stmt = stmt.where(ClicheBlacklist.enabled.is_(True))
    stmt = stmt.order_by(ClicheBlacklist.id.asc())
    return list(session.scalars(stmt).all())


def update_cliche_entry(
    session: Session,
    cliche_id: int,
    project_id: int,
    pattern: str | None = None,
    pattern_type: str | None = None,
    category: str | None = None,
    genre: str | None = None,
    severity: str | None = None,
    suggestion: str | None = None,
    enabled: bool | None = None,
) -> ClicheBlacklist:
    entry = session.scalar(
        select(ClicheBlacklist).where(ClicheBlacklist.id == cliche_id, ClicheBlacklist.project_id == project_id)
    )
    if not entry:
        raise KeyError(f"套话条目不存在: ID {cliche_id}")

    if pattern is not None:
        entry.pattern = pattern.strip()
    if pattern_type is not None:
        entry.pattern_type = pattern_type.upper()
    if category is not None:
        entry.category = category
    if genre is not None:
        entry.genre = genre
    if severity is not None:
        entry.severity = severity
    if suggestion is not None:
        entry.suggestion = suggestion
    if enabled is not None:
        entry.enabled = enabled

    entry.version += 1
    session.commit()
    session.refresh(entry)
    return entry


def delete_cliche_entry(session: Session, cliche_id: int, project_id: int) -> None:
    entry = session.scalar(
        select(ClicheBlacklist).where(ClicheBlacklist.id == cliche_id, ClicheBlacklist.project_id == project_id)
    )
    if not entry:
        raise KeyError(f"套话条目不存在: ID {cliche_id}")
    session.delete(entry)
    session.commit()


def scan_text_cliches(
    session: Session,
    project_id: int,
    text: str,
    genre: str | None = None,
) -> list[dict[str, Any]]:
    entries = list_cliche_entries(session, project_id, genre=genre, enabled_only=True)
    dict_entries = [
        {
            "id": e.id,
            "pattern": e.pattern,
            "pattern_type": e.pattern_type,
            "category": e.category,
            "genre": e.genre,
            "severity": e.severity,
            "suggestion": e.suggestion,
            "enabled": e.enabled,
        }
        for e in entries
    ]
    return detect_cliche_patterns(text, dict_entries)
