from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from novelagent.api import create_app
from novelagent.config import Settings
from novelagent.infrastructure.fsck import check_project


@pytest.fixture
def client(tmp_path: Path):
    project_dir = tmp_path / "my_novel"
    project_dir.mkdir()
    settings = Settings()
    app = create_app(settings)
    test_client = TestClient(app)

    # Fetch token
    res = test_client.get("/api/session")
    token = res.json()["token"]
    test_client.headers.update({"X-NovelAgent-Token": token})

    # Select directory & open project
    test_client.post("/api/workspaces/select-directory", json={"current_path": str(project_dir)})
    test_client.post("/api/projects/open", json={"path": str(project_dir)})

    return test_client, project_dir


def test_workspace_crud_and_auto_save(client):
    c, _ = client
    # Create chapter & scene
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第一章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "第一场"}).json()["id"]

    # 1. GET workspace (should auto-create default workspace)
    ws = c.get(f"/api/scenes/{sc_id}/workspace").json()
    assert ws["scene_id"] == sc_id
    assert ws["draft_content"] == ""
    assert ws["cursor_position"] == 0

    # 2. PUT workspace (update draft & stacks)
    update_res = c.put(f"/api/scenes/{sc_id}/workspace", json={
        "draft_content": "林舟在客栈窗前沉思。",
        "cursor_position": 10,
        "selection_start": 2,
        "selection_end": 4,
        "undo_stack": [{"draft_content": "", "cursor_position": 0}],
        "auto_save_snapshot": {
            "draft_content": "林舟在客栈窗前沉思。",
            "cursor_position": 10,
            "timestamp": "2026-08-20T16:00:00Z"
        }
    })
    assert update_res.status_code == 200
    ws_updated = update_res.json()
    assert ws_updated["draft_content"] == "林舟在客栈窗前沉思。"
    assert ws_updated["cursor_position"] == 10
    assert len(ws_updated["undo_stack"]) == 1

    # 3. Snapshot & Restore
    snap_res = c.post(f"/api/scenes/{sc_id}/workspace/snapshot")
    assert snap_res.status_code == 200
    assert snap_res.json()["auto_save_snapshot"]["draft_content"] == "林舟在客栈窗前沉思。"

    # Modify draft then restore
    c.put(f"/api/scenes/{sc_id}/workspace", json={"draft_content": "被污染的草稿"})
    restore_res = c.post(f"/api/scenes/{sc_id}/workspace/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["draft_content"] == "林舟在客栈窗前沉思。"

    # 4. DELETE / reset workspace
    del_res = c.delete(f"/api/scenes/{sc_id}/workspace")
    assert del_res.status_code == 200
    assert del_res.json()["draft_content"] == ""


def test_text_patch_insert_delete_replace(client):
    c, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第二章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "补丁测试场"}).json()["id"]

    # Base revision: "林舟按住剑柄。"
    rev1_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "林舟按住剑柄。"}).json()["revision_id"]
    c.post(f"/api/scenes/{sc_id}/revisions/{rev1_id}/accept")

    # 1. Insert patch: at index 2 insert "快步" -> "林舟快步按住剑柄。"
    patch_insert = {
        "base_revision_id": rev1_id,
        "range_start": 2,
        "range_end": 2,
        "new_content": "快步",
        "source": "AUTHOR",
        "intent": "insert",
    }
    res_ins = c.post(f"/api/scenes/{sc_id}/text-patches", json=patch_insert)
    assert res_ins.status_code == 200
    rev2_id = res_ins.json()["revision_id"]
    rev2_data = c.get(f"/api/scenes/{sc_id}/revisions/{rev2_id}").json()
    assert rev2_data["content"] == "林舟快步按住剑柄。"
    assert rev2_data["patch_info"]["intent"] == "insert"

    # Accept rev2
    c.post(f"/api/scenes/{sc_id}/revisions/{rev2_id}/accept")

    # 2. Replace patch: replace "剑柄" with "刀柄" -> "林舟快步按住刀柄。"
    patch_replace = {
        "base_revision_id": rev2_id,
        "range_start": 6,
        "range_end": 8,
        "new_content": "刀柄",
        "source": "AI",
        "intent": "replace",
    }
    res_rep = c.post(f"/api/scenes/{sc_id}/text-patches", json=patch_replace)
    assert res_rep.status_code == 200
    rev3_id = res_rep.json()["revision_id"]
    rev3_data = c.get(f"/api/scenes/{sc_id}/revisions/{rev3_id}").json()
    assert rev3_data["content"] == "林舟快步按住刀柄。"

    # 3. Delete patch: delete "快步" -> "林舟按住刀柄。"
    c.post(f"/api/scenes/{sc_id}/revisions/{rev3_id}/accept")
    patch_del = {
        "base_revision_id": rev3_id,
        "range_start": 2,
        "range_end": 4,
        "new_content": "",
        "source": "AUTHOR",
        "intent": "delete",
    }
    res_del = c.post(f"/api/scenes/{sc_id}/text-patches", json=patch_del)
    assert res_del.status_code == 200
    rev4_id = res_del.json()["revision_id"]
    rev4_data = c.get(f"/api/scenes/{sc_id}/revisions/{rev4_id}").json()
    assert rev4_data["content"] == "林舟按住刀柄。"


def test_text_patch_conflict_detection(client):
    c, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第三章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "冲突测试场"}).json()["id"]

    rev1_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "原始内容"}).json()["revision_id"]
    c.post(f"/api/scenes/{sc_id}/revisions/{rev1_id}/accept")

    # Range out of bounds -> 400
    bad_range = {
        "base_revision_id": rev1_id,
        "range_start": 10,
        "range_end": 20,
        "new_content": "超出范围",
    }
    assert c.post(f"/api/scenes/{sc_id}/text-patches", json=bad_range).status_code == 400

    # Advance scene to rev2
    rev2_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "已更新的内容", "base_revision_id": rev1_id}).json()["revision_id"]
    c.post(f"/api/scenes/{sc_id}/revisions/{rev2_id}/accept")

    # Stale base_revision_id (rev1 instead of rev2) -> 409 Conflict
    stale_patch = {
        "base_revision_id": rev1_id,
        "range_start": 0,
        "range_end": 2,
        "new_content": "过期修改",
    }
    conflict_res = c.post(f"/api/scenes/{sc_id}/text-patches", json=stale_patch)
    assert conflict_res.status_code == 409
    assert conflict_res.json()["detail"]["current_revision_id"] == rev2_id


def test_patch_merge_no_overlap_and_overlap_conflict(client):
    c, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第四章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "合并测试场"}).json()["id"]

    # Base: "AAAA BBBB CCCC"
    rev1_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "AAAA BBBB CCCC"}).json()["revision_id"]
    c.post(f"/api/scenes/{sc_id}/revisions/{rev1_id}/accept")

    # Non-overlapping: patch1 modifies AAAA(0..4) -> 1111, patch2 modifies CCCC(10..14) -> 2222
    patches = [
        {"range_start": 0, "range_end": 4, "new_content": "1111", "source": "AI"},
        {"range_start": 10, "range_end": 14, "new_content": "2222", "source": "AI"},
    ]
    merge_res = c.post(f"/api/scenes/{sc_id}/patches/merge", json={
        "base_revision_id": rev1_id,
        "patches": patches,
    })
    assert merge_res.status_code == 200
    assert merge_res.json()["merged_content"] == "1111 BBBB 2222"

    # Overlapping: patch1 (0..6), patch2 (5..10) -> Overlap conflict 409
    overlap_patches = [
        {"range_start": 0, "range_end": 6, "new_content": "111111", "source": "AI"},
        {"range_start": 5, "range_end": 10, "new_content": "22222", "source": "AI"},
    ]
    overlap_res = c.post(f"/api/scenes/{sc_id}/patches/merge", json={
        "base_revision_id": rev1_id,
        "patches": overlap_patches,
    })
    assert overlap_res.status_code == 409


def test_selective_accept_patches(client):
    c, project_dir = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第五章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "局部采纳场"}).json()["id"]

    rev1_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "第一段。第二段。第三段。"}).json()["revision_id"]
    c.post(f"/api/scenes/{sc_id}/revisions/{rev1_id}/accept")

    # Selectively accept 2 non-overlapping patches
    patches = [
        {"range_start": 0, "range_end": 4, "new_content": "新第一段。", "source": "AI"},
        {"range_start": 8, "range_end": 12, "new_content": "新第三段。", "source": "AI"},
    ]
    accept_res = c.post(f"/api/scenes/{sc_id}/patches/selective-accept", json={
        "base_revision_id": rev1_id,
        "patches": patches,
    })
    assert accept_res.status_code == 200
    new_rev_id = accept_res.json()["revision_id"]
    assert accept_res.json()["status"] == "SCENE_ACCEPTED"

    # Verify content
    rev_data = c.get(f"/api/scenes/{sc_id}/revisions/{new_rev_id}").json()
    assert rev_data["content"] == "新第一段。第二段。新第三段。"

    # Verify fsck
    _, factory = c.app.state.novelagent.require_project()
    with factory() as session:
        fsck_res = check_project(project_dir, session)
        assert fsck_res["ok"] is True


def test_revision_diff(client):
    c, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第六章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "Diff测试场"}).json()["id"]

    rev1_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "夜色深沉\n客栈寂静"}).json()["revision_id"]
    rev2_id = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "夜色深沉\n客栈灯火通明"}).json()["revision_id"]

    diff_res = c.get(f"/api/scenes/{sc_id}/revisions/{rev2_id}/diff?against={rev1_id}")
    assert diff_res.status_code == 200
    diff = diff_res.json()
    assert diff["base_revision_id"] == rev1_id
    assert diff["target_revision_id"] == rev2_id
    assert "灯火通明" in diff["unified_diff"]
    assert diff["additions"] >= 1
    assert diff["deletions"] >= 1
