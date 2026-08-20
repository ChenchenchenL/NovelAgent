from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from novelagent.api import create_app
from novelagent.config import Settings
from novelagent.domain.rules import (
    validate_chapter_status_transition,
    validate_scene_status_transition,
)
from novelagent.infrastructure.fsck import check_project


def test_chapter_status_transitions():
    # Valid transitions
    validate_chapter_status_transition("IDEA", "OUTLINED", [])
    validate_chapter_status_transition("OUTLINED", "IN_PROGRESS", [])
    validate_chapter_status_transition("IN_PROGRESS", "READY_FOR_REVIEW", ["SCENE_ACCEPTED"])
    validate_chapter_status_transition("READY_FOR_REVIEW", "RELEASED", ["SCENE_ACCEPTED", "SCENE_ACCEPTED"])
    validate_chapter_status_transition("RELEASED", "IN_PROGRESS", ["SCENE_ACCEPTED"])

    # Invalid: no scene accepted when moving to READY_FOR_REVIEW
    with pytest.raises(ValueError, match="SCENE_ACCEPTED"):
        validate_chapter_status_transition("IN_PROGRESS", "READY_FOR_REVIEW", ["PLANNED"])

    # Invalid: not all scenes accepted when moving to RELEASED
    with pytest.raises(ValueError, match="SCENE_ACCEPTED"):
        validate_chapter_status_transition("READY_FOR_REVIEW", "RELEASED", ["SCENE_ACCEPTED", "WRITING"])

    # Invalid transition jump
    with pytest.raises(ValueError, match="非法章节状态流转"):
        validate_chapter_status_transition("IDEA", "RELEASED", [])


def test_scene_status_transitions():
    validate_scene_status_transition("PLANNED", "WRITING")
    validate_scene_status_transition("WRITING", "PARTIALLY_ACCEPTED", has_content=True)
    validate_scene_status_transition("WRITING", "SCENE_ACCEPTED", has_content=True)
    validate_scene_status_transition("SCENE_ACCEPTED", "WRITING")

    with pytest.raises(ValueError, match="无正文内容"):
        validate_scene_status_transition("WRITING", "SCENE_ACCEPTED", has_content=False)

    with pytest.raises(ValueError, match="非法场景状态流转"):
        validate_scene_status_transition("PLANNED", "SCENE_ACCEPTED")


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(Settings())
    client = TestClient(app)
    # Get session token
    res = client.get("/api/session")
    token = res.json()["token"]
    client.headers.update({"X-NovelAgent-Token": token})

    # Authorize & open project
    project_dir = tmp_path / "my_novel"
    project_dir.mkdir()
    client.post("/api/workspaces/select-directory", json={"current_path": str(project_dir)})
    client.post("/api/projects/open", json={"path": str(project_dir)})
    return client, project_dir


def test_volume_crud(client):
    c, _ = client
    # 1. Create Volume
    res = c.post("/api/projects/current/volumes", json={"title": "第一卷 风起云涌"})
    assert res.status_code == 200, res.text
    vol_id = res.json()["id"]
    assert res.json()["title"] == "第一卷 风起云涌"
    assert res.json()["sequence"] == 1

    # Create second Volume
    res2 = c.post("/api/projects/current/volumes", json={"title": "第二卷 潜龙在渊"})
    assert res2.status_code == 200
    assert res2.json()["sequence"] == 2

    # List volumes
    res_list = c.get("/api/projects/current/volumes")
    assert len(res_list.json()) == 2

    # Update volume
    res_up = c.put(f"/api/volumes/{vol_id}", json={"title": "第一卷 风起"})
    assert res_up.status_code == 200
    assert res_up.json()["title"] == "第一卷 风起"

    # Create chapter under volume
    res_ch = c.post("/api/projects/current/chapters", json={"title": "卷内第一章", "volume_id": vol_id})
    assert res_ch.status_code == 200
    ch_id = res_ch.json()["id"]

    # Delete volume should fail because it has chapters
    res_del = c.delete(f"/api/volumes/{vol_id}")
    assert res_del.status_code == 400
    assert "包含章节" in res_del.json()["detail"]

    # Move chapter out or delete chapter
    c.delete(f"/api/chapters/{ch_id}")
    # Now delete volume succeeds
    res_del_ok = c.delete(f"/api/volumes/{vol_id}")
    assert res_del_ok.status_code == 200


def test_chapter_and_scene_management(client):
    c, project_dir = client
    # Create Chapter
    res_ch = c.post("/api/projects/current/chapters", json={"title": "第二章 暗流"})
    assert res_ch.status_code == 200
    ch_id = res_ch.json()["id"]

    # Update Chapter contract
    contract_data = {
        "chapter_id": ch_id,
        "title": "第二章 暗流",
        "goal": "揭示阴谋线索",
        "target_word_count": 3000,
    }
    res_up = c.put(f"/api/chapters/{ch_id}", json={"contract": contract_data})
    assert res_up.status_code == 200
    assert res_up.json()["contract"]["goal"] == "揭示阴谋线索"

    # Get single Chapter
    res_get = c.get(f"/api/chapters/{ch_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == ch_id
    assert res_get.json()["contract"]["target_word_count"] == 3000

    # Create Scene in Chapter
    res_sc = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "夜探古寺", "pov": "林舟", "location": "古寺"})
    assert res_sc.status_code == 200
    sc_id = res_sc.json()["id"]

    # Update Scene Contracts
    entry_contract = {
        "scene_id": sc_id,
        "location": "古寺大殿",
        "pov_character": "林舟",
    }
    res_ec = c.put(f"/api/scenes/{sc_id}/entry-contract", json={"entry_contract": entry_contract})
    assert res_ec.status_code == 200
    assert res_ec.json()["entry_contract"]["location"] == "古寺大殿"

    exit_state = {
        "scene_id": sc_id,
        "last_action": "发现暗格中的书信",
    }
    res_es = c.put(f"/api/scenes/{sc_id}/exit-state", json={"exit_state": exit_state})
    assert res_es.status_code == 200
    assert res_es.json()["exit_state"]["last_action"] == "发现暗格中的书信"

    # Create patch & accept revision
    patch_res = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "夜色深沉，古寺内一片寂静。"})
    assert patch_res.status_code == 200
    rev_id = patch_res.json()["revision_id"]

    accept_res = c.post(f"/api/scenes/{sc_id}/revisions/{rev_id}/accept")
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "SCENE_ACCEPTED"

    # Check immutable revision get
    rev_get = c.get(f"/api/scenes/{sc_id}/revisions/{rev_id}")
    assert rev_get.status_code == 200
    assert rev_get.json()["content"] == "夜色深沉，古寺内一片寂静。"

    # Check file exists and fsck passes
    rev_file = project_dir / ".novelagent" / "text" / "scenes" / f"scene-{sc_id}" / f"rev-{rev_id}.md"
    assert rev_file.exists()
    assert rev_file.read_text(encoding="utf-8") == "夜色深沉，古寺内一片寂静。"

    # Check fsck
    _, factory = c.app.state.novelagent.require_project()
    with factory() as session:
        fsck_res = check_project(project_dir, session)
        assert fsck_res["ok"] is True
        assert len(fsck_res["errors"]) == 0

    # Delete chapter with scenes should fail
    del_fail = c.delete(f"/api/chapters/{ch_id}")
    assert del_fail.status_code == 400


def test_reorder_api(client):
    c, _ = client
    # Create 3 volumes
    v1 = c.post("/api/projects/current/volumes", json={"title": "卷1"}).json()["id"]
    v2 = c.post("/api/projects/current/volumes", json={"title": "卷2"}).json()["id"]
    v3 = c.post("/api/projects/current/volumes", json={"title": "卷3"}).json()["id"]

    # Reorder volumes: v3, v1, v2
    reorder_res = c.put("/api/projects/current/reorder", json={
        "type": "volume",
        "order": [v3, v1, v2]
    })
    assert reorder_res.status_code == 200

    volumes = c.get("/api/projects/current/volumes").json()
    assert [v["id"] for v in volumes] == [v3, v1, v2]
    assert [v["sequence"] for v in volumes] == [1, 2, 3]

    # Reorder with invalid ID should fail
    bad_reorder = c.put("/api/projects/current/reorder", json={
        "type": "volume",
        "order": [v3, 99999]
    })
    assert bad_reorder.status_code == 400


def test_project_tree_api(client):
    c, _ = client
    # Tree should return structured volumes, chapters, scenes
    tree_res = c.get("/api/projects/current/tree")
    assert tree_res.status_code == 200
    tree = tree_res.json()
    assert "volumes" in tree
    assert "unassigned_chapters" in tree


def test_import_creates_files_and_journal_for_fsck(client, tmp_path):
    c, project_dir = client
    import_source = tmp_path / "import_source"
    import_source.mkdir()
    (import_source / "01.md").write_text("第一章导入正文内容", encoding="utf-8")

    # Authorize directory
    auth_res = c.post("/api/workspaces/select-directory", json={"current_path": str(project_dir), "history_paths": [str(import_source)]})
    assert auth_res.status_code == 200

    # Import
    imp_res = c.post("/api/projects/current/import", json={"source_path": str(import_source)})
    assert imp_res.status_code == 200
    assert imp_res.json()["files"] == 1

    # Verify fsck passes on imported files
    _, factory = c.app.state.novelagent.require_project()
    with factory() as session:
        fsck_res = check_project(project_dir, session)
        assert fsck_res["ok"] is True
        assert len(fsck_res["errors"]) == 0


def test_scene_revision_foreign_key(client):
    from novelagent.domain.models import Scene, SceneRevision
    c, _ = client
    _, factory = c.app.state.novelagent.require_project()
    with factory() as session:
        ch_res = c.post("/api/projects/current/chapters", json={"title": "外键测试章"})
        ch_id = ch_res.json()["id"]
        sc_res = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "外键测试场景"})
        sc_id = sc_res.json()["id"]

        patch_res = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "版本内容"})
        rev_id = patch_res.json()["revision_id"]
        c.post(f"/api/scenes/{sc_id}/revisions/{rev_id}/accept")

        scene = session.get(Scene, sc_id)
        assert scene.current_revision_id == rev_id

        # Delete the revision and verify current_revision_id is set to None
        rev = session.get(SceneRevision, rev_id)
        session.delete(rev)
        session.commit()
        session.refresh(scene)
        assert scene.current_revision_id is None
