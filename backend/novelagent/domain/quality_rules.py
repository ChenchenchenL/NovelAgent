from __future__ import annotations

import math
import re
from typing import Any, Optional

COLLOQUIAL_MARKERS = {"啊", "呀", "吧", "呢", "啦", "嘛", "哇", "欸", "哈", "嘿", "哪", "呗", "行了", "得咧", "我说"}
CLASSICAL_MARKERS = {"之", "乎", "者", "也", "矣", "焉", "哉", "乃", "其", "遂", "且", "夫", "若", "盖", "何以", "莫非"}


def split_sentences(text: str) -> list[str]:
    """Split text into sentence strings using standard punctuation delimiters."""
    if not text:
        return []
    parts = re.split(r"([。！？\n!?]+)", text)
    sentences: list[str] = []
    for i in range(0, len(parts) - 1, 2):
        s = (parts[i] + parts[i + 1]).strip()
        if s:
            sentences.append(s)
    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences or [text.strip()]


def detect_semantic_duplicates(paragraphs: list[str], threshold: float = 0.6) -> list[dict[str, Any]]:
    """Detect repetitive or looping sentences/paragraphs with high character similarity."""
    issues: list[dict[str, Any]] = []
    clean_items = [(idx + 1, p.strip()) for idx, p in enumerate(paragraphs) if p.strip()]

    for i in range(len(clean_items)):
        orig_i, p1 = clean_items[i]
        for j in range(i + 1, min(i + 4, len(clean_items))):
            orig_j, p2 = clean_items[j]
            if len(p1) < 8 or len(p2) < 8:
                continue
            set1, set2 = set(p1), set(p2)
            jaccard = len(set1 & set2) / max(1, len(set1 | set2))
            overlap = len(set1 & set2) / max(1, min(len(set1), len(set2)))
            if jaccard >= threshold or overlap >= (threshold + 0.05) or p1 == p2:
                issues.append({
                    "issue_type": "SEMANTIC_DUPLICATE",
                    "severity": "WARNING",
                    "source_text": p2,
                    "description": f"第 {orig_j} 段与第 {orig_i} 段语义高度重复或结构循环",
                    "evidence": [p1, p2],
                    "suggestion": "合并或精简重复段落，推动具体事件进展",
                    "root_cause_id": f"dup_{orig_i}_{orig_j}",
                })
    return issues


def detect_cliche_patterns(text: str, blacklists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scan text for cliche blacklist hits (exact, regex, or fuzzy substring)."""
    issues: list[dict[str, Any]] = []
    if not text:
        return issues

    for item in blacklists:
        if not item.get("enabled", True):
            continue
        pat = item.get("pattern", "")
        if not pat:
            continue
        p_type = item.get("pattern_type", "EXACT").upper()
        severity = item.get("severity", "WARNING")
        category = item.get("category", "GENERAL")
        suggestion = item.get("suggestion") or "替换为具体动作或更有新意的描写"

        hit = False
        if p_type == "EXACT":
            if pat in text:
                hit = True
        elif p_type == "REGEX":
            try:
                if re.search(pat, text):
                    hit = True
            except re.error:
                if pat in text:
                    hit = True
        elif p_type == "FUZZY":
            # Fuzzy check: characters in pat appear in sequence with small gaps
            fuzzy_re = ".*?".join(map(re.escape, list(pat)))
            if re.search(fuzzy_re, text):
                hit = True

        if hit:
            issues.append({
                "issue_type": "CLICHE",
                "severity": severity,
                "source_text": pat,
                "description": f"命中【{category}】类套话黑名单: \"{pat}\"",
                "evidence": [f"规则模式: {pat} ({p_type})"],
                "suggestion": suggestion,
                "root_cause_id": f"cliche_{pat}",
            })
    return issues


def extract_voice_statistics(samples: list[str]) -> dict[str, Any]:
    """Compute stylistic voice statistics from text samples."""
    all_sentences: list[str] = []
    for s in samples:
        all_sentences.extend(split_sentences(s))

    if not all_sentences:
        return {
            "avg_sentence_length": 15.0,
            "sentence_length_std": 5.0,
            "colloquial_ratio": 0.0,
            "classical_ratio": 0.0,
            "honorific_level": "MEDIUM",
            "preferred_particles": [],
            "common_patterns": [],
            "source_text_sample_count": 0,
        }

    lengths = [len(s) for s in all_sentences]
    avg_len = sum(lengths) / len(lengths)
    var = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    std_len = math.sqrt(var)

    full_text = "".join(samples)
    total_chars = max(1, len(full_text))

    colloquial_hits = sum(full_text.count(w) for w in COLLOQUIAL_MARKERS)
    classical_hits = sum(full_text.count(w) for w in CLASSICAL_MARKERS)

    colloquial_ratio = round(colloquial_hits / total_chars * 100, 2)
    classical_ratio = round(classical_hits / total_chars * 100, 2)

    particles = [w for w in COLLOQUIAL_MARKERS if full_text.count(w) >= 2]

    return {
        "avg_sentence_length": round(avg_len, 2),
        "sentence_length_std": round(std_len, 2),
        "colloquial_ratio": colloquial_ratio,
        "classical_ratio": classical_ratio,
        "honorific_level": "HIGH" if classical_ratio > 1.5 else ("LOW" if colloquial_ratio > 2.0 else "MEDIUM"),
        "preferred_particles": particles[:5],
        "common_patterns": [],
        "source_text_sample_count": len(samples),
    }


def detect_voice_drift(
    text: str,
    fingerprint: dict[str, Any] | None,
    lexicons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect voice drift and lexicon violations against character voice fingerprint."""
    issues: list[dict[str, Any]] = []
    if not text:
        return issues

    # 1. Lexicon checks (FORBIDDEN words)
    for lex in lexicons:
        pat = lex.get("pattern", "")
        if not pat:
            continue
        l_type = lex.get("lexicon_type", "ALLOWED")
        if l_type == "FORBIDDEN" and pat in text:
            issues.append({
                "issue_type": "VOICE_DRIFT",
                "severity": "ADVISORY",
                "source_text": pat,
                "description": f"使用了该人物禁用表达或口吻: \"{pat}\"",
                "evidence": [f"词表规则: {lex.get('entry_type', '')} 禁用 \"{pat}\""],
                "suggestion": "替换为符合该人物身份性格的惯用词",
                "root_cause_id": f"voice_lex_{pat}",
            })

    # 2. Fingerprint comparison
    if fingerprint:
        target_avg = float(fingerprint.get("avg_sentence_length", 15.0))
        target_std = float(fingerprint.get("sentence_length_std", 5.0))
        sents = split_sentences(text)
        if len(sents) >= 4:
            curr_avg = sum(len(s) for s in sents) / len(sents)
            if abs(curr_avg - target_avg) > max(10.0, target_std * 2.0):
                issues.append({
                    "issue_type": "VOICE_DRIFT",
                    "severity": "ADVISORY",
                    "source_text": text[:60] + "...",
                    "description": f"句长显著偏离指纹基准 (当前平均 {curr_avg:.1f} 字, 基准 {target_avg:.1f} 字)",
                    "evidence": [f"指纹基准句长: {target_avg}, 当前句长: {curr_avg:.1f}"],
                    "suggestion": "调整长短句节奏以保持人物特有语调",
                    "root_cause_id": "voice_drift_length",
                })
    return issues


def detect_vague_and_no_progress(paragraphs: list[str]) -> list[dict[str, Any]]:
    """Check for consecutive vague descriptions or dialogues with low narrative progress."""
    issues: list[dict[str, Any]] = []
    vague_markers = ["仿佛", "隐隐约约", "有一种说不出的", "周围的空气似乎", "静静地看着这一切", "心中涌起一股"]

    for idx, p in enumerate(paragraphs):
        p_clean = p.strip()
        hits = [m for m in vague_markers if m in p_clean]
        if len(hits) >= 2:
            issues.append({
                "issue_type": "EMPTY_DESCRIPTION",
                "severity": "ADVISORY",
                "source_text": p_clean[:80],
                "description": f"第 {idx + 1} 段包含多处空泛模糊描写",
                "evidence": hits,
                "suggestion": "替换为具体的视听感官细节、物理动作或环境交互",
                "root_cause_id": f"vague_{idx}",
            })
    return issues
