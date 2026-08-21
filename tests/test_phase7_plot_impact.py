from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.rules import check_character_knowledge_violation
from novelagent.infrastructure.db import Base


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase7.db"
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


def test_plot_thread_lifecycle_events_and_cascade_delete(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "主线章"}).json()["id"]
    sc1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "开局"}).json()["id"]
    sc2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "终局"}).json()["id"]

    # 1. Create thread
    t_resp = c.post(
        "/api/plot-threads",
        json={"name": "寻找失落的神剑", "thread_type": "MAIN", "priority": 1, "start_scene_id": sc1},
    )
    assert t_resp.status_code == 200
    t_id = t_resp.json()["id"]

    # 2. Add events
    ev1 = c.post(
        f"/api/plot-threads/{t_id}/events",
        json={"plot_thread_id": t_id, "event_type": "DEVELOPMENT", "scene_id": sc1, "description": "在古刹获得线索"},
    )
    assert ev1.status_code == 200

    ev2 = c.post(
        f"/api/plot-threads/{t_id}/events",
        json={"plot_thread_id": t_id, "event_type": "RESOLUTION", "scene_id": sc2, "description": "拔出神剑，剧情闭环"},
    )
    assert ev2.status_code == 200

    thread_view = c.get(f"/api/plot-threads/{t_id}").json()
    assert thread_view["status"] == "RESOLVED"

    # 3. Test cascade deletion of plot thread and events
    del_res = c.delete(f"/api/plot-threads/{t_id}")
    assert del_res.status_code == 200
    assert c.get(f"/api/plot-threads/{t_id}").status_code == 404
    assert len(c.get(f"/api/plot-threads/{t_id}/events").json()) == 0 or c.get(f"/api/plot-threads/{t_id}/events").status_code == 404


def test_foreshadowing_lifecycle_scheduling_and_update(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第1章"}).json()["id"]
    sc1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "埋设场景"}).json()["id"]
    sc2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "触发场景"}).json()["id"]

    # 1. Create foreshadowing
    f_resp = c.post(
        "/api/foreshadowings",
        json={
            "name": "古井下的密道",
            "setup_scene_id": sc1,
            "target_chapter_start": 1,
            "target_chapter_end": 5,
            "trigger_condition_type": "CHARACTER_ARRIVES",
            "trigger_condition_params": {"character_id": 1, "location": "后院古井"},
        },
    )
    assert f_resp.status_code == 200
    f_id = f_resp.json()["id"]

    # 2. Update foreshadowing
    upd = c.put(f"/api/foreshadowings/{f_id}", json={"priority": "MAIN", "name": "古井下的惊天密道"})
    assert upd.status_code == 200
    assert upd.json()["priority"] == "MAIN"

    # 3. Schedule for scene
    sched = c.get(f"/api/scenes/{sc2}/foreshadowings/scheduled").json()
    assert len(sched) >= 1
    assert sched[0]["foreshadowing_id"] == f_id

    # 4. Payoff foreshadowing
    payoff = c.post(f"/api/foreshadowings/{f_id}/payoff", json={"payoff_scene_id": sc2, "description": "主角跳下古井发现密道"})
    assert payoff.status_code == 200
    assert payoff.json()["status"] == "PAYOFF"


def test_scene_transition_contracts_merging_and_cut(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "过渡章"}).json()["id"]
    sc1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "场景A"}).json()["id"]
    sc2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "场景B"}).json()["id"]

    # 1. Set contracts and verify merging without wipe
    c.put(f"/api/scenes/{sc1}/contracts", json={"exit_state": {"narrative_time": "12:00", "injured_characters": ["林舟"], "pending_action": "combat"}})
    c.put(f"/api/scenes/{sc1}/contracts", json={"entry_contract": {"location": "古庙", "pov": "林舟"}})
    c.put(f"/api/scenes/{sc1}/contracts", json={"entry_contract": {"time_jump": "none"}})
    
    # Check scene contracts retain previous fields
    sc1_res = c.get(f"/api/scenes/{sc1}/transition-report").json()
    assert sc1_res["scene_id"] == sc1

    # Check normal transition (expect conflict on injury recovery)
    res = c.post(
        f"/api/scenes/{sc2}/check-transition",
        json={"prev_scene_id": sc1, "entry_contract_override": {"narrative_time": "12:30", "healthy_characters": ["林舟"]}},
    ).json()
    assert res["status"] == "CONFLICT"

    # Intentional Cut bypass
    cut_res = c.post(
        f"/api/scenes/{sc2}/check-transition",
        json={"prev_scene_id": sc1, "entry_contract_override": {"intentional_cut": True}},
    ).json()
    assert cut_res["status"] == "INTENTIONAL_CUT"


def test_impact_graph_nodes_edges_and_propagation(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "影响章"}).json()["id"]
    sc1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "源场景"}).json()["id"]
    sc2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "受影响场景"}).json()["id"]

    # Create Impact Nodes
    n1 = c.post("/api/impact-graph/nodes", json={"node_type": "CLAIM", "entity_type": "character", "scene_id": sc1}).json()
    n2 = c.post("/api/impact-graph/nodes", json={"node_type": "SCENE_REVISION", "scene_id": sc2}).json()

    # Create Impact Edge
    e = c.post("/api/impact-graph/edges", json={"source_node_id": n1["id"], "target_node_id": n2["id"], "edge_type": "CONTINUES"}).json()
    assert e["source_node_id"] == n1["id"]

    # Simulate BFS Propagation
    prop = c.post("/api/impact-graph/propagate", json={"changed_node_id": n1["id"], "change_type": "MODIFIED"}).json()
    assert sc2 in prop["affected_scenes"]
    assert n2["id"] in prop["stale_nodes"]

    # Impact report for scene
    rep = c.get(f"/api/scenes/{sc2}/impact-report").json()
    assert rep["scene_id"] == sc2
    assert rep["nodes_count"] >= 1

    # Project Impact summary
    summ = c.get("/api/projects/current/impact-summary").json()
    assert summ["total_nodes"] >= 2
    assert summ["total_edges"] >= 1

    # Knowledge violation helper test
    assert check_character_knowledge_violation(1, {10, 20}, [10, 30]) == [30]
    assert check_character_knowledge_violation(0, {10, 20}, [10, 30]) == []
