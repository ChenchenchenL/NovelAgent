from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from ...domain.models import Chapter, CommitJournal, ImportCheckpoint, ImportJob, Scene, SceneRevision
from ...infrastructure.parsers import discover_files, parse_document_file
from ...infrastructure.security import hash_text

logger = logging.getLogger(__name__)
active_import_cancel_tokens: dict[int, threading.Event] = {}
active_import_pause_tokens: dict[int, threading.Event] = {}
_import_events: dict[int, list[dict[str, Any]]] = {}
_import_lock = threading.Lock()


def now() -> datetime:
    return datetime.now(timezone.utc)


def emit_import_event(job_id: int, event_type: str, payload: dict[str, Any]) -> None:
    with _import_lock:
        events = _import_events.setdefault(job_id, [])
        seq = len(events) + 1
        payload["sequence_number"] = seq
        events.append({"event": event_type, "data": payload, "seq": seq})
        if len(_import_events) > 50:
            for k in list(_import_events.keys())[:-50]:
                _import_events.pop(k, None)


def start_import_runner_thread(
    job_id: int,
    session_factory: sessionmaker,
    project_dir: Path,
    source_dir: Path,
    batch_size: int = 10,
    auto_extract: bool = False,
) -> None:
    cancel_token = threading.Event()
    pause_token = threading.Event()
    with _import_lock:
        active_import_cancel_tokens[job_id] = cancel_token
        active_import_pause_tokens[job_id] = pause_token

    def _worker():
        try:
            _execute_import_job(
                job_id=job_id,
                session_factory=session_factory,
                project_dir=project_dir,
                source_dir=source_dir,
                batch_size=batch_size,
                auto_extract=auto_extract,
                cancel_token=cancel_token,
                pause_token=pause_token,
            )
        finally:
            with _import_lock:
                active_import_cancel_tokens.pop(job_id, None)
                active_import_pause_tokens.pop(job_id, None)

    thread = threading.Thread(target=_worker, daemon=True, name=f"ImportRunner-{job_id}")
    thread.start()


def _execute_import_job(
    job_id: int,
    session_factory: sessionmaker,
    project_dir: Path,
    source_dir: Path,
    batch_size: int,
    auto_extract: bool,
    cancel_token: threading.Event,
    pause_token: threading.Event,
) -> None:
    files = discover_files(source_dir)
    total_files = len(files)
    batches = [files[i:i + batch_size] for i in range(0, total_files, batch_size)] if files else []
    total_batches = len(batches)

    with session_factory() as db:
        job = db.get(ImportJob, job_id)
        if not job:
            return
        job.status = "RUNNING"
        job.total_files = total_files
        job.total_batches = total_batches
        job.started_at = now()
        start_batch = job.checkpoint
        db.commit()

    emit_import_event(job_id, "import_started", {"job_id": job_id, "total_files": total_files, "total_batches": total_batches})

    for b_idx in range(start_batch, total_batches):
        if cancel_token.is_set():
            _set_job_status(session_factory, job_id, "CANCELLED")
            emit_import_event(job_id, "cancelled", {"job_id": job_id, "message": "导入任务已取消"})
            return
        if pause_token.is_set():
            _set_job_status(session_factory, job_id, "PAUSED")
            emit_import_event(job_id, "paused", {"job_id": job_id, "checkpoint": b_idx})
            return

        batch_files = batches[b_idx]
        emit_import_event(job_id, "batch_progress", {"batch_index": b_idx + 1, "status": "RUNNING", "files_in_batch": len(batch_files)})
        success = process_single_batch(session_factory, project_dir, job_id, b_idx, batch_files, auto_extract)

        if not success:
            emit_import_event(job_id, "batch_completed", {"batch_index": b_idx + 1, "status": "FAILED"})
        else:
            emit_import_event(job_id, "batch_completed", {"batch_index": b_idx + 1, "status": "COMPLETED"})

    _finalize_import_job(session_factory, job_id)


def process_single_batch(
    session_factory: sessionmaker,
    project_dir: Path,
    job_id: int,
    batch_index: int,
    batch_files: list[Path],
    auto_extract: bool,
) -> bool:
    with session_factory() as db:
        job = db.get(ImportJob, job_id)
        if not job:
            return False
        imported_count = 0
        try:
            for file_path in batch_files:
                chapters, enc = parse_document_file(file_path)
                for ch_data in chapters:
                    imported_count += _import_chapter_scenes(db, project_dir, job.project_id, ch_data, file_path, enc, auto_extract)

            chk = db.scalar(select(ImportCheckpoint).where(ImportCheckpoint.job_id == job_id, ImportCheckpoint.batch_index == batch_index + 1))
            if not chk:
                chk = ImportCheckpoint(job_id=job_id, batch_index=batch_index + 1)
                db.add(chk)
            chk.status = "COMPLETED"
            chk.items_imported = imported_count
            chk.batch_info = {"files": [str(f) for f in batch_files]}
            job.checkpoint = batch_index + 1
            db.commit()
            return True
        except Exception as exc:
            db.rollback()
            logger.exception("Batch import failed: %s", exc)
            _record_batch_error(db, job_id, batch_index + 1, str(exc), batch_files)
            return False


def _import_chapter_scenes(
    db: Session,
    project_dir: Path,
    project_id: int,
    ch_data: dict[str, Any],
    file_path: Path,
    enc: str,
    auto_extract: bool,
) -> int:
    max_seq = db.scalar(select(func.max(Chapter.sequence)).where(Chapter.project_id == project_id)) or 0
    chapter = Chapter(project_id=project_id, title=ch_data.get("title", "导入章节"), sequence=max_seq + 1, status="IN_PROGRESS")
    db.add(chapter)
    db.flush()

    imported_scenes = 0
    for s_idx, sc_data in enumerate(ch_data.get("scenes", [])):
        content = sc_data.get("content", "")
        scene = Scene(chapter_id=chapter.id, title=sc_data.get("title", f"场景 {s_idx + 1}"), sequence=s_idx + 1, status="SCENE_ACCEPTED")
        db.add(scene)
        db.flush()

        rev = SceneRevision(scene_id=scene.id, content=content, source="IMPORT", content_hash=hash_text(content))
        db.add(rev)
        db.flush()
        scene.current_revision_id = rev.id

        scene_dir = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{scene.id}"
        rev_file = scene_dir / f"rev-{rev.id}.md"
        current_file = scene_dir / "current.md"

        journal = CommitJournal(revision_id=rev.id, content_hash=rev.content_hash, file_path=str(rev_file), file_status="PENDING", file_size=len(content.encode("utf-8")), encoding=enc)
        db.add(journal)
        db.flush()

        scene_dir.mkdir(parents=True, exist_ok=True)
        rev_file.write_text(content, encoding="utf-8")
        current_file.write_text(content, encoding="utf-8")
        journal.file_status = "COMMITTED"
        imported_scenes += 1
    return imported_scenes


def _record_batch_error(db: Session, job_id: int, batch_index: int, error_msg: str, files: list[Path]) -> None:
    chk = db.scalar(select(ImportCheckpoint).where(ImportCheckpoint.job_id == job_id, ImportCheckpoint.batch_index == batch_index))
    if not chk:
        chk = ImportCheckpoint(job_id=job_id, batch_index=batch_index)
        db.add(chk)
    chk.status = "FAILED"
    chk.error_message = error_msg
    chk.batch_info = {"files": [str(f) for f in files]}
    db.commit()


def _set_job_status(session_factory: sessionmaker, job_id: int, status: str) -> None:
    with session_factory() as db:
        job = db.get(ImportJob, job_id)
        if job:
            job.status = status
            db.commit()


def _finalize_import_job(session_factory: sessionmaker, job_id: int) -> None:
    with session_factory() as db:
        job = db.get(ImportJob, job_id)
        if not job or job.status in {"CANCELLED", "PAUSED"}:
            return
        failed_count = db.scalar(select(ImportCheckpoint).where(ImportCheckpoint.job_id == job_id, ImportCheckpoint.status == "FAILED").limit(1))
        job.status = "FAILED" if failed_count else "COMPLETED"
        job.completed_at = now()
        db.commit()

    emit_import_event(job_id, "import_completed", {"job_id": job_id, "status": job.status})


async def stream_import_events(job_id: int, since_seq: int = 0) -> AsyncIterator[str]:
    cursor = since_seq
    idle_count = 0
    while True:
        events_to_send = []
        with _import_lock:
            all_evts = _import_events.get(job_id, [])
            for e in all_evts:
                if e["seq"] > cursor:
                    events_to_send.append(e)

        for ev in events_to_send:
            cursor = ev["seq"]
            yield f"id: {ev['seq']}\nevent: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
            if ev["event"] in {"import_completed", "cancelled", "paused"}:
                return

        await asyncio.sleep(0.2)
        idle_count += 1
        if idle_count % 75 == 0:
            yield ": keep-alive\n\n"
        if idle_count > 3000:
            break
