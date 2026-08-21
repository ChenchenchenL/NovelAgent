from __future__ import annotations

import hashlib
import math
import struct
from typing import Any, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ...domain.models import CanonClaim, Chapter, Scene, SceneRevision
from ...domain.search_models import VectorDocument, VectorEmbedding

DEFAULT_VECTOR_DIM = 64
DEFAULT_MODEL_NAME = "local-hash-ngram-64"


def generate_local_embedding(text_content: str, dim: int = DEFAULT_VECTOR_DIM) -> list[float]:
    """Generate a normalized dim-dimensional embedding vector deterministically from text."""
    clean = text_content.strip().lower()
    if not clean:
        return [0.0] * dim

    vec = [0.0] * dim
    # Hash 2-grams and 3-grams into embedding dimensions
    for n in (1, 2, 3):
        for i in range(len(clean) - n + 1):
            gram = clean[i : i + n]
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        return [x / norm for x in vec]
    return [0.0] * dim


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute true cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def pack_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def unpack_vector(data: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", data))


def index_vector_document(
    session: Session,
    project_id: int,
    doc_type: str,
    source_id: int,
    source_version: int,
    content: str,
    narrative_time: str | None = None,
    modality: str = "ACTUAL",
    confirmed: bool = False,
    model_name: str = DEFAULT_MODEL_NAME,
) -> VectorDocument:
    # Delete old vector documents for same source
    old_docs = session.scalars(
        select(VectorDocument).where(
            VectorDocument.project_id == project_id,
            VectorDocument.doc_type == doc_type,
            VectorDocument.source_id == source_id,
        )
    ).all()
    for od in old_docs:
        session.execute(delete(VectorEmbedding).where(VectorEmbedding.document_id == od.id))
        session.delete(od)

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    doc = VectorDocument(
        project_id=project_id,
        doc_type=doc_type,
        source_id=source_id,
        source_version=source_version,
        content=content.strip(),
        content_hash=content_hash,
        narrative_time=narrative_time,
        modality=modality,
        confirmed=confirmed,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    # Compute and store embedding
    vec = generate_local_embedding(content, dim=DEFAULT_VECTOR_DIM)
    emb = VectorEmbedding(
        document_id=doc.id,
        model_name=model_name,
        vector_data=pack_vector(vec),
        vector_dim=DEFAULT_VECTOR_DIM,
    )
    session.add(emb)
    session.commit()
    return doc


def search_vectors(
    session: Session,
    project_id: int,
    query_text: str,
    doc_type: str | None = None,
    top_k: int = 10,
    min_similarity: float = 0.0,
) -> list[dict[str, Any]]:
    query_vec = generate_local_embedding(query_text, dim=DEFAULT_VECTOR_DIM)

    stmt = select(VectorDocument, VectorEmbedding).join(
        VectorEmbedding, VectorEmbedding.document_id == VectorDocument.id
    ).where(VectorDocument.project_id == project_id)

    if doc_type:
        stmt = stmt.where(VectorDocument.doc_type == doc_type)

    pairs = session.execute(stmt).all()
    scored = []
    for doc, emb in pairs:
        vec = unpack_vector(emb.vector_data, emb.vector_dim)
        sim = cosine_similarity(query_vec, vec)
        if sim >= min_similarity:
            scored.append({
                "id": doc.id,
                "project_id": doc.project_id,
                "doc_type": doc.doc_type,
                "source_id": doc.source_id,
                "source_version": doc.source_version,
                "content": doc.content,
                "narrative_time": doc.narrative_time,
                "modality": doc.modality,
                "confirmed": doc.confirmed,
                "similarity": round(sim, 4),
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def count_vector_documents(session: Session, project_id: int) -> int:
    return session.scalar(select(func.count()).select_from(VectorDocument).where(VectorDocument.project_id == project_id)) or 0


def rebuild_vector_index(session: Session, project_id: int) -> int:
    docs = list(session.scalars(select(VectorDocument).where(VectorDocument.project_id == project_id)).all())
    for d in docs:
        session.execute(delete(VectorEmbedding).where(VectorEmbedding.document_id == d.id))
        session.delete(d)
    session.commit()

    count = 0
    scenes = session.scalars(
        select(Scene).join(Chapter).where(Chapter.project_id == project_id)
    ).all()
    for sc in scenes:
        if sc.current_revision_id:
            rev = session.get(SceneRevision, sc.current_revision_id)
            if rev and rev.content:
                index_vector_document(
                    session,
                    project_id=project_id,
                    doc_type="SCENE",
                    source_id=sc.id,
                    source_version=rev.id,
                    content=rev.content,
                    narrative_time=sc.entry_contract.get("narrative_time") if sc.entry_contract else None,
                    modality="ACTUAL",
                    confirmed=True,
                )
                count += 1
    return count
