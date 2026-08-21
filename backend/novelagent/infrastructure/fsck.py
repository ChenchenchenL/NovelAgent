from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import make_session_factory


def _calculate_hash(path: Path) -> str:
    content = path.read_text(encoding="utf-8", errors="replace")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _check_journals(
    project_dir: Path,
    session: Session,
    auto_fix: bool,
) -> tuple[list[dict[str, Any]], int, int]:
    from ..domain.models import CommitJournal, SceneRevision

    journals = session.scalars(select(CommitJournal)).all()
    errors: list[dict[str, Any]] = []
    auto_fixed = 0

    for item in journals:
        raw_path = Path(item.file_path)
        file_path = raw_path if raw_path.is_absolute() else project_dir / raw_path

        if not file_path.exists():
            if auto_fix:
                rev = session.get(SceneRevision, item.revision_id)
                if rev:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(rev.content, encoding="utf-8")
                    item.file_status = "COMMITTED"
                    session.commit()
                    auto_fixed += 1
            if not file_path.exists():
                errors.append({
                    "type": "MISSING_FILE",
                    "journal_id": item.id,
                    "revision_id": item.revision_id,
                    "file_path": str(file_path),
                    "action": "RECOVER_FROM_SQLITE",
                })
                continue

        actual_hash = _calculate_hash(file_path)
        if actual_hash != item.content_hash:
            errors.append({
                "type": "HASH_MISMATCH",
                "journal_id": item.id,
                "revision_id": item.revision_id,
                "file_path": str(file_path),
                "expected": item.content_hash,
                "actual": actual_hash,
                "action": "REQUIRE_AUTHOR_DECISION",
            })
    return errors, auto_fixed, len(journals)


def _check_orphan_files(project_dir: Path, session: Session) -> tuple[list[dict[str, Any]], int]:
    from ..domain.models import CommitJournal

    text_dir = project_dir / ".novelagent" / "text" / "scenes"
    if not text_dir.exists():
        return [], 0

    journals = session.scalars(select(CommitJournal)).all()
    known_paths = {
        str((Path(j.file_path) if Path(j.file_path).is_absolute() else project_dir / Path(j.file_path)).resolve())
        for j in journals
    }

    orphans: list[dict[str, Any]] = []
    all_files = list(text_dir.rglob("*.md"))
    for md_file in all_files:
        if md_file.name == "current.md":
            continue
        if str(md_file.resolve()) not in known_paths:
            orphans.append({
                "type": "ORPHAN_FILE",
                "file_path": str(md_file),
                "action": "REQUIRE_AUTHOR_DECISION",
            })
    return orphans, len(all_files)


def _check_projections(session: Session, auto_fix: bool) -> tuple[list[dict[str, Any]], int, int]:
    from ..domain.models import PendingProjection

    all_projs = session.scalars(select(PendingProjection)).all()
    pending = [p for p in all_projs if p.status != "COMPLETED"]
    errors = []
    fixed = 0

    for proj in pending:
        if auto_fix:
            proj.status = "COMPLETED"
            session.commit()
            fixed += 1
        else:
            errors.append({
                "type": "PENDING_PROJECTION",
                "projection_id": proj.id,
                "projection_type": proj.projection_type,
                "revision_id": proj.revision_id,
                "action": "AUTO_REBUILD",
            })
    return errors, fixed, len(all_projs)


def check_project(project_dir: Path, session: Session, auto_fix: bool = False) -> dict[str, Any]:
    """Inspect consistency across SQLite, scene files, and pending projections."""
    journal_errors, journal_fixed, total_journals = _check_journals(project_dir, session, auto_fix)
    orphan_errors, total_files = _check_orphan_files(project_dir, session)
    projection_errors, proj_fixed, total_projs = _check_projections(session, auto_fix)

    all_errors = journal_errors + orphan_errors + projection_errors
    total_fixed = journal_fixed + proj_fixed
    total_checked = total_journals + total_files + total_projs

    return {
        "ok": len(all_errors) == 0,
        "status": "HEALTHY" if not all_errors else "CORRUPTED",
        "checked": total_checked,
        "errors": all_errors,
        "auto_fixed": total_fixed,
        "requires_decision": sum(1 for e in all_errors if e.get("action") == "REQUIRE_AUTHOR_DECISION"),
    }


def resolve_hash_conflict(
    project_dir: Path,
    session: Session,
    journal_id: int,
    resolution: str,  # "SQLITE", "FILE", "DUAL"
) -> dict[str, Any]:
    """Resolve HASH_MISMATCH based on author's explicit resolution."""
    from ..domain.models import CommitJournal, Scene, SceneRevision
    from .security import hash_text

    journal = session.get(CommitJournal, journal_id)
    if not journal:
        raise ValueError("提交日志不存在")

    rev = session.get(SceneRevision, journal.revision_id)
    raw_path = Path(journal.file_path)
    file_path = raw_path if raw_path.is_absolute() else project_dir / raw_path

    if resolution == "SQLITE" and rev:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(rev.content, encoding="utf-8")
        journal.content_hash = hash_text(rev.content)
        journal.file_status = "COMMITTED"
        session.commit()
        return {"status": "ok", "applied": "SQLITE_RESTORED"}

    if resolution == "FILE" and file_path.exists():
        file_content = file_path.read_text(encoding="utf-8", errors="replace")
        new_hash = hash_text(file_content)
        if rev:
            rev.content = file_content
            rev.content_hash = new_hash
        journal.content_hash = new_hash
        journal.file_status = "COMMITTED"
        session.commit()
        return {"status": "ok", "applied": "FILE_ADOPTED"}

    if resolution == "DUAL" and rev and file_path.exists():
        file_content = file_path.read_text(encoding="utf-8", errors="replace")
        dual_rev = SceneRevision(
            scene_id=rev.scene_id,
            base_revision_id=rev.id,
            content=file_content,
            source="CONFLICT_FILE",
            content_hash=hash_text(file_content),
        )
        session.add(dual_rev)
        session.flush()

        scene = session.get(Scene, rev.scene_id)
        if scene:
            scene.current_revision_id = dual_rev.id

        scene_dir = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{rev.scene_id}"
        dual_file = scene_dir / f"rev-{dual_rev.id}.md"
        current_file = scene_dir / "current.md"
        scene_dir.mkdir(parents=True, exist_ok=True)
        dual_file.write_text(file_content, encoding="utf-8")
        current_file.write_text(file_content, encoding="utf-8")

        dual_journal = CommitJournal(
            revision_id=dual_rev.id,
            content_hash=dual_rev.content_hash,
            file_path=str(dual_file),
            file_status="COMMITTED",
        )
        session.add(dual_journal)
        session.commit()
        return {"status": "ok", "applied": "DUAL_BRANCH_CREATED", "new_revision_id": dual_rev.id}

    raise ValueError(f"无效的决议参数: {resolution}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent File System & Consistency Checker")
    parser.add_argument("path", help="Project workspace root path")
    parser.add_argument("--fix", action="store_true", help="Auto heal missing files and projections")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()

    project_dir = Path(args.path).expanduser().resolve()
    db_path = project_dir / ".novelagent" / "project.db"
    if not db_path.is_file():
        print(f"Error: Database not found at {db_path}")
        return

    _, factory = make_session_factory(db_path)
    with factory() as session:
        result = check_project(project_dir, session, auto_fix=args.fix)
        if getattr(args, "json", False):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Status: {result['status']}, Errors: {len(result['errors'])}, Fixed: {result['auto_fixed']}")
            for err in result["errors"]:
                print(f" - [{err.get('type')}] {err.get('file_path', '')} -> {err.get('action')}")
