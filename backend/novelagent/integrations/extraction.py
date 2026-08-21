from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from ..domain.rules import claim_is_low_risk
from .prompt_templates import render_prompt

MODALITY_PATTERNS: dict[str, list[str]] = {
    "DREAMED": [r"梦见", r"做了一个梦", r"梦中", r"恍惚间", r"幻境", r"幻象", r"梦里的", r"似梦非梦"],
    "REPORTED": [r"听说", r"相传", r"据说", r"有人.*说", r"传闻", r"谣言", r"小道消息", r"风闻", r"转述"],
    "REMEMBERED": [r"记得", r"回想起", r"回忆", r"当年", r"那时候", r"往事", r"蓦然想起", r"记忆中"],
    "HYPOTHETICAL": [r"也许", r"可能", r"假如", r"如果.*就", r"若是.*便", r"万一", r"倘若", r"假使", r"要是.*的话"],
    "COUNTERFACTUAL": [r"如果当初", r"要是当时", r"本该.*却", r"本可以.*但没有"],
    "METAPHORICAL": [r"像.*一样", r"仿佛", r"如同", r"好似", r"犹如", r"若有若无"],
    "BELIEVED": [r"相信", r"认为", r"坚信", r"觉得.*是", r"以为", r"自以为"],
}

PREDICATE_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?:按住|握着|拿着|拔出|取出|持有|佩戴)\s*([^\s，。；！]+)", "holds", "item"),
    (r"(?:来到|身处|位于|进入|留在|到达)\s*([^\s，。；！]+)", "located_at", "location"),
    (r"(?:结盟|背叛|敌对|仇视|爱慕)\s*([^\s，。；！]+)", "relationship_with", "character"),
    (r"(?:阵亡|重伤|昏迷|自尽|陨落)\b", "event_participated", "event"),
    (r"(?:暗自发誓|埋下隐患|殊不知|日后)\b", "foreshadowing", "concept"),
]


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
    cognitive_subject: str | None = None
    paragraph_index: int | None = None
    content_hash: str | None = None
    hypothesis_tags: list[str] = field(default_factory=list)


def infer_modality(text: str) -> tuple[str, float]:
    for modality, patterns in MODALITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return modality, 0.85
    return "ACTUAL", 0.95


def infer_modality_t2(
    paragraph: str,
    context: str = "",
    model_gateway: Any | None = None,
) -> tuple[str, float]:
    """T2 Model-driven modality refinement (PRD 4.3.2) with rule baseline fallback."""
    modality, mod_conf = infer_modality(paragraph)
    if modality != "ACTUAL":
        return modality, mod_conf

    if model_gateway and getattr(model_gateway, "config", None) and model_gateway.config.endpoint:
        try:
            prompt = render_prompt("modality_inference", {"sentence": paragraph, "context": context})
            if hasattr(model_gateway, "invoke_sync"):
                response = model_gateway.invoke_sync(tier="T2", prompt=prompt)
                if response:
                    import json
                    parsed = json.loads(response)
                    if "modality" in parsed and (parsed["modality"] in MODALITY_PATTERNS or parsed["modality"] == "ACTUAL"):
                        return parsed["modality"], float(parsed.get("confidence", 0.85))
        except Exception:
            pass
    return modality, mod_conf


def _paragraphs(text: str):
    offset = 0
    for idx, paragraph in enumerate(text.splitlines(keepends=True)):
        clean = paragraph.strip()
        start = offset + (len(paragraph) - len(paragraph.lstrip()))
        end = start + len(clean)
        if clean:
            yield idx, clean, start, end
        offset += len(paragraph)


def extract_candidates(
    text: str,
    known_aliases: dict[str, str] | set[str] | None = None,
) -> list[Candidate]:
    """Rule-based baseline extractor with entity disambiguation and modality inference."""
    if isinstance(known_aliases, set):
        alias_map = {k: k for k in known_aliases}
    elif isinstance(known_aliases, dict):
        alias_map = known_aliases
    else:
        alias_map = {}

    candidates: list[Candidate] = []

    for p_idx, paragraph, start, end in _paragraphs(text):
        p_hash = hashlib.sha256(paragraph.encode("utf-8")).hexdigest()
        modality, mod_conf = infer_modality(paragraph)

        # Detect cognitive subject if reported/believed
        cog_subj = None
        cog_match = re.search(r"([\u4e00-\u9fff]{2,4})(?:听说|相信|以为|记得|回忆)", paragraph)
        if cog_match:
            cog_subj = cog_match.group(1)

        # 1. Extract character appearance
        alias_hits = [alias for alias in sorted(alias_map.keys(), key=len, reverse=True) if alias in paragraph]
        found_names = alias_hits if alias_hits else list(dict.fromkeys(re.findall(r"[\u4e00-\u9fff]{2,3}", paragraph)))

        for raw_name in found_names[:5]:  # limit to top 5 per paragraph
            canonical = alias_map.get(raw_name, raw_name)
            is_resolved = raw_name in alias_map
            ent_conf = 0.96 if is_resolved else 0.65
            low_risk = claim_is_low_risk(
                modality=modality,
                subject_resolved=is_resolved,
                predicate="appears",
                explicit=True,
                confidence=mod_conf,
                entity_confidence=ent_conf,
            )
            status = "AUTO_CONFIRMED" if low_risk else "REVIEW_REQUIRED"

            candidates.append(Candidate(
                subject=canonical,
                predicate="appears",
                object_value="scene",
                modality=modality,
                cognitive_subject=cog_subj,
                source_start=start,
                source_end=end,
                paragraph_index=p_idx,
                source_text=paragraph,
                content_hash=p_hash,
                confidence=mod_conf,
                entity_confidence=ent_conf,
                hypothesis_tags=["alias_mapped"] if is_resolved else ["unlinked_entity"],
                status=status,
            ))

        # 2. Extract predicates (holds, located_at, etc.)
        for pattern, pred, obj_type in PREDICATE_PATTERNS:
            match = re.search(pattern, paragraph)
            if match:
                obj_val = match.group(1) if match.groups() else obj_type
                main_subj = alias_map.get(found_names[0], found_names[0]) if found_names else "主人公"
                is_resolved = (main_subj in alias_map.values()) or (found_names and found_names[0] in alias_map)
                ent_conf = 0.90 if is_resolved else 0.60

                low_risk = claim_is_low_risk(
                    modality=modality,
                    subject_resolved=is_resolved,
                    predicate=pred,
                    explicit=True,
                    confidence=mod_conf * 0.9,
                    entity_confidence=ent_conf,
                )
                status = "AUTO_CONFIRMED" if low_risk else "REVIEW_REQUIRED"

                candidates.append(Candidate(
                    subject=main_subj,
                    predicate=pred,
                    object_value=obj_val,
                    modality=modality,
                    cognitive_subject=cog_subj,
                    source_start=start,
                    source_end=end,
                    paragraph_index=p_idx,
                    source_text=paragraph,
                    content_hash=p_hash,
                    confidence=round(mod_conf * 0.9, 2),
                    entity_confidence=ent_conf,
                    hypothesis_tags=[f"pred_{pred}"],
                    status=status,
                ))

    return candidates
