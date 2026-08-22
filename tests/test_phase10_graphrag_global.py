from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.graphrag_rules import (
    analyze_character_arc,
    analyze_foreshadow_fulfillment,
    analyze_plot_ruptures,
    calculate_feedback_optimization_suggestions,
    detect_logical_communities,
)
from novelagent.infrastructure.db import Base


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase10.db"
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


def test_community_auto_detect_and_summaries(client):
    c, _, _ = client
    # 1. Create Volume and Plot Thread
    res_vol = c.post("/api/projects/current/volumes", json={"title": "第一卷 风起青萍"})
    assert res_vol.status_code == 200
    res_pt = c.post("/api/plot-threads", json={"name": "夜探古刹线", "priority": 1, "thread_type": "MAIN"})
    assert res_pt.status_code == 200

    # 2. Auto-detect communities
    comms = c.post("/api/communities/auto-detect").json()
    assert len(comms) >= 2
    vol_comm = next(comm for comm in comms if comm["community_type"] == "VOLUME")
    assert "第一卷" in vol_comm["name"]

    # 3. Generate summary
    summary = c.post(f"/api/communities/{vol_comm['id']}/summaries/generate?summary_type=OVERVIEW").json()
    assert summary["community_id"] == vol_comm["id"]
    assert summary["status"] == "VALID"
    assert summary["token_count"] > 0

    # 4. Invalidate by entity
    inv = c.post("/api/communities/invalidate?entity_type=VOLUME").json()
    assert inv["invalidated_count"] >= 1
    updated_comm = c.get(f"/api/communities/{vol_comm['id']}").json()
    assert updated_comm["status"] == "STALE"


def test_graphrag_query_execution(client):
    c, _, _ = client
    # 1. Create character and community
    char = c.post("/api/characters", json={"name": "林舟"}).json()
    comm = c.post("/api/communities", json={"name": "青云宗", "community_type": "FACTION"}).json()
    c.post(f"/api/communities/{comm['id']}/summaries/generate")

    # 2. Query GraphRAG
    res = c.post(
        "/api/graphrag/query",
        json={
            "query_type": "CROSS_VOLUME",
            "query_text": "林舟在各卷中的关系发展",
            "parameters": {"include_communities": [comm["id"]]},
        },
    ).json()
    assert res["status"] == "COMPLETED"
    assert res["query_type"] == "CROSS_VOLUME"
    assert "林舟" in res["result"]["answer"]

    # 3. Retrieve history
    history = c.get("/api/graphrag/queries").json()
    assert len(history) >= 1
    assert history[0]["id"] == res["id"]


def test_global_analysis_audits(client):
    c, _, _ = client
    # 1. Setup Character, State, Foreshadowing and Plot Thread
    char_id = c.post("/api/characters", json={"name": "林舟"}).json()["id"]
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第一章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "古刹惊变"}).json()["id"]

    res_st = c.post(
        f"/api/characters/{char_id}/states",
        json={"scene_id": sc_id, "location": "青云山脚", "emotion": "警惕", "arc_stage": "初入江湖", "confirmed": True},
    )
    assert res_st.status_code == 200

    res_fo = c.post(
        "/api/foreshadowings",
        json={"name": "断剑之谜", "setup_scene_id": sc_id, "target_chapter_start": 1, "target_chapter_end": 5},
    )
    assert res_fo.status_code == 200

    res_pt = c.post("/api/plot-threads", json={"name": "寻找身世", "priority": 1, "thread_type": "MAIN"})
    assert res_pt.status_code == 200

    # 2. Character Arcs analysis
    arc_rep = c.post("/api/global-analysis/character-arcs").json()
    assert arc_rep["report_type"] == "CHARACTER_ARC"
    assert arc_rep["status"] == "COMPLETED"

    # 3. Relationship Network analysis
    rel_rep = c.post("/api/global-analysis/relationship-network").json()
    assert rel_rep["report_type"] == "RELATIONSHIP_NETWORK"

    # 4. Foreshadow Audit
    fore_rep = c.post("/api/global-analysis/foreshadow-audit").json()
    assert fore_rep["report_type"] == "FORESHADOW_AUDIT"
    assert fore_rep["content"]["total"] >= 1

    # 5. Plot Rupture Audit
    rup_rep = c.post("/api/global-analysis/plot-rupture").json()
    assert rup_rep["report_type"] == "PLOT_RUPTURE"


def test_model_stats_and_feedback_optimization(client):
    c, _, _ = client
    # 1. Trigger aggregation
    stats = c.post("/api/model-stats/aggregate").json()
    assert isinstance(stats, list)

    summary = c.get("/api/model-stats/summary").json()
    assert "total_calls" in summary
    assert "estimated_cost_usd" in summary

    # 2. Add author feedback
    c.post(
        "/api/author-feedback",
        json={"issue_type": "CLICHE", "decision": "IGNORE", "scope": "THIS_SCENE", "reason": "特殊修辞"},
    )
    c.post(
        "/api/author-feedback",
        json={"issue_type": "CLICHE", "decision": "IGNORE", "scope": "THIS_SCENE", "reason": "特殊修辞"},
    )
    c.post(
        "/api/author-feedback",
        json={"issue_type": "CLICHE", "decision": "IGNORE", "scope": "THIS_SCENE", "reason": "特殊修辞"},
    )

    # 3. Get optimization suggestions
    sug_res = c.get("/api/feedback-optimization/suggestions").json()
    assert sug_res["feedback_summary"]["total_feedback"] >= 3
    assert len(sug_res["suggestions"]) >= 1

    # 4. Apply optimization
    apply_res = c.post(
        "/api/feedback-optimization/apply",
        json={"issue_type": "CLICHE", "action": "SUPPRESS"},
    ).json()
    assert apply_res["status"] == "APPLIED"
    assert apply_res["scope"] == "ALWAYS"


def test_domain_graphrag_rules():
    # 1. Community detection
    vols = [{"id": 1, "title": "卷一"}]
    threads = [{"id": 1, "name": "主线", "priority": "MAIN"}]
    detected = detect_logical_communities(vols, threads, factions=["魔教"], custom_tags=["悬疑"])
    assert len(detected) == 4
    assert any(d["community_type"] == "VOLUME" for d in detected)
    assert any(d["community_type"] == "FACTION" for d in detected)

    # 2. Foreshadow fulfillment calculation
    foreshadows = [
        {"id": 1, "status": "RESOLVED", "target_chapter_end": 3},
        {"id": 2, "status": "ACTIVE", "target_chapter_end": 2},
    ]
    audit = analyze_foreshadow_fulfillment(foreshadows, current_scene_index=4)
    assert audit["fulfillment_rate"] == 0.5
    assert len(audit["overdue_items"]) == 1

    # 3. Plot rupture calculation
    ruptures = analyze_plot_ruptures(
        [{"id": 1, "name": "断裂主线", "status": "ACTIVE"}],
        [],
        scene_count=6,
    )
    assert len(ruptures) == 1
    assert ruptures[0]["issue_type"] == "DORMANT_PLOT_THREAD"
