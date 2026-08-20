from novelagent.integrations.extraction import extract_candidates


def test_extraction_preserves_modality_and_offsets():
    text = "也许林舟在客栈后门留下了记号。"
    candidates = extract_candidates(text, known_aliases={"林舟"})
    assert len(candidates) == 1
    c = candidates[0]
    assert c.subject == "林舟"
    assert c.modality == "HYPOTHETICAL"
    assert c.status == "REVIEW_REQUIRED"
    assert c.source_start == 0
    assert c.source_end == len(text)


def test_unknown_entity_is_review_required():
    text = "陆清风拔剑出鞘。"
    candidates = extract_candidates(text, known_aliases=set())
    assert any(c.subject == "陆清风" and c.status == "REVIEW_REQUIRED" for c in candidates)
