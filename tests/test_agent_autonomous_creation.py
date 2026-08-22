from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.infrastructure.db import Base


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_agent_refactor.db"
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


def test_agent_auto_plan_novel_from_seed(client):
    c, _, _ = client
    # 1. Trigger Autonomous Novel Planning
    plan_res = c.post(
        "/api/agent/auto-plan",
        json={
            "seed_prompt": "赛博修仙：底层义体维修工林舟，在废弃金丹芯片中发现了万仙宗的灭门真相",
            "genre": "科幻仙侠",
            "target_volumes": 2,
            "chapters_per_vol": 2,
        },
    ).json()

    assert plan_res["project_id"] == 1
    assert "林舟" in plan_res["characters_created"]
    assert len(plan_res["volumes"]) == 2
    assert plan_res["total_scenes"] == 4
    assert plan_res["communities_count"] >= 2

    # Verify project tree
    tree = c.get("/api/projects/current/tree").json()
    assert len(tree["volumes"]) == 2
    assert len(tree["volumes"][0]["chapters"]) == 2


def test_agent_auto_write_scene_grounded(client):
    c, _, _ = client
    # 1. Initialize novel outline
    plan_res = c.post(
        "/api/agent/auto-plan",
        json={
            "seed_prompt": "悬疑仙侠：林舟夜探废弃古刹寻找失落剑胚",
            "target_volumes": 1,
            "chapters_per_vol": 1,
        },
    ).json()

    sc_id = plan_res["volumes"][0]["chapters"][0]["scene_id"]

    # 2. Trigger Grounded Scene Writing
    write_res = c.post(
        "/api/agent/auto-write-scene",
        json={
            "scene_id": sc_id,
            "guidance": "让林舟在暗道中发现第一枚染血玉简",
            "auto_extract": True,
        },
    ).json()

    assert write_res["scene_id"] == sc_id
    assert len(write_res["content"]) > 50
    assert "林舟" in write_res["content"]
    assert "thought_process" in write_res
    assert write_res["thought_process"]["quality_score"] > 80

    # 3. Verify workspace & revision persisted
    ws = c.get(f"/api/scenes/{sc_id}/workspace").json()
    assert len(ws["draft_content"]) > 50


def test_agent_auto_advance_sequential(client):
    c, _, _ = client
    # 1. Plan structure
    c.post(
        "/api/agent/auto-plan",
        json={
            "seed_prompt": "剑道独尊，少年闯荡江湖",
            "target_volumes": 1,
            "chapters_per_vol": 2,
        },
    )

    # 2. Advance first scene
    res1 = c.post("/api/agent/auto-advance").json()
    assert res1["scene_id"] > 0
    assert len(res1["content"]) > 0

    # 3. Advance second scene
    res2 = c.post("/api/agent/auto-advance").json()
    assert res2["scene_id"] > 0
    assert len(res2["content"]) > 0


def test_agent_director_chat_interaction(client):
    c, _, _ = client
    # 1. Outline instruction
    res_outline = c.post(
        "/api/agent/director-chat",
        json={"instruction": "帮我规划下一卷的主角成长大纲"},
    ).json()
    assert res_outline["action"] == "SUGGEST_OUTLINE"
    assert "大纲建议" in res_outline["reply"]

    # 2. Knowledge query instruction
    res_query = c.post(
        "/api/agent/director-chat",
        json={"instruction": "查一下主角林舟目前所在的地点和关系"},
    ).json()
    assert res_query["action"] == "QUERY_GRAPH"
    assert len(res_query["reply"]) > 0
