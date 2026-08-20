from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.models import Chapter, CommitJournal, ImportJob, Project, Scene, SceneRevision
from ...infrastructure.security import hash_text, is_path_allowed


def run_project_import(
    session: Session,
    project_id: int,
    project_dir: Path,
    raw_source_path: str,
    allowed_dirs: set[Path],
) -> dict[str, Any]:
    source = Path(raw_source_path).expanduser().resolve()
    if not source.is_dir() or not is_path_allowed(source, allowed_dirs):
        raise HTTPException(status_code=403, detail="导入目录未授权")

    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}
    )
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    job = ImportJob(project_id=project.id, source_path=str(source), status="RUNNING")
    session.add(job)
    session.flush()

    imported: list[dict[str, Any]] = []
    for index, file_path in enumerate(files):
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        documents = [(file_path.stem, raw)]
        if file_path.suffix.lower() == ".json":
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and isinstance(parsed.get("chapters"), list):
                    documents = [
                        (str(item.get("title", f"导入章节 {index + 1}")), str(item.get("content", "")))
                        for item in parsed["chapters"]
                        if isinstance(item, dict)
                    ]
            except json.JSONDecodeError:
                pass

        for title, content in documents:
            chapter = Chapter(
                project_id=project.id,
                title=title or file_path.stem,
                sequence=len(imported) + 1,
                status="IN_PROGRESS",
            )
            session.add(chapter)
            session.flush()
            scene = Scene(
                chapter_id=chapter.id,
                title="导入场景",
                sequence=1,
                status="SCENE_ACCEPTED",
            )
            session.add(scene)
            session.flush()
            revision = SceneRevision(
                scene_id=scene.id,
                content=content,
                source="IMPORT",
                content_hash=hash_text(content),
            )
            session.add(revision)
            session.flush()
            scene.current_revision_id = revision.id

            # Write immutable Markdown version with 2-Phase Commit
            scene_dir = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{scene.id}"
            rev_file = scene_dir / f"rev-{revision.id}.md"
            current_file = scene_dir / "current.md"

            journal = CommitJournal(
                revision_id=revision.id,
                content_hash=revision.content_hash,
                file_path=str(rev_file),
                file_status="PENDING",
            )
            session.add(journal)
            session.flush()

            scene_dir.mkdir(parents=True, exist_ok=True)
            rev_file.write_text(revision.content, encoding="utf-8")
            current_file.write_text(revision.content, encoding="utf-8")

            journal.file_status = "COMMITTED"
            imported.append({"chapter_id": chapter.id, "scene_id": scene.id, "source": str(file_path)})

        job.checkpoint = index + 1
        session.flush()

    job.status = "COMPLETED"
    session.commit()
    return {"job_id": job.id, "status": job.status, "files": len(files), "imported": imported}
