from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from novelagent.api import create_app
from novelagent.api.dependencies import AppState
from novelagent.application.services.vector_service import cosine_similarity
from novelagent.domain.transition_rules import estimate_tokens
from novelagent.infrastructure.db import Base


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    state = AppState(None)
    app.state.novelagent = state

    db_file = tmp_path / "test_phase8.db"
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


def test_fts_indexing_and_search_with_quotes_and_wildcards(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第一章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "客栈相遇"}).json()["id"]

    # Save scene text revision and accept to canon
    p = c.post(f"/api/scenes/{sc_id}/patches", json={"content": '林舟推开客栈的木门，手中紧握着"龙渊神剑"，命中率达100%_精准。', "source": "AUTHOR"}).json()
    c.post(f"/api/scenes/{sc_id}/revisions/{p['revision_id']}/accept")

    # Rebuild FTS and search
    rebuild = c.post("/api/indexes/fts/rebuild")
    assert rebuild.status_code == 200
    assert rebuild.json()["indexed_count"] >= 1

    # Exact search with double quotes in query input
    res_quotes = c.get("/api/search/fts", params={"query": '"龙渊神剑"'}).json()
    assert len(res_quotes) >= 1

    # Search with wildcards in query input
    res_wildcard = c.get("/api/search/fts", params={"query": "100%"}).json()
    assert len(res_wildcard) >= 1


def test_vector_similarity_search_and_cosine(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第二章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "雪夜决战"}).json()["id"]

    # Test standalone cosine similarity with unnormalized and zero vectors
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([2.0, 0.0], [4.0, 0.0]) == 1.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    p = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "漫天大雪纷飞，林舟在山巅拔剑迎战黑衣人。", "source": "AUTHOR"}).json()
    c.post(f"/api/scenes/{sc_id}/revisions/{p['revision_id']}/accept")

    rebuild = c.post("/api/indexes/vector/rebuild").json()
    assert rebuild["indexed_count"] >= 1

    res = c.get("/api/search/vector", params={"query_text": "在雪地中山巅战斗", "top_k": 5}).json()
    assert len(res) >= 1
    assert res[0]["similarity"] > 0.0
    assert res[0]["source_id"] == sc_id


def test_kg_projections_and_path_finding(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第3章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "宗门"}).json()["id"]

    c1 = c.post("/api/characters", json={"name": "林舟"}).json()["id"]
    c2 = c.post("/api/characters", json={"name": "苏晓晓"}).json()["id"]
    c3 = c.post("/api/characters", json={"name": "神秘阁主"}).json()["id"]

    c.post("/api/relationships", json={"subject_character_id": c1, "object_character_id": c2, "relationship_type": "FRIEND", "scene_id": sc_id, "confirmed": True})
    c.post("/api/relationships", json={"subject_character_id": c2, "object_character_id": c3, "relationship_type": "MASTER", "scene_id": sc_id, "confirmed": True})

    rebuild = c.post("/api/indexes/kg/rebuild").json()
    assert rebuild["nodes"] >= 3
    assert rebuild["edges"] >= 2

    nodes = c.get("/api/kg/nodes").json()
    n1 = [n["id"] for n in nodes if n["entity_id"] == c1][0]
    n3 = [n["id"] for n in nodes if n["entity_id"] == c3][0]

    path = c.post("/api/kg/path", json={"source_node_id": n1, "target_node_id": n3, "max_hops": 3}).json()
    assert len(path) == 2  # 2 hops: c1 -> c2 -> c3


def test_hrag_hierarchy_and_context_pack(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第三章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "进入秘境"}).json()["id"]
    p = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "古老的石门缓缓开启，尘封千年的光芒透射而出。", "source": "AUTHOR"}).json()
    c.post(f"/api/scenes/{sc_id}/revisions/{p['revision_id']}/accept")
    c.put(f"/api/scenes/{sc_id}/contracts", json={"entry_contract": {"location": "秘境古门", "narrative_time": "黄昏"}})

    # Token estimation check
    assert estimate_tokens("你好世界") == 2
    assert estimate_tokens("") == 0

    c.post("/api/summaries", json={"summary_type": "PROJECT", "source_id": 1, "source_version": 1, "content": "少年修士探寻上古秘境的故事。"})

    hrag = c.get("/api/search/hrag", params={"scene_id": sc_id, "max_tokens": 3000}).json()
    assert len(hrag) >= 1
    assert any(h["type"] == "PROJECT_SUMMARY" for h in hrag)

    pack = c.post(
        "/api/context-packs",
        json={"scene_id": sc_id, "instruction": "描写踏入石门后的宏大景象", "max_tokens": 5000},
    ).json()
    assert pack["scene_id"] == sc_id
    assert len(pack["fragments"]) >= 2

    val = c.post("/api/context-packs/validate", json={"pack_data": pack}).json()
    assert val["valid"] is True


def test_index_rebuild_from_canon_and_validation(client):
    c, _, _ = client
    ch_id = c.post("/api/projects/current/chapters", json={"title": "第四章"}).json()["id"]
    sc_id = c.post(f"/api/chapters/{ch_id}/scenes", json={"title": "尾声"}).json()["id"]
    p = c.post(f"/api/scenes/{sc_id}/patches", json={"content": "江湖路远，少年终将仗剑天涯。", "source": "AUTHOR"}).json()
    c.post(f"/api/scenes/{sc_id}/revisions/{p['revision_id']}/accept")

    rebuild = c.post("/api/indexes/rebuild-all").json()
    assert rebuild["status"] == "COMPLETED"
    assert rebuild["fts_documents"] >= 1
    assert rebuild["vector_documents"] >= 1

    status = c.get("/api/indexes/status").json()
    assert status["overall_status"] == "HEALTHY"
    assert status["fts"]["status"] == "HEALTHY"
    assert status["vector"]["status"] == "HEALTHY"
