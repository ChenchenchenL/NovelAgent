from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...domain.models import CommitJournal, Scene, SceneRevision
from ...domain.rules import TextPatchData
from ...infrastructure.security import hash_text


def _get_base_content(session: Session, scene: Scene) -> str:
    if not scene.current_revision_id:
        return ""
    rev = session.get(SceneRevision, scene.current_revision_id)
    return rev.content if rev else ""


def apply_text_patch(session: Session, scene_id: int, patch: TextPatchData | Any) -> tuple[SceneRevision, dict[str, int]]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    if patch.base_revision_id is not None and patch.base_revision_id != scene.current_revision_id:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "CONFLICT",
                "current_revision_id": scene.current_revision_id,
                "workspace_base_revision_id": patch.base_revision_id,
                "suggestion": "reload_or_merge",
            },
        )

    base_content = _get_base_content(session, scene)
    if patch.range_start < 0 or patch.range_end < patch.range_start or patch.range_end > len(base_content):
        raise HTTPException(status_code=400, detail="补丁范围超出正文边界")

    new_content = base_content[:patch.range_start] + patch.new_content + base_content[patch.range_end:]
    patch_info = {
        "range_start": patch.range_start,
        "range_end": patch.range_end,
        "new_content": patch.new_content,
        "source": patch.source,
        "intent": getattr(patch, "intent", "edit"),
    }
    revision = SceneRevision(
        scene_id=scene.id,
        base_revision_id=scene.current_revision_id,
        content=new_content,
        source=patch.source,
        content_hash=hash_text(new_content),
        patch_info=patch_info,
    )
    session.add(revision)
    scene.status = "PARTIALLY_ACCEPTED"
    session.commit()
    session.refresh(revision)

    applied_range = {
        "start": patch.range_start,
        "end": patch.range_start + len(patch.new_content),
    }
    return revision, applied_range


def merge_text_patches(
    session: Session,
    scene_id: int,
    base_revision_id: int | None,
    patches: list[TextPatchData | Any],
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    if base_revision_id is not None and base_revision_id != scene.current_revision_id:
        raise HTTPException(status_code=409, detail="基础版本冲突，正典已被其他操作更新")

    base_content = _get_base_content(session, scene)
    sorted_patches = sorted(patches, key=lambda p: p.range_start)

    for i in range(len(sorted_patches) - 1):
        if sorted_patches[i].range_end > sorted_patches[i + 1].range_start:
            raise HTTPException(
                status_code=409,
                detail=f"检测到补丁重叠冲突：第 {i+1} 项与第 {i+2} 项存在交集",
            )

    merged = base_content
    for p in reversed(sorted_patches):
        if p.range_start < 0 or p.range_end < p.range_start or p.range_end > len(base_content):
            raise HTTPException(status_code=400, detail="存在超出正文边界的补丁")
        merged = merged[:p.range_start] + p.new_content + merged[p.range_end:]

    return {
        "base_revision_id": scene.current_revision_id,
        "merged_content": merged,
        "patches_count": len(patches),
    }


def selective_accept_patches(
    session: Session,
    project_dir: Path,
    scene_id: int,
    base_revision_id: int | None,
    patches: list[TextPatchData | Any],
) -> tuple[Scene, SceneRevision]:
    merge_result = merge_text_patches(session, scene_id, base_revision_id, patches)
    merged_content = merge_result["merged_content"]

    scene = session.get(Scene, scene_id)
    revision = SceneRevision(
        scene_id=scene.id,
        base_revision_id=scene.current_revision_id,
        content=merged_content,
        source="SELECTIVE_ACCEPT",
        content_hash=hash_text(merged_content),
        patch_info={"type": "selective_accept", "count": len(patches)},
    )
    session.add(revision)
    session.flush()

    scene.current_revision_id = revision.id
    scene.status = "SCENE_ACCEPTED"

    scene_dir = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{scene.id}"
    rev_file = scene_dir / f"rev-{revision.id}.md"
    current_file = scene_dir / "current.md"

    # 2-Phase commit: write journal with PENDING status first
    journal = CommitJournal(
        revision_id=revision.id,
        content_hash=revision.content_hash,
        file_path=str(rev_file),
        file_status="PENDING",
    )
    session.add(journal)
    session.commit()

    # Write files to disk
    scene_dir.mkdir(parents=True, exist_ok=True)
    rev_file.write_text(revision.content, encoding="utf-8")
    current_file.write_text(revision.content, encoding="utf-8")

    # Mark as COMMITTED
    journal.file_status = "COMMITTED"
    session.commit()

    return scene, revision


def compute_revision_diff(
    session: Session,
    scene_id: int,
    target_revision_id: int,
    base_revision_id: int | None,
) -> dict[str, Any]:
    scene = session.get(Scene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")

    target_rev = session.get(SceneRevision, target_revision_id)
    if not target_rev or target_rev.scene_id != scene_id:
        raise HTTPException(status_code=404, detail="目标版本不存在")

    base_content = ""
    if base_revision_id is not None:
        base_rev = session.get(SceneRevision, base_revision_id)
        if not base_rev or base_rev.scene_id != scene_id:
            raise HTTPException(status_code=404, detail="对比基准版本不存在")
        base_content = base_rev.content

    base_lines = base_content.splitlines(keepends=True)
    target_lines = target_rev.content.splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(
        base_lines,
        target_lines,
        fromfile=f"rev-{base_revision_id or 'none'}",
        tofile=f"rev-{target_revision_id}",
    ))

    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    return {
        "base_revision_id": base_revision_id,
        "target_revision_id": target_revision_id,
        "unified_diff": "".join(diff_lines),
        "additions": additions,
        "deletions": deletions,
        "chunks": [{"diff": "".join(diff_lines)}],
    }
