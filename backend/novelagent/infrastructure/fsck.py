from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import make_session_factory


def check_project(project_dir: Path, session: Session, auto_fix: bool = False) -> dict[str, Any]:
    from ..domain.models import CommitJournal, SceneRevision

    journals = session.scalars(select(CommitJournal)).all()
    corruptions: list[dict[str, Any]] = []

    for item in journals:
        raw_path = Path(item.file_path)
        file_path = raw_path if raw_path.is_absolute() else project_dir / raw_path

        if not file_path.exists():
            if auto_fix:
                revision = session.get(SceneRevision, item.revision_id)
                if revision:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(revision.content, encoding="utf-8")
            if not file_path.exists():
                corruptions.append({
                    "journal_id": item.id,
                    "file_path": str(file_path),
                    "reason": "MISSING_FILE",
                })
                continue

        content = file_path.read_text(encoding="utf-8", errors="replace")
        actual_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual_hash != item.content_hash:
            corruptions.append({
                "journal_id": item.id,
                "file_path": str(file_path),
                "expected": item.content_hash,
                "actual": actual_hash,
                "reason": "HASH_MISMATCH",
            })

    return {
        "ok": not corruptions,
        "errors": corruptions,
        "status": "HEALTHY" if not corruptions else "CORRUPTED",
        "checked": len(journals),
        "corruptions": corruptions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent File System & Consistency Checker")
    parser.add_argument("path", help="Project workspace root path")
    parser.add_argument("--fix", action="store_true", help="Auto heal missing files from SQLite revisions")
    args = parser.parse_args()

    project_dir = Path(args.path).expanduser().resolve()
    db_path = project_dir / ".novelagent" / "project.db"
    if not db_path.is_file():
        print(f"Error: Database not found at {db_path}")
        return

    _, factory = make_session_factory(db_path)
    with factory() as session:
        result = check_project(project_dir, session, auto_fix=args.fix)
        print(result)
