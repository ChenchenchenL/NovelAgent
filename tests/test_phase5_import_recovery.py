from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from novelagent.api import create_app
from novelagent.config import Settings
from novelagent.domain.models import (
    Chapter,
    CommitJournal,
    ImportCheckpoint,
    ImportJob,
    PendingProjection,
    Project,
    Scene,
    SceneRevision,
)
from novelagent.infrastructure.backup_export import (
    create_project_backup,
    export_project_novel,
    restore_project_backup,
)
from novelagent.infrastructure.db import make_session_factory
from novelagent.infrastructure.fsck import check_project, resolve_hash_conflict
from novelagent.infrastructure.parsers import (
    detect_encoding,
    discover_files,
    parse_document_file,
    parse_json_document,
    parse_markdown,
    parse_txt_document,
    parse_yaml_document,
    read_file_text,
)


def test_file_discovery_and_encoding(tmp_path: Path):
    source_dir = tmp_path / "source_docs"
    source_dir.mkdir()

    # UTF-8 BOM
    f1 = source_dir / "utf8_bom.txt"
    f1.write_bytes(b"\xef\xbb\xbf" + "第一章 带有BOM的正文".encode("utf-8"))

    # GBK
    f2 = source_dir / "gbk.txt"
    f2.write_bytes("第二章 中文GBK编码正文".encode("gbk"))

    # Big5
    f3 = source_dir / "big5.txt"
    f3.write_bytes("第三章 繁體Big5編碼正文".encode("big5"))

    # Markdown
    f4 = source_dir / "chapter.md"
    f4.write_text("# 第四章 Markdown\n\n## 场景一\n\n风雪漫天。", encoding="utf-8")

    # Hidden file (should be ignored)
    f_hidden = source_dir / ".hidden.txt"
    f_hidden.write_text("hidden", encoding="utf-8")

    files = discover_files(source_dir)
    assert len(files) == 4
    assert f_hidden not in files

    # Test encodings
    assert detect_encoding(f1.read_bytes()) == "utf-8-sig"
    assert detect_encoding(f2.read_bytes()) == "gbk"
    assert detect_encoding(f3.read_bytes()) == "big5"

    text2, enc2 = read_file_text(f2)
    assert "第二章" in text2
    assert enc2 == "gbk"


def test_document_parsing():
    # Markdown
    md_content = "# 第一章 启程\n\n## 场景一 出发\n\n收拾行囊。\n\n## 场景二 途中\n\n马蹄声急。"
    md_chapters = parse_markdown(md_content)
    assert len(md_chapters) == 1
    assert md_chapters[0]["title"] == "第一章 启程"
    assert len(md_chapters[0]["scenes"]) == 2
    assert md_chapters[0]["scenes"][0]["title"] == "场景一 出发"
    assert md_chapters[0]["scenes"][0]["content"] == "收拾行囊。"

    # Plain text without headers
    txt_content = "纯文本段落一。\n纯文本段落二。"
    txt_chapters = parse_markdown(txt_content, default_title="默认章节")
    assert len(txt_chapters) == 1
    assert len(txt_chapters[0]["scenes"]) == 1

    # Text with Chinese Chapter Markings
    marked_txt = "第一卷 序幕\n第一回 龙争虎斗\n江湖夜雨十年灯。\n\n第二回 风起云涌\n落花时节又逢君。"
    marked_chapters = parse_txt_document(marked_txt)
    assert len(marked_chapters) >= 2

    # JSON Document
    json_str = json.dumps({"chapters": [{"title": "JSON章", "scenes": [{"title": "JSON景", "content": "JSON正文"}]}]})
    json_chapters = parse_json_document(json_str)
    assert len(json_chapters) == 1
    assert json_chapters[0]["title"] == "JSON章"

    # YAML Document
    yaml_str = "chapters:\n  - title: YAML章\n    scenes:\n      - title: YAML景\n        content: YAML正文\n"
    yaml_chapters = parse_yaml_document(yaml_str)
    assert len(yaml_chapters) == 1
    assert yaml_chapters[0]["title"] == "YAML章"


def test_fsck_missing_file_recovery(tmp_path: Path):
    project_dir = tmp_path / "project_fsck"
    db_path = project_dir / ".novelagent" / "project.db"
    _, factory = make_session_factory(db_path)

    with factory() as session:
        proj = Project(path=str(project_dir), name="测试项目")
        session.add(proj)
        session.flush()

        ch = Chapter(project_id=proj.id, title="第1章", sequence=1)
        session.add(ch)
        session.flush()

        sc = Scene(chapter_id=ch.id, title="第1场", sequence=1)
        session.add(sc)
        session.flush()

        content = "正典正文内容，绝不丢失。"
        rev = SceneRevision(scene_id=sc.id, content=content, content_hash="hash_123", source="AUTHOR")
        session.add(rev)
        session.flush()
        sc.current_revision_id = rev.id

        rev_file = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{sc.id}" / f"rev-{rev.id}.md"
        journal = CommitJournal(
            revision_id=rev.id,
            content_hash="hash_123",
            file_path=str(rev_file),
            file_status="COMMITTED",
        )
        session.add(journal)
        session.commit()

        # File is intentionally not on disk
        assert not rev_file.exists()

        # Run fsck check
        res = check_project(project_dir, session, auto_fix=False)
        assert res["status"] == "CORRUPTED"
        assert res["errors"][0]["type"] == "MISSING_FILE"

        # Run fsck with auto_fix=True
        fix_res = check_project(project_dir, session, auto_fix=True)
        assert fix_res["auto_fixed"] == 1
        assert rev_file.exists()
        assert rev_file.read_text(encoding="utf-8") == content


def test_fsck_hash_mismatch_and_conflict_resolution(tmp_path: Path):
    project_dir = tmp_path / "project_conflict"
    db_path = project_dir / ".novelagent" / "project.db"
    _, factory = make_session_factory(db_path)

    with factory() as session:
        proj = Project(path=str(project_dir), name="冲突项目")
        session.add(proj)
        session.flush()

        ch = Chapter(project_id=proj.id, title="第1章", sequence=1)
        session.add(ch)
        session.flush()

        sc = Scene(chapter_id=ch.id, title="第1场", sequence=1)
        session.add(sc)
        session.flush()

        rev = SceneRevision(scene_id=sc.id, content="数据库正典文本", content_hash="db_hash", source="AUTHOR")
        session.add(rev)
        session.flush()
        sc.current_revision_id = rev.id

        rev_file = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{sc.id}" / f"rev-{rev.id}.md"
        rev_file.parent.mkdir(parents=True, exist_ok=True)
        rev_file.write_text("磁盘被外部修改过的文本", encoding="utf-8")

        from novelagent.infrastructure.security import hash_text
        journal = CommitJournal(
            revision_id=rev.id,
            content_hash=hash_text("数据库正典文本"),
            file_path=str(rev_file),
            file_status="COMMITTED",
        )
        session.add(journal)
        session.commit()

        # FSCK detects HASH_MISMATCH
        res = check_project(project_dir, session, auto_fix=False)
        assert res["status"] == "CORRUPTED"
        assert any(e["type"] == "HASH_MISMATCH" for e in res["errors"])

        # Test Option 1: resolve with SQLITE (overwrite disk with DB)
        resolve_hash_conflict(project_dir, session, journal.id, "SQLITE")
        assert rev_file.read_text(encoding="utf-8") == "数据库正典文本"

        # Test Option 2: resolve with FILE
        rev_file.write_text("二次修改的文本", encoding="utf-8")
        resolve_hash_conflict(project_dir, session, journal.id, "FILE")
        assert session.get(SceneRevision, rev.id).content == "二次修改的文本"

        # Test Option 3: resolve with DUAL (create fork branch)
        rev_file.write_text("分支版本文本", encoding="utf-8")
        dual_res = resolve_hash_conflict(project_dir, session, journal.id, "DUAL")
        assert dual_res["applied"] == "DUAL_BRANCH_CREATED"
        new_rev_id = dual_res["new_revision_id"]
        assert session.get(SceneRevision, new_rev_id).content == "分支版本文本"
        assert session.get(Scene, sc.id).current_revision_id == new_rev_id


def test_fsck_orphan_file_and_projections(tmp_path: Path):
    project_dir = tmp_path / "project_orphan"
    db_path = project_dir / ".novelagent" / "project.db"
    _, factory = make_session_factory(db_path)

    with factory() as session:
        proj = Project(path=str(project_dir), name="孤儿检测")
        session.add(proj)
        session.flush()

        # Add a PendingProjection
        pending = PendingProjection(revision_id=1, projection_type="FTS", status="PENDING")
        session.add(pending)
        session.commit()

        orphan_file = project_dir / ".novelagent" / "text" / "scenes" / "scene-1" / "rev-999.md"
        orphan_file.parent.mkdir(parents=True, exist_ok=True)
        orphan_file.write_text("孤儿文件", encoding="utf-8")

        res = check_project(project_dir, session, auto_fix=False)
        assert any(e["type"] == "ORPHAN_FILE" for e in res["errors"])
        assert any(e["type"] == "PENDING_PROJECTION" for e in res["errors"])

        # Auto-fix marks pending projections completed
        fix_res = check_project(project_dir, session, auto_fix=True)
        assert fix_res["auto_fixed"] >= 1
        assert session.get(PendingProjection, pending.id).status == "COMPLETED"


def test_backup_export_and_restore(tmp_path: Path):
    project_dir = tmp_path / "my_novel"
    db_path = project_dir / ".novelagent" / "project.db"
    _, factory = make_session_factory(db_path)

    with factory() as session:
        proj = Project(path=str(project_dir), name="我的长篇小说")
        session.add(proj)
        session.flush()

        ch1 = Chapter(project_id=proj.id, title="第一章", sequence=1)
        session.add(ch1)
        session.flush()

        sc1 = Scene(chapter_id=ch1.id, title="场景一", sequence=1)
        session.add(sc1)
        session.flush()

        rev1 = SceneRevision(scene_id=sc1.id, content="小说开篇正文。", content_hash="h1")
        session.add(rev1)
        session.flush()
        sc1.current_revision_id = rev1.id
        session.commit()

        # 1. Export novel
        md_export = export_project_novel(session, proj.id, export_format="markdown")
        assert "我的长篇小说" in md_export["content"]
        assert "小说开篇正文。" in md_export["content"]

        json_export = export_project_novel(session, proj.id, export_format="json")
        assert len(json_export["chapters"]) == 1

        # 2. Backup project
        backup_file = create_project_backup(project_dir)
        assert backup_file.is_file()

        # 3. Restore to new directory
        restore_dir = tmp_path / "restored_novel"
        restore_res = restore_project_backup(backup_file, restore_dir)
        assert restore_res["status"] == "ok"
        assert (restore_dir / ".novelagent" / "project.db").is_file()

        # 4. Path traversal protection test
        import pytest
        import tarfile
        malicious_tar = tmp_path / "malicious.tar.gz"
        with tarfile.open(malicious_tar, "w:gz") as tar:
            import io
            dummy_data = b"malicious content"
            ti = tarfile.TarInfo(name="../escape.txt")
            ti.size = len(dummy_data)
            tar.addfile(ti, io.BytesIO(dummy_data))
        with pytest.raises(ValueError, match="非法路径遍历"):
            restore_project_backup(malicious_tar, restore_dir)


def test_phase5_api_endpoints(tmp_path: Path):
    project_dir = tmp_path / "api_project"
    project_dir.mkdir()
    source_dir = tmp_path / "import_source"
    source_dir.mkdir()

    (source_dir / "ch1.md").write_text("# 第一章 烽火\n\n## 场景一\n\n烽火连三月。", encoding="utf-8")
    (source_dir / "ch2.md").write_text("# 第二章 家书\n\n## 场景一\n\n家书抵万金。", encoding="utf-8")

    app = create_app(Settings())
    client = TestClient(app)

    token_res = client.get("/api/session")
    token = token_res.json()["token"]
    headers = {"X-NovelAgent-Token": token}

    # Authorize directories
    client.post(
        "/api/workspaces/select-directory",
        headers=headers,
        json={"current_path": str(project_dir), "history_paths": [str(source_dir)]},
    )

    # Open project
    client.post("/api/projects/open", headers=headers, json={"path": str(project_dir)})

    # Create batch import job
    import_res = client.post(
        "/api/projects/current/import-jobs",
        headers=headers,
        json={"source_path": str(source_dir), "batch_size": 1, "auto_extract": False},
    )
    assert import_res.status_code == 200
    data = import_res.json()
    job_id = data["job_id"]
    assert data["total_files"] == 2

    # Query import job
    job_get = client.get(f"/api/import-jobs/{job_id}", headers=headers)
    assert job_get.status_code == 200

    # List jobs
    list_res = client.get("/api/import-jobs", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Run FSCK API
    fsck_res = client.post("/api/projects/current/fsck", headers=headers)
    assert fsck_res.status_code == 200

    # Run FSCK fix API
    fsck_fix = client.post("/api/projects/current/fsck/fix", headers=headers)
    assert fsck_fix.status_code == 200

    # Backup API
    backup_res = client.post("/api/projects/current/backup", headers=headers, json={})
    assert backup_res.status_code == 200
    assert "output_path" in backup_res.json()

    # Export API
    export_res = client.post("/api/projects/current/export", headers=headers, json={"format": "markdown"})
    assert export_res.status_code == 200
    assert "content" in export_res.json()

    # Query checkpoints
    chk_res = client.get(f"/api/import-jobs/{job_id}/checkpoints", headers=headers)
    assert chk_res.status_code == 200

    # Test Cancel
    cancel_res = client.delete(f"/api/import-jobs/{job_id}", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
