from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.quality_rules import (
    detect_cliche_patterns,
    detect_semantic_duplicates,
    detect_vague_and_no_progress,
    detect_voice_drift,
    extract_voice_statistics,
)
from novelagent.infrastructure.db import Base
from novelagent.integrations.model_gateway import ModelConfig, ModelRouter


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase9.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    state.authorized_dirs.add(tmp_path)
    state.project_dir = tmp_path
    state.engine = engine
    state.session_factory = factory

    c = TestClient(app)
    c.headers.update({"X-NovelAgent-Token": state.session_token})
    c.post("/api/projects/open", json={"path": str(tmp_path)})
    return c, tmp_path, state.session_factory


def test_beat_advancement_and_stop_condition(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第一章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "破庙夜谈"}).json()["id"]

    # 1. Create Beat contract
    beat = c.post(
        f"/api/scenes/{sc_id}/beats",
        json={
            "required_advancements": [{"type": "NEW_ACTION", "description": "林舟决定夜探古寺"}],
            "stop_conditions": [{"type": "WORD_COUNT", "target": 500, "tolerance": 0.2}],
            "target_word_count": 500,
            "max_word_count": 800,
        },
    ).json()
    assert beat["status"] == "PENDING"
    assert beat["target_word_count"] == 500

    # 2. Advance beat
    adv = c.post(
        f"/api/beats/{beat['id']}/advance",
        json={"advancement": {"type": "NEW_ACTION", "description": "林舟推门进入古寺"}},
    ).json()
    assert adv["status"] == "COMPLETED"

    # 3. Stop beat
    stopped = c.post(f"/api/beats/{beat['id']}/stop", json={"reason": "DONE", "actual_word_count": 520}).json()
    assert stopped["status"] == "STOPPED"
    assert stopped["actual_word_count"] == 520


def test_semantic_duplicate_and_vague_detection():
    paras = [
        "林舟按住了腰间的长剑，目光冷冷地扫过四周的黑衣人。",
        "林舟握紧了腰间配剑，冷冽的目光看向周围这群黑衣刺客。",  # high character overlap
        "周围的空气似乎隐隐约约有一种说不出的寒意，林舟静静地看着这一切。",  # vague description
    ]

    dups = detect_semantic_duplicates(paras, threshold=0.6)
    assert len(dups) >= 1
    assert dups[0]["issue_type"] == "SEMANTIC_DUPLICATE"

    vagues = detect_vague_and_no_progress(paras)
    assert len(vagues) >= 1
    assert vagues[0]["issue_type"] == "EMPTY_DESCRIPTION"


def test_cliche_blacklist_and_genre_scan(client):
    c, _, _ = client
    # 1. Add cliche blacklist entry
    c.post(
        "/api/cliche-blacklist",
        json={
            "pattern": "不知不觉中",
            "pattern_type": "EXACT",
            "category": "GENERAL",
            "severity": "WARNING",
            "suggestion": "替换为具体时间推移动作",
        },
    )
    c.post(
        "/api/cliche-blacklist",
        json={
            "pattern": "事情并没有那么简单",
            "pattern_type": "EXACT",
            "category": "GENERIC_TRANSITION",
            "genre": "SUSPENSE",
            "severity": "WARNING",
        },
    )

    # 2. Scan text
    text = "不知不觉中，天色已经暗了下来，然而事情并没有那么简单。"
    hits = c.post("/api/cliche-blacklist/scan", json={"text": text, "genre": "SUSPENSE"}).json()
    assert len(hits) == 2
    assert any("不知不觉中" in h["source_text"] for h in hits)
    assert any("事情并没有那么简单" in h["source_text"] for h in hits)


def test_voice_fingerprint_extraction_and_drift(client):
    c, _, _ = client
    # 1. Create character
    char_id = c.post("/api/characters", json={"name": "林舟"}).json()["id"]

    # 2. Add forbidden lexicon entry
    c.post(
        "/api/voice-lexicons",
        json={
            "character_id": char_id,
            "lexicon_type": "FORBIDDEN",
            "entry_type": "MODERN_SLANG",
            "pattern": "绝绝子",
            "pattern_type": "EXACT",
        },
    )

    # 3. Create canonical scene with character dialogue
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第2章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "论道"}).json()["id"]
    content = "林舟道：'道之所在，虽千万人吾往矣。此乃剑心也，岂容退缩？'"
    p = c.post(f"/api/scenes/{sc_id}/patches", json={"content": content, "source": "AUTHOR"}).json()
    c.post(f"/api/scenes/{sc_id}/revisions/{p['revision_id']}/accept")

    # 4. Extract voice fingerprint
    fp = c.post(f"/api/characters/{char_id}/voice-fingerprint/extract").json()
    assert fp["character_id"] == char_id
    assert fp["classical_ratio"] > 0.0

    # 5. Check voice drift
    drift = c.post("/api/voice-drift-check", json={"character_id": char_id, "text": "林舟说：'这把宝剑真是绝绝子！'"}).json()
    assert len(drift) >= 1
    assert any("绝绝子" in d["source_text"] for d in drift)


def test_quality_report_and_author_feedback_ignore(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第3章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "质检场景"}).json()["id"]

    # Add cliche entry
    c.post("/api/cliche-blacklist", json={"pattern": "阳光明媚的一天", "category": "EMPTY_OPENING"})

    # Check quality
    text = "阳光明媚的一天。阳光明媚的一天。\n周围的空气似乎隐隐约约有一种说不出的怪异。"
    report = c.post(f"/api/scenes/{sc_id}/quality-check", json={"text_content": text}).json()
    assert report["summary"]["total"] >= 1
    assert any(i["issue_type"] == "CLICHE" for i in report["issues"])

    # Author feedback to IGNORE cliche in this scene
    fb = c.post(
        "/api/author-feedback",
        json={
            "issue_type": "CLICHE",
            "decision": "IGNORE",
            "scope": "THIS_SCENE",
            "scene_id": sc_id,
            "reason": "特殊意象开场",
        },
    ).json()
    assert fb["decision"] == "IGNORE"

    # Re-run quality check: cliche should now be suppressed
    report2 = c.post(f"/api/scenes/{sc_id}/quality-check", json={"text_content": text}).json()
    assert not any(i["issue_type"] == "CLICHE" for i in report2["issues"])


def test_model_router_tiers_and_degradation():
    cfg = ModelConfig(endpoint="mock://", models={"T1": "gpt-mini", "T2": "gpt-mid", "T3": "gpt-pro"})
    router = ModelRouter(cfg)

    # 1. T0 Rule tasks
    t0_tier, _ = router.route("rules_eval")
    assert t0_tier == "T0"
    assert router.get_degraded_tier("T0") is None  # T0 must not degrade

    # 2. T1/T2/T3 Routing
    assert router.route("cliche_scan")[0] == "T1"
    assert router.route("beat_plan")[0] == "T2"
    assert router.route("full_scene_generation")[0] == "T3"

    # 3. Degradation chain
    assert router.get_degraded_tier("T3") == "T2"
    assert router.get_degraded_tier("T2") == "T1"
    assert router.get_degraded_tier("T1") is None
