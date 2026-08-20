from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.rules import claim_is_low_risk

MODALITY_HINTS = {
    "梦": "DREAMED",
    "也许": "HYPOTHETICAL",
    "传言": "REPORTED",
    "听说": "REPORTED",
    "回忆": "REMEMBERED",
    "仿佛": "METAPHORICAL",
}


@dataclass(frozen=True)
class Candidate:
    subject: str
    predicate: str
    object_value: str
    modality: str
    source_start: int
    source_end: int
    source_text: str
    confidence: float
    entity_confidence: float
    status: str


def _paragraphs(text: str):
    offset = 0
    for paragraph in text.splitlines(keepends=True):
        clean = paragraph.strip()
        start = offset + (len(paragraph) - len(paragraph.lstrip()))
        end = start + len(clean)
        if clean:
            yield clean, start, end
        offset += len(paragraph)


def extract_candidates(text: str, known_aliases: set[str] | None = None) -> list[Candidate]:
    """Deterministic baseline extractor; model adapters can replace this function."""
    aliases = known_aliases or set()
    candidates: list[Candidate] = []
    for paragraph, start, end in _paragraphs(text):
        modality = "ACTUAL"
        for hint, hinted in MODALITY_HINTS.items():
            if hint in paragraph:
                modality = hinted
                break
        alias_hits = [alias for alias in sorted(aliases, key=len, reverse=True) if alias and alias in paragraph]
        names = alias_hits if alias_hits else [name for name in re.findall(r"[\u4e00-\u9fff]{2,3}", paragraph)]
        for name in dict.fromkeys(names):
            resolved = name in aliases
            predicate = "appears"
            explicit = True
            status = "AUTO_CONFIRMED" if claim_is_low_risk(
                modality=modality,
                subject_resolved=resolved,
                predicate=predicate,
                explicit=explicit,
            ) else "REVIEW_REQUIRED"
            candidates.append(Candidate(
                subject=name,
                predicate=predicate,
                object_value="scene",
                modality=modality,
                source_start=start,
                source_end=end,
                source_text=paragraph,
                confidence=0.82 if resolved else 0.55,
                entity_confidence=0.96 if resolved else 0.45,
                status=status,
            ))
    return candidates
