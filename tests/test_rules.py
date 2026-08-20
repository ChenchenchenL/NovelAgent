import pytest

from novelagent.domain.rules import ItemTransition, claim_is_low_risk, validate_item_transition


def test_unique_item_transfer_requires_current_holder():
    assert validate_item_transition(
        current_state="HELD",
        current_holder="林舟",
        transition=ItemTransition("TRANSFERRED", "林舟", "沈砚"),
        unique_item=True,
    ) == "HELD"
    with pytest.raises(ValueError, match="source"):
        validate_item_transition(
            current_state="HELD",
            current_holder="林舟",
            transition=ItemTransition("TRANSFERRED", "沈砚", "赵明"),
            unique_item=True,
        )


def test_destroyed_item_cannot_be_transferred():
    with pytest.raises(ValueError):
        validate_item_transition(
            current_state="DESTROYED",
            current_holder=None,
            transition=ItemTransition("TRANSFERRED", None, "沈砚"),
            unique_item=True,
        )


def test_only_explicit_low_risk_claims_auto_confirm():
    assert claim_is_low_risk(modality="ACTUAL", subject_resolved=True, predicate="located_at", explicit=True)
    assert not claim_is_low_risk(modality="DREAMED", subject_resolved=True, predicate="located_at", explicit=True)
    assert not claim_is_low_risk(modality="ACTUAL", subject_resolved=True, predicate="betrayed", explicit=True)
