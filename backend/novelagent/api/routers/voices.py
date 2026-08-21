from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import AppState, require_session
from ...application.services import project_service, voice_service
from ..schemas.quality import (
    VoiceDriftCheckRequest,
    VoiceFingerprintCreate,
    VoiceFingerprintView,
    VoiceLexiconCreate,
    VoiceLexiconView,
)

router = APIRouter(tags=["Voice Fingerprints & Lexicons"])


def _to_fp_view(fp: Any) -> VoiceFingerprintView:
    return VoiceFingerprintView(
        id=fp.id,
        project_id=fp.project_id,
        character_id=fp.character_id,
        version=fp.version,
        avg_sentence_length=fp.avg_sentence_length,
        sentence_length_std=fp.sentence_length_std,
        colloquial_ratio=fp.colloquial_ratio,
        classical_ratio=fp.classical_ratio,
        honorific_level=fp.honorific_level,
        common_patterns=fp.common_patterns or [],
        preferred_particles=fp.preferred_particles or [],
        preferred_address_terms=fp.preferred_address_terms or [],
        preferred_perception_verbs=fp.preferred_perception_verbs or [],
        forbidden_expressions=fp.forbidden_expressions or [],
        source_revision_ids=fp.source_revision_ids or [],
        source_text_sample_count=fp.source_text_sample_count,
        created_at=fp.created_at.isoformat() if fp.created_at else "",
        updated_at=fp.updated_at.isoformat() if fp.updated_at else "",
    )


@router.get("/api/characters/{character_id}/voice-fingerprint", response_model=VoiceFingerprintView)
def get_character_voice_fingerprint(
    character_id: int,
    state: AppState = Depends(require_session),
) -> VoiceFingerprintView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        fp = voice_service.get_voice_fingerprint(db, project.id, character_id)
        if not fp:
            raise HTTPException(status_code=404, detail="未找到该人物的声音指纹")
        return _to_fp_view(fp)


@router.post("/api/characters/{character_id}/voice-fingerprint", response_model=VoiceFingerprintView)
def set_character_voice_fingerprint(
    character_id: int,
    payload: VoiceFingerprintCreate,
    state: AppState = Depends(require_session),
) -> VoiceFingerprintView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        fp = voice_service.create_or_update_voice_fingerprint(
            db,
            project_id=project.id,
            character_id=character_id,
            avg_sentence_length=payload.avg_sentence_length,
            sentence_length_std=payload.sentence_length_std,
            colloquial_ratio=payload.colloquial_ratio,
            classical_ratio=payload.classical_ratio,
            honorific_level=payload.honorific_level,
            preferred_particles=payload.preferred_particles,
            forbidden_expressions=payload.forbidden_expressions,
        )
        return _to_fp_view(fp)


@router.post("/api/characters/{character_id}/voice-fingerprint/extract", response_model=VoiceFingerprintView)
def extract_character_voice_fingerprint_endpoint(
    character_id: int,
    state: AppState = Depends(require_session),
) -> VoiceFingerprintView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            fp = voice_service.extract_character_voice_fingerprint(db, project.id, character_id)
            return _to_fp_view(fp)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/voice-drift-check")
def check_voice_drift_endpoint(
    payload: VoiceDriftCheckRequest,
    state: AppState = Depends(require_session),
) -> list[dict[str, Any]]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        return voice_service.check_voice_drift(db, project.id, payload.character_id, payload.text)


@router.get("/api/voice-lexicons", response_model=list[VoiceLexiconView])
def list_voice_lexicons_endpoint(
    character_id: int | None = None,
    state: AppState = Depends(require_session),
) -> list[VoiceLexiconView]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        lexicons = voice_service.list_voice_lexicons(db, project.id, character_id=character_id)
        return [
            VoiceLexiconView(
                id=l.id,
                project_id=l.project_id,
                character_id=l.character_id,
                lexicon_type=l.lexicon_type,
                entry_type=l.entry_type,
                pattern=l.pattern,
                pattern_type=l.pattern_type,
                version=l.version,
                created_at=l.created_at.isoformat() if l.created_at else "",
            )
            for l in lexicons
        ]


@router.post("/api/voice-lexicons", response_model=VoiceLexiconView)
def create_voice_lexicon_endpoint(
    payload: VoiceLexiconCreate,
    state: AppState = Depends(require_session),
) -> VoiceLexiconView:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        entry = voice_service.create_voice_lexicon_entry(
            db,
            project_id=project.id,
            character_id=payload.character_id,
            lexicon_type=payload.lexicon_type,
            entry_type=payload.entry_type,
            pattern=payload.pattern,
            pattern_type=payload.pattern_type,
        )
        return VoiceLexiconView(
            id=entry.id,
            project_id=entry.project_id,
            character_id=entry.character_id,
            lexicon_type=entry.lexicon_type,
            entry_type=entry.entry_type,
            pattern=entry.pattern,
            pattern_type=entry.pattern_type,
            version=entry.version,
            created_at=entry.created_at.isoformat() if entry.created_at else "",
        )


@router.delete("/api/voice-lexicons/{lexicon_id}")
def delete_voice_lexicon_endpoint(
    lexicon_id: int,
    state: AppState = Depends(require_session),
) -> dict[str, Any]:
    _, factory = state.require_project()
    with factory() as db:
        project = project_service.get_current_project(db)
        try:
            voice_service.delete_voice_lexicon_entry(db, lexicon_id, project.id)
            return {"status": "DELETED", "id": lexicon_id}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
