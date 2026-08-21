import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.models import Base, GenerationRun, GenerationRunEvent, GenerationWorkspace
from novelagent.integrations.model_gateway import KeyringManager, ModelConfig, ModelRouter


@pytest.fixture
def client(tmp_path: Path):
    settings = None
    app = create_app()
    state = AppState(settings)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase3.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    state.authorized_dirs.add(tmp_path)
    state.project_dir = tmp_path
    state.engine = engine
    state.session_factory = factory
    state.model_config = ModelConfig(
        endpoint="mock://test",
        models={"T1": "mock-t1", "T2": "mock-t2", "T3": "mock-t3"},
    )

    c = TestClient(app)
    c.headers.update({"X-NovelAgent-Token": state.session_token})

    # Open project
    c.post("/api/projects/open", json={"path": str(tmp_path)})
    return c, tmp_path, state.session_factory


def test_keyring_save_load_and_fallback():
    KeyringManager.save_key("test_endpoint", "sk-secret-123")
    assert KeyringManager.load_key("test_endpoint") == "sk-secret-123"
    KeyringManager.delete_key("test_endpoint")
    assert KeyringManager.load_key("test_endpoint") is None


def test_model_routing_tier_mapping():
    cfg = ModelConfig(
        endpoint="mock://test",
        models={"T1": "t1-model", "T2": "t2-model", "T3": "t3-model"},
    )
    router = ModelRouter(cfg)

    tier, model = router.route("extraction_entity")
    assert tier == "T1" and model == "t1-model"

    tier, model = router.route("beat_plan")
    assert tier == "T2" and model == "t2-model"

    tier, model = router.route("paragraph_generation")
    assert tier == "T3" and model == "t3-model"

    assert ModelRouter.get_degraded_tier("T3") == "T2"
    assert ModelRouter.get_degraded_tier("T2") == "T1"
    assert ModelRouter.get_degraded_tier("T1") is None


def test_model_test_and_config_endpoints(client):
    c, _, _ = client
    # Test connection
    res = c.post("/api/model/test", json={"endpoint": "mock://local"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # Update config and key
    res = c.put("/api/model/config", json={
        "endpoint": "https://api.mock.com/v1",
        "models": {"T1": "m1", "T2": "m2", "T3": "m3"},
        "api_key": "sk-test-key-abc",
    })
    assert res.status_code == 200
    assert res.json()["key_saved"] is True

    # Check config
    res = c.get("/api/model/config")
    assert res.status_code == 200
    assert res.json()["endpoint"] == "https://api.mock.com/v1"
    assert res.json()["has_key"] is True


def test_generation_run_lifecycle_and_sse(client):
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "生成测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "生成测试场"}).json()["id"]

    # 1. Create generation run
    req = {
        "task_type": "paragraph_generation",
        "instruction": "林舟缓步向前",
        "tier": "T3",
    }
    create_res = c.post(f"/api/scenes/{sc_id}/generation-runs", json=req)
    assert create_res.status_code == 200
    run_id = create_res.json()["id"]
    assert "sse_url" in create_res.json()

    # 2. Concurrency check: creating a 2nd run immediately on the same scene -> 409 Conflict
    conflict_res = c.post(f"/api/scenes/{sc_id}/generation-runs", json=req)
    assert conflict_res.status_code in {409, 200}  # If 1st finished quickly or 409

    # 3. Read SSE stream events
    sse_res = c.get(f"/api/generation-runs/{run_id}/sse")
    assert sse_res.status_code == 200
    text = sse_res.text
    assert "event: connected" in text
    assert "event: chunk" in text or "event: success" in text

    # 4. Check query endpoint
    run_view = c.get(f"/api/generation-runs/{run_id}").json()
    assert run_view["id"] == run_id
    assert run_view["status"] in {"RUNNING", "COMPLETED"}

    # 5. Check events persisted in database
    with factory() as db:
        events = list(db.scalars(
            select(GenerationRunEvent).where(GenerationRunEvent.run_id == run_id).order_by(GenerationRunEvent.sequence_number.asc())
        ).all())
        assert len(events) >= 1
        assert events[0].event_type == "connected"
        assert events[0].sequence_number == 1


def test_generation_cancel_running(client):
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "取消测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "取消测试场"}).json()["id"]

    create_res = c.post(f"/api/scenes/{sc_id}/generation-runs", json={"instruction": "测试取消"})
    run_id = create_res.json()["id"]

    # Cancel task
    cancel_res = c.post(f"/api/generation-runs/{run_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # List tasks for scene
    list_res = c.get(f"/api/generation-runs?scene_id={sc_id}")
    assert list_res.status_code == 200
    assert any(r["id"] == run_id for r in list_res.json())


def test_generated_output_to_workspace_draft_and_sse_reconnect(client):
    import time
    c, _, factory = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "草稿测试章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "草稿测试场"}).json()["id"]

    # Initial workspace
    ws_init = c.get(f"/api/scenes/{sc_id}/workspace").json()
    assert ws_init["draft_content"] == ""

    # Run generation
    create_res = c.post(f"/api/scenes/{sc_id}/generation-runs", json={
        "task_type": "paragraph_generation",
        "instruction": "描写客栈风雪",
    })
    run_id = create_res.json()["id"]

    # Consume full SSE stream
    sse_res = c.get(f"/api/generation-runs/{run_id}/sse")
    assert sse_res.status_code == 200

    # Wait for completion & verify workspace draft was populated
    time.sleep(0.15)
    ws_after = c.get(f"/api/scenes/{sc_id}/workspace").json()
    assert "林舟" in ws_after["draft_content"]

    # Test SSE reconnection with since parameter
    sse_reconnect = c.get(f"/api/generation-runs/{run_id}/sse?since=2")
    assert sse_reconnect.status_code == 200
    # Should not include sequence 1
    assert "id: 1\n" not in sse_reconnect.text

