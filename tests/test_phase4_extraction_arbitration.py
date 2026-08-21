from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.models import Base, CanonClaim, ClaimCandidate, EntityAlias
from novelagent.integrations.model_gateway import ModelConfig


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase4.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    state.authorized_dirs.add(tmp_path)
    state.project_dir = tmp_path
    state.engine = engine
    state.session_factory = factory
    state.model_config = ModelConfig(endpoint="mock://test")

    c = TestClient(app)
    c.headers.update({"X-NovelAgent-Token": state.session_token})
    c.post("/api/projects/open", json={"path": str(tmp_path)})
    return c, tmp_path, state.session_factory


def test_modality_inference_rules_and_extraction(client):
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "模态测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "模态测试场"}).json()["id"]

    # Add text with various modalities to workspace and accept revision
    sample_text = (
        "林舟按住寒铁剑，缓步推开客栈后门。\n"
        "他梦见自己在云端飞翔，四周尽是雷霆。\n"
        "李四听说城东的大盗昨夜被抓了。\n"
        "老掌柜回想起当年的往事，心中感慨万千。\n"
        "假如明日下雨，我们便暂留一日。\n"
        "他的心像石头一样坚硬，丝毫不为所动。"
    )
    c.put(f"/api/scenes/{sc_id}/workspace", json={"draft_content": sample_text})
    c.post(f"/api/scenes/{sc_id}/patches", json={"content": sample_text})

    # Trigger extraction
    res = c.post(f"/api/scenes/{sc_id}/extract", json={"force_full_scan": True})
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_count"] >= 5

    candidates = data["candidates"]
    modalities = {c["modality"] for c in candidates}
    assert "ACTUAL" in modalities
    assert "DREAMED" in modalities
    assert "REPORTED" in modalities
    assert "REMEMBERED" in modalities
    assert "HYPOTHETICAL" in modalities
    assert "METAPHORICAL" in modalities


def test_entity_alias_resolution_and_auto_confirm(client):
    c, _, factory = client
    # 1. Add alias: "阿舟" -> "林舟"
    alias_res = c.post("/api/entity-aliases", json={
        "canonical_name": "林舟",
        "alias_name": "阿舟",
        "alias_type": "informal",
    })
    assert alias_res.status_code == 200
    alias_id = alias_res.json()["id"]

    ch_id = c.post("/api/projects/current/chapters", json={"title": "别名测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "别名测试场"}).json()["id"]

    text = "阿舟来到客栈大堂，在窗边坐下。"
    c.post(f"/api/scenes/{sc_id}/patches", json={"content": text})

    # Extract claims
    extract_res = c.post(f"/api/scenes/{sc_id}/extract")
    assert extract_res.status_code == 200
    data = extract_res.json()
    assert data["auto_confirmed_count"] >= 1

    # Verify alias resolved to canonical name "林舟"
    cands = c.get(f"/api/scenes/{sc_id}/claim-candidates").json()
    resolved_cand = next((cand for cand in cands if cand["subject"] == "林舟"), None)
    assert resolved_cand is not None
    assert resolved_cand["status"] == "AUTO_CONFIRMED"

    # Verify auto-created CanonClaim
    canons = c.get(f"/api/scenes/{sc_id}/canon-claims").json()
    assert len(canons) >= 1
    assert canons[0]["subject"] == "林舟"
    assert canons[0]["auto_confirmed"] is True

    # Delete alias test
    del_res = c.delete(f"/api/entity-aliases/{alias_id}")
    assert del_res.status_code == 200


def test_manual_arbitration_and_conflict_detection(client):
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "仲裁测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "仲裁测试场"}).json()["id"]

    text = "赵六拿着青霜剑，冷冷注视着前方的黑衣人。"
    c.post(f"/api/scenes/{sc_id}/patches", json={"content": text})
    c.post(f"/api/scenes/{sc_id}/extract")

    cands = c.get(f"/api/scenes/{sc_id}/claim-candidates").json()
    assert len(cands) >= 1
    target_id = cands[0]["id"]

    # 1. Single Decision: Confirm
    dec_res = c.post(f"/api/claim-candidates/{target_id}/decision", json={
        "decision": "CONFIRM",
        "corrections": {"object_value": "青霜古剑"},
        "notes": "作者手动确认持有神剑",
    })
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "CONFIRMED"

    # Verify updated canon claim
    canons = c.get(f"/api/scenes/{sc_id}/canon-claims").json()
    confirmed = next(cn for cn in canons if cn["source_candidate_id"] == target_id)
    assert confirmed["object_value"] == "青霜古剑"
    assert confirmed["author_decision_notes"] == "作者手动确认持有神剑"

    # 2. Batch Decision Test
    batch_res = c.post(f"/api/scenes/{sc_id}/claim-candidates/batch-decision", json={
        "decisions": [
            {"id": target_id, "decision": "DEFER"},
        ]
    })
    assert batch_res.status_code == 200
    assert batch_res.json()["deferred_count"] == 1


def test_chapter_batch_extraction(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "批量抽取章"}).json()["id"]
    s1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "场1"}).json()["id"]
    s2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "场2"}).json()["id"]

    c.post(f"/api/scenes/{s1}/patches", json={"content": "张三推开了木门。"})
    c.post(f"/api/scenes/{s2}/patches", json={"content": "李四进入了暗室。"})

    batch_res = c.post(f"/api/chapters/{ch_id}/batch-extract")
    assert batch_res.status_code == 200
    data = batch_res.json()
    assert data["chapter_id"] == ch_id
    assert data["scene_count"] == 2
    assert data["candidate_count"] >= 2


def test_blocking_conflict_detection_across_claims(client):
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "冲突测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "冲突测试场"}).json()["id"]

    # 1. First character holds sword
    c.post(f"/api/scenes/{sc_id}/patches", json={"content": "张三按住青霜剑。"})
    c.post(f"/api/scenes/{sc_id}/extract")
    cands1 = c.get(f"/api/scenes/{sc_id}/claim-candidates").json()
    c.post(f"/api/claim-candidates/{cands1[0]['id']}/decision", json={"decision": "CONFIRM", "corrections": {"subject": "张三", "predicate": "holds", "object_value": "青霜剑", "modality": "ACTUAL"}})

    # 2. Second character holds same sword
    c.post(f"/api/scenes/{sc_id}/patches", json={"content": "李四拿着青霜剑。"})
    c.post(f"/api/scenes/{sc_id}/extract")
    cands2 = c.get(f"/api/scenes/{sc_id}/claim-candidates").json()
    c.post(f"/api/claim-candidates/{cands2[-1]['id']}/decision", json={"decision": "CONFIRM", "corrections": {"subject": "李四", "predicate": "holds", "object_value": "青霜剑", "modality": "ACTUAL"}})

    # Check conflicts
    conflicts_res = c.get(f"/api/claims/conflicts?scene_id={sc_id}").json()
    assert len(conflicts_res["conflicts"]) >= 1
    conflict = conflicts_res["conflicts"][0]
    assert conflict["severity"] == "BLOCKING_CONFIRMED"
    assert "青霜剑" in conflict["message"]

