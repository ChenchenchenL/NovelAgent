from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.domain.rules import (
    calculate_time_delta_minutes,
    evaluate_movement_feasibility,
    evaluate_shadow_coexistence,
    validate_item_transition,
    ItemTransition,
)
from novelagent.infrastructure.db import Base


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase6.db"
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


def test_character_and_character_states_crud_and_cascade_delete(client):
    c, _, _ = client
    resp = c.post("/api/characters", json={"name": "林舟", "aliases": ["无名剑客"]})
    assert resp.status_code == 200
    char_id = resp.json()["id"]

    ch_id = c.post("/api/projects/current/chapters", json={"title": "卷一"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "破庙"}).json()["id"]

    st_resp = c.post(
        f"/api/characters/{char_id}/states",
        json={"scene_id": sc_id, "location": "城外破庙", "physical_state": "健康"},
    )
    assert st_resp.status_code == 200

    # Test Cascade Delete of Character
    del_resp = c.delete(f"/api/characters/{char_id}")
    assert del_resp.status_code == 200
    assert c.get(f"/api/characters/{char_id}").status_code == 404
    assert len(c.get(f"/api/characters/{char_id}/states").json()) == 0 or c.get(f"/api/characters/{char_id}/states").status_code == 404


def test_relationship_events_and_state_projections(client):
    c, _, _ = client
    ch1 = c.post("/api/characters", json={"name": "林舟"}).json()["id"]
    ch2 = c.post("/api/characters", json={"name": "苏清月"}).json()["id"]

    ch_id = c.post("/api/projects/current/chapters", json={"title": "第1章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "并肩"}).json()["id"]

    evt = c.post(
        "/api/relationships",
        json={"subject_character_id": ch1, "object_character_id": ch2, "relationship_type": "TRUSTS", "scene_id": sc_id, "confirmed": True},
    )
    assert evt.status_code == 200

    cur_states = c.get("/api/relationships/current").json()
    assert len(cur_states) == 1
    assert cur_states[0]["relationship_type"] == "TRUSTS"


def test_narrative_secrets_and_knowledge_violation_check(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "秘密章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "密室"}).json()["id"]

    char_a = c.post("/api/characters", json={"name": "林舟"}).json()["id"]
    char_b = c.post("/api/characters", json={"name": "李四"}).json()["id"]

    sec = c.post(
        "/api/secrets",
        json={"secret_name": "宝图", "secret_content": "在黑水潭", "created_scene_id": sc_id, "known_by": [{"character_id": char_a, "known_since_scene_id": sc_id}]},
    ).json()
    sec_id = sec["id"]

    chk_resp = c.post(f"/api/scenes/{sc_id}/check-knowledge", json={"character_id": char_b, "secret_ids": [sec_id]}).json()
    assert chk_resp["has_violation"] is True

    c.post(f"/api/secrets/{sec_id}/reveal", json={"character_id": char_b, "scene_id": sc_id})
    chk_after = c.post(f"/api/scenes/{sc_id}/check-knowledge", json={"character_id": char_b, "secret_ids": [sec_id]}).json()
    assert chk_after["has_violation"] is False


def test_item_conservation_state_machine(client):
    c, _, _ = client
    item = c.post("/api/items", json={"name": "龙渊剑", "unique_item": True, "current_holder": "林舟", "current_state": "HELD"}).json()
    item_id = item["id"]

    tr = c.post(f"/api/items/{item_id}/events", json={"event_type": "TRANSFERRED", "from_holder": "林舟", "to_holder": "苏清月"})
    assert tr.status_code == 200

    err_tr = c.post(f"/api/items/{item_id}/events", json={"event_type": "TRANSFERRED", "from_holder": "林舟", "to_holder": "李四"})
    assert err_tr.status_code == 400

    dest = c.post(f"/api/items/{item_id}/events", json={"event_type": "DESTROYED"})
    assert dest.status_code == 200
    assert c.post(f"/api/items/{item_id}/events", json={"event_type": "TRANSFERRED", "from_holder": "苏清月", "to_holder": "李四"}).status_code == 400


def test_shadow_entity_reveal_and_history_serialization(client):
    c, _, _ = client
    canonical_char = c.post("/api/characters", json={"name": "林舟"}).json()["id"]
    shadow = c.post("/api/shadow-entities", json={"display_name": "黑衣人"}).json()
    shadow_id = shadow["id"]

    c.post(f"/api/shadow-entities/{shadow_id}/hypotheses", json={"canonical_character_id": canonical_char, "confidence": 0.9, "evidence": [{"scene_id": 1, "location": "客栈"}]})

    ch_id = c.post("/api/projects/current/chapters", json={"title": "掉马章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "揭秘"}).json()["id"]

    rev = c.post(f"/api/shadow-entities/{shadow_id}/reveal", json={"canonical_character_id": canonical_char, "reveal_scene_id": sc_id, "evidence": "揭下面具"})
    assert rev.status_code == 200

    # Test serialization of history endpoint
    hist = c.get(f"/api/shadow-entities/{shadow_id}/history")
    assert hist.status_code == 200
    data = hist.json()
    assert data["shadow_entity"]["revealed"] is True
    assert len(data["hypotheses"]) == 1
    assert len(data["reveal_events"]) == 1


def test_locations_travel_profiles_polymorphic_and_negative_time(client):
    c, _, _ = client
    loc1 = c.post("/api/locations", json={"name": "临安"}).json()["id"]
    loc2 = c.post("/api/locations", json={"name": "姑苏"}).json()["id"]

    c.post("/api/travel-profiles", json={"from_location_id": loc1, "to_location_id": loc2, "travel_mode": "HORSE", "min_duration_minutes": 120})

    ch_id = c.post("/api/projects/current/chapters", json={"title": "赶路"}).json()["id"]
    sc1 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "出城"}).json()["id"]
    sc2 = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "到城"}).json()["id"]

    char_id = c.post("/api/characters", json={"name": "林舟"}).json()["id"]

    # Movement conflict test
    mov = c.post("/api/movements", json={"subject_type": "CHARACTER", "subject_id": char_id, "from_location_id": loc1, "to_location_id": loc2, "travel_mode": "HORSE", "departure_scene_id": sc1, "arrival_scene_id": sc2, "actual_duration_minutes": 50}).json()
    assert mov["feasibility"]["status"] == "CONFLICT"

    # Polymorphic subject validation failure test
    invalid_sub = c.post("/api/movements", json={"subject_type": "CHARACTER", "subject_id": 9999, "from_location_id": loc1, "to_location_id": loc2, "travel_mode": "HORSE", "departure_scene_id": sc1, "arrival_scene_id": sc2, "actual_duration_minutes": 150})
    assert invalid_sub.status_code == 404

    # Negative integer time delta test
    assert calculate_time_delta_minutes("-10", "50") == 60
    assert calculate_time_delta_minutes("100", "40") == 60

    # Delete location cascade test
    del_loc = c.delete(f"/api/locations/{loc1}")
    assert del_loc.status_code == 200
    assert c.get(f"/api/locations/{loc1}").status_code == 404
