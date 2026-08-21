from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ...domain.models import ImportCheckpoint, ImportJob, Project
from ...infrastructure.parsers import discover_files
from ...infrastructure.security import is_path_allowed
from .import_runner import (
    active_import_cancel_tokens,
    active_import_pause_tokens,
    start_import_runner_thread,
)


def create_import_job(
    session: Session,
    session_factory: sessionmaker,
    project_id: int,
    project_dir: Path,
    source_path: str,
    allowed_dirs: set[Path],
    batch_size: int = 10,
    auto_extract: bool = False,
) -> tuple[ImportJob, str]:
    source = Path(source_path).expanduser().resolve()
    if not source.is_dir() or not is_path_allowed(source, allowed_dirs):
        raise HTTPException(status_code=403, detail="导入目录未授权")

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    files = discover_files(source)
    total_files = len(files)
    total_batches = (total_files + batch_size - 1) // batch_size if total_files > 0 else 0

    job = ImportJob(
        project_id=project.id,
        source_path=str(source),
        status="RUNNING",
        total_files=total_files,
        total_batches=total_batches,
        batch_size=batch_size,
        auto_extract=auto_extract,
        checkpoint=0,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    start_import_runner_thread(
        job_id=job.id,
        session_factory=session_factory,
        project_dir=project_dir,
        source_dir=source,
        batch_size=batch_size,
        auto_extract=auto_extract,
    )
    return job, f"/api/import-jobs/{job.id}/sse"


def get_import_job(session: Session, job_id: int) -> ImportJob:
    job = session.get(ImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="导入任务不存在")
    return job


def list_import_jobs(session: Session, project_id: int | None = None) -> list[ImportJob]:
    stmt = select(ImportJob)
    if project_id is not None:
        stmt = stmt.where(ImportJob.project_id == project_id)
    stmt = stmt.order_by(ImportJob.id.desc())
    return list(session.scalars(stmt).all())


def list_checkpoints(session: Session, job_id: int) -> list[ImportCheckpoint]:
    get_import_job(session, job_id)
    stmt = select(ImportCheckpoint).where(ImportCheckpoint.job_id == job_id).order_by(ImportCheckpoint.batch_index.asc())
    return list(session.scalars(stmt).all())


def pause_import_job(session: Session, job_id: int) -> ImportJob:
    job = get_import_job(session, job_id)
    if job.status != "RUNNING":
        raise HTTPException(status_code=400, detail="只能暂停正在运行的导入任务")
    token = active_import_pause_tokens.get(job_id)
    if token:
        token.set()
    job.status = "PAUSED"
    session.commit()
    session.refresh(job)
    return job


def resume_import_job(
    session: Session,
    session_factory: sessionmaker,
    project_dir: Path,
    job_id: int,
) -> ImportJob:
    job = get_import_job(session, job_id)
    if job.status not in {"PAUSED", "FAILED"}:
        raise HTTPException(status_code=400, detail="只能恢复已暂停或失败的导入任务")
    job.status = "RUNNING"
    session.commit()
    session.refresh(job)

    start_import_runner_thread(
        job_id=job.id,
        session_factory=session_factory,
        project_dir=project_dir,
        source_dir=Path(job.source_path),
        batch_size=job.batch_size,
        auto_extract=job.auto_extract,
    )
    return job


def retry_import_job(
    session: Session,
    session_factory: sessionmaker,
    project_dir: Path,
    job_id: int,
) -> ImportJob:
    job = get_import_job(session, job_id)
    job.status = "RUNNING"
    session.commit()
    session.refresh(job)

    start_import_runner_thread(
        job_id=job.id,
        session_factory=session_factory,
        project_dir=project_dir,
        source_dir=Path(job.source_path),
        batch_size=job.batch_size,
        auto_extract=job.auto_extract,
    )
    return job


def cancel_import_job(session: Session, job_id: int) -> ImportJob:
    job = get_import_job(session, job_id)
    token = active_import_cancel_tokens.get(job_id)
    if token:
        token.set()
    job.status = "CANCELLED"
    session.commit()
    session.refresh(job)
    return job


def run_project_import(
    session: Session,
    project_id: int,
    project_dir: Path,
    raw_source_path: str,
    allowed_dirs: set[Path],
) -> dict[str, Any]:
    """Synchronous import helper maintaining backwards compatibility."""
    source = Path(raw_source_path).expanduser().resolve()
    if not source.is_dir() or not is_path_allowed(source, allowed_dirs):
        raise HTTPException(status_code=403, detail="导入目录未授权")

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    files = discover_files(source)
    job = ImportJob(
        project_id=project.id,
        source_path=str(source),
        status="RUNNING",
        total_files=len(files),
        total_batches=1,
    )
    session.add(job)
    session.commit()

    from .import_runner import process_single_batch
    from ...infrastructure.db import make_session_factory
    _, factory = make_session_factory(project_dir / ".novelagent" / "project.db")
    success = process_single_batch(factory, project_dir, job.id, 0, files, auto_extract=False)

    job.status = "COMPLETED" if success else "FAILED"
    session.commit()
    return {"job_id": job.id, "status": job.status, "files": len(files)}
