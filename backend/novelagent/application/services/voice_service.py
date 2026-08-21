from __future__ import annotations

from typing import Any, Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ...domain.continuity_models import Character
from ...domain.models import Chapter, Scene, SceneRevision
from ...domain.quality_models import VoiceFingerprint, VoiceLexicon
from ...domain.quality_rules import detect_voice_drift, extract_voice_statistics


def get_voice_fingerprint(session: Session, project_id: int, character_id: int) -> VoiceFingerprint | None:
    return session.scalar(
        select(VoiceFingerprint).where(
            VoiceFingerprint.project_id == project_id,
            VoiceFingerprint.character_id == character_id,
        )
    )


def extract_character_voice_fingerprint(
    session: Session,
    project_id: int,
    character_id: int,
) -> VoiceFingerprint:
    char = session.get(Character, character_id)
    if not char:
        raise KeyError(f"人物不存在: ID {character_id}")

    # Gather text samples from canonical scenes where character speaks or is present
    char_names = [char.name] + list(char.aliases or [])
    scenes = session.scalars(
        select(Scene).join(Chapter).where(Chapter.project_id == project_id)
    ).all()

    samples: list[str] = []
    rev_ids: list[int] = []
    for sc in scenes:
        if sc.current_revision_id:
            rev = session.get(SceneRevision, sc.current_revision_id)
            if rev and rev.content:
                # Find matching sentences or dialogue lines
                matched_sentences = [
                    s for s in rev.content.split("\n")
                    if s.strip() and any(n in s for n in char_names)
                ]
                if matched_sentences:
                    samples.extend(matched_sentences)
                    rev_ids.append(rev.id)

    stats = extract_voice_statistics(samples)

    fp = get_voice_fingerprint(session, project_id, character_id)
    if not fp:
        fp = VoiceFingerprint(
            project_id=project_id,
            character_id=character_id,
            version=1,
            avg_sentence_length=stats["avg_sentence_length"],
            sentence_length_std=stats["sentence_length_std"],
            colloquial_ratio=stats["colloquial_ratio"],
            classical_ratio=stats["classical_ratio"],
            honorific_level=stats["honorific_level"],
            preferred_particles=stats["preferred_particles"],
            source_revision_ids=rev_ids,
            source_text_sample_count=len(samples),
        )
        session.add(fp)
    else:
        fp.version += 1
        fp.avg_sentence_length = stats["avg_sentence_length"]
        fp.sentence_length_std = stats["sentence_length_std"]
        fp.colloquial_ratio = stats["colloquial_ratio"]
        fp.classical_ratio = stats["classical_ratio"]
        fp.honorific_level = stats["honorific_level"]
        fp.preferred_particles = stats["preferred_particles"]
        fp.source_revision_ids = rev_ids
        fp.source_text_sample_count = len(samples)

    session.commit()
    session.refresh(fp)
    return fp


def create_or_update_voice_fingerprint(
    session: Session,
    project_id: int,
    character_id: int,
    avg_sentence_length: float,
    sentence_length_std: float,
    colloquial_ratio: float = 0.0,
    classical_ratio: float = 0.0,
    honorific_level: str = "MEDIUM",
    preferred_particles: list[str] | None = None,
    forbidden_expressions: list[str] | None = None,
) -> VoiceFingerprint:
    fp = get_voice_fingerprint(session, project_id, character_id)
    if not fp:
        fp = VoiceFingerprint(
            project_id=project_id,
            character_id=character_id,
            version=1,
            avg_sentence_length=avg_sentence_length,
            sentence_length_std=sentence_length_std,
            colloquial_ratio=colloquial_ratio,
            classical_ratio=classical_ratio,
            honorific_level=honorific_level,
            preferred_particles=preferred_particles or [],
            forbidden_expressions=forbidden_expressions or [],
        )
        session.add(fp)
    else:
        fp.version += 1
        fp.avg_sentence_length = avg_sentence_length
        fp.sentence_length_std = sentence_length_std
        fp.colloquial_ratio = colloquial_ratio
        fp.classical_ratio = classical_ratio
        fp.honorific_level = honorific_level
        if preferred_particles is not None:
            fp.preferred_particles = preferred_particles
        if forbidden_expressions is not None:
            fp.forbidden_expressions = forbidden_expressions

    session.commit()
    session.refresh(fp)
    return fp


def create_voice_lexicon_entry(
    session: Session,
    project_id: int,
    character_id: int,
    lexicon_type: str,
    entry_type: str,
    pattern: str,
    pattern_type: str = "EXACT",
) -> VoiceLexicon:
    entry = VoiceLexicon(
        project_id=project_id,
        character_id=character_id,
        lexicon_type=lexicon_type.upper(),
        entry_type=entry_type,
        pattern=pattern.strip(),
        pattern_type=pattern_type.upper(),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_voice_lexicons(
    session: Session,
    project_id: int,
    character_id: int | None = None,
) -> list[VoiceLexicon]:
    stmt = select(VoiceLexicon).where(VoiceLexicon.project_id == project_id)
    if character_id is not None:
        stmt = stmt.where(VoiceLexicon.character_id == character_id)
    stmt = stmt.order_by(VoiceLexicon.id.asc())
    return list(session.scalars(stmt).all())


def delete_voice_lexicon_entry(session: Session, lexicon_id: int, project_id: int) -> None:
    entry = session.scalar(
        select(VoiceLexicon).where(VoiceLexicon.id == lexicon_id, VoiceLexicon.project_id == project_id)
    )
    if not entry:
        raise KeyError(f"词表条目不存在: ID {lexicon_id}")
    session.delete(entry)
    session.commit()


def check_voice_drift(
    session: Session,
    project_id: int,
    character_id: int,
    text: str,
) -> list[dict[str, Any]]:
    fp = get_voice_fingerprint(session, project_id, character_id)
    fp_dict = {
        "avg_sentence_length": fp.avg_sentence_length if fp else 15.0,
        "sentence_length_std": fp.sentence_length_std if fp else 5.0,
        "colloquial_ratio": fp.colloquial_ratio if fp else 0.0,
        "classical_ratio": fp.classical_ratio if fp else 0.0,
    } if fp else None

    lex_list = list_voice_lexicons(session, project_id, character_id=character_id)
    lex_dicts = [
        {
            "id": l.id,
            "lexicon_type": l.lexicon_type,
            "entry_type": l.entry_type,
            "pattern": l.pattern,
            "pattern_type": l.pattern_type,
        }
        for l in lex_list
    ]
    return detect_voice_drift(text, fp_dict, lex_dicts)
