from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import make_session_factory


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_project_backup(project_dir: Path, output_path: Path | None = None) -> Path:
    """Create a compressed .tar.gz backup of the project database and text versions."""
    resolved_dir = project_dir.resolve()
    novelagent_dir = resolved_dir / ".novelagent"
    if not novelagent_dir.is_dir():
        raise ValueError(f"不是有效的 NovelAgent 目录: {project_dir}")

    if output_path is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = resolved_dir / f"backup_{resolved_dir.name}_{timestamp}.tar.gz"

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta = {
        "project_name": resolved_dir.name,
        "created_at": _now_iso(),
        "format_version": "1.0",
    }

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as meta_file:
        json.dump(meta, meta_file, ensure_ascii=False, indent=2)
        meta_path = Path(meta_file.name)

    try:
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(novelagent_dir, arcname=".novelagent")
            tar.add(meta_path, arcname="backup_meta.json")
    finally:
        meta_path.unlink(missing_ok=True)

    return output_path


def export_project_novel(session: Session, project_id: int, export_format: str = "markdown") -> dict[str, Any]:
    """Export whole novel content in concatenated Markdown or structured JSON."""
    from ..domain.models import Chapter, Project, Scene, SceneRevision, Volume

    project = session.get(Project, project_id)
    if not project:
        raise ValueError("项目不存在")

    volumes = list(session.scalars(select(Volume).where(Volume.project_id == project_id).order_by(Volume.sequence)).all())
    chapters = list(session.scalars(select(Chapter).where(Chapter.project_id == project_id).order_by(Chapter.sequence)).all())
    scenes = list(session.scalars(
        select(Scene).join(Chapter, Scene.chapter_id == Chapter.id)
        .where(Chapter.project_id == project_id).order_by(Scene.sequence)
    ).all())

    scenes_by_chapter: dict[int, list[tuple[Scene, str]]] = {}
    for s in scenes:
        content = ""
        if s.current_revision_id:
            rev = session.get(SceneRevision, s.current_revision_id)
            if rev:
                content = rev.content
        scenes_by_chapter.setdefault(s.chapter_id, []).append((s, content))

    if export_format == "json":
        return _build_json_export(project.name, chapters, scenes_by_chapter)
    return _build_markdown_export(project.name, volumes, chapters, scenes_by_chapter)


def _build_json_export(project_name: str, chapters: list, scenes_map: dict) -> dict[str, Any]:
    ch_data = []
    for c in chapters:
        sc_list = [{"title": s.title, "sequence": s.sequence, "pov": s.pov, "location": s.location, "content": text} for s, text in scenes_map.get(c.id, [])]
        ch_data.append({"title": c.title, "sequence": c.sequence, "status": c.status, "scenes": sc_list})
    return {"project_name": project_name, "exported_at": _now_iso(), "chapters": ch_data}


def _build_markdown_export(project_name: str, volumes: list, chapters: list, scenes_map: dict) -> dict[str, Any]:
    lines = [f"# {project_name}\n"]
    for c in chapters:
        lines.append(f"\n# {c.title}\n")
        for s, text in scenes_map.get(c.id, []):
            lines.append(f"\n## {s.title}\n\n{text}\n")
    full_text = "\n".join(lines).strip()
    return {"project_name": project_name, "exported_at": _now_iso(), "format": "markdown", "content": full_text}


def restore_project_backup(backup_path: Path, target_dir: Path) -> dict[str, Any]:
    """Restore project from a .tar.gz archive safely and verify consistency."""
    from .fsck import check_project

    if not backup_path.is_file():
        raise ValueError(f"备份文件不存在: {backup_path}")

    resolved_target = target_dir.resolve()
    resolved_target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(backup_path, "r:gz") as tar:
        for member in tar.getmembers():
            target_file = (resolved_target / member.name).resolve()
            if not target_file.is_relative_to(resolved_target):
                raise ValueError(f"检测到非法路径遍历项: {member.name}")
        try:
            tar.extractall(path=resolved_target, filter="data")
        except TypeError:
            tar.extractall(path=resolved_target)

    db_path = resolved_target / ".novelagent" / "project.db"
    if not db_path.is_file():
        raise ValueError("备份文件中缺少有效的 .novelagent/project.db")

    _, factory = make_session_factory(db_path)
    with factory() as session:
        fsck_res = check_project(resolved_target, session, auto_fix=True)

    return {
        "status": "ok",
        "target_dir": str(resolved_target),
        "fsck_status": fsck_res["status"],
        "auto_fixed": fsck_res["auto_fixed"],
    }


def backup_cli() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent Project Backup Utility")
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("--output", help="Destination path for .tar.gz archive")
    args = parser.parse_args()
    out = create_project_backup(Path(args.project_path), Path(args.output) if args.output else None)
    print(f"Backup created successfully: {out}")


def export_cli() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent Export Utility")
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("--project-id", type=int, default=None, help="Project ID to export")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"], help="Export format")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    project_dir = Path(args.project_path).resolve()
    db_path = project_dir / ".novelagent" / "project.db"
    if not db_path.is_file():
        print(f"Error: Database not found at {db_path}")
        return

    _, factory = make_session_factory(db_path)
    with factory() as session:
        from ..domain.models import Project
        project_id = args.project_id
        if project_id is None:
            proj = session.scalars(select(Project)).first()
            if not proj:
                print("Error: No project found in database")
                return
            project_id = proj.id
        result = export_project_novel(session, project_id=project_id, export_format=args.format)
        content = result.get("content") if args.format == "markdown" else json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            print(f"Export written to {args.output}")
        else:
            print(content)


def restore_cli() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent Restore Utility")
    parser.add_argument("backup_file", help="Path to backup .tar.gz file")
    parser.add_argument("--target", required=True, help="Target project root directory")
    args = parser.parse_args()
    res = restore_project_backup(Path(args.backup_file), Path(args.target))
    print(f"Restore completed: {res}")
