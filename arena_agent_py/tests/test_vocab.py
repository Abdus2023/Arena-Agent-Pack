from arena_agent.vocab import (
    INAPPLICABLE,
    EvidenceClass,
    LifecycleState,
    LIFECYCLE_FAILURE_BRANCHES,
    LIFECYCLE_HAPPY_PATH,
    VerificationResult,
)


def test_str_enum_values_serialize_as_plain_strings():
    assert EvidenceClass.VERIFIED == "VERIFIED"
    assert EvidenceClass.VERIFIED.value == "VERIFIED"


def test_v1_inapplicable_alias_matches_v2_not_applicable():
    # pack v2 Appendix C changelog item #4
    assert INAPPLICABLE is VerificationResult.NOT_APPLICABLE


def test_invalid_enum_value_raises():
    import pytest

    with pytest.raises(ValueError):
        EvidenceClass("NOT-A-REAL-CLASS")


def test_claim_status_and_decision_status_disclose_non_pack_provenance():
    """Conformance audit R22: ClaimStatus/DecisionStatus were previously
    mildly mislabeled -- their docstrings cited a pack section as if it
    defined a closed vocabulary, when in fact neither section names an
    enumerated set (and neither appears in Appendix A). This asserts the
    corrected docstrings actually say so, so the disclosure can't silently
    regress back to an implied-pack-provenance claim.
    """
    from arena_agent.vocab import ClaimStatus, DecisionStatus

    assert "implementation-only vocabulary" in (ClaimStatus.__doc__ or "").lower()
    assert "no" in (ClaimStatus.__doc__ or "").lower() and "appendix a" in (ClaimStatus.__doc__ or "").lower()

    assert "implementation-only vocabulary" in (DecisionStatus.__doc__ or "").lower()
    assert "appendix a" in (DecisionStatus.__doc__ or "").lower()


def test_lifecycle_happy_path_is_ordered():
    assert LIFECYCLE_HAPPY_PATH[0] == LifecycleState.DISCOVERED
    assert LIFECYCLE_HAPPY_PATH[-1] == LifecycleState.VERIFIED
    assert len(LIFECYCLE_HAPPY_PATH) == 8


def test_lifecycle_failure_branches_match_pack_text_exactly():
    # v2 §9.1 documents exactly 7 failure branches for the 8 happy-path
    # states -- NORMALIZED has no documented failure branch in the pack
    # itself. This is a faithful transcription of the source text (and
    # incidentally a gap worth flagging back to the pack authors), not an
    # omission introduced by this implementation.
    assert set(LIFECYCLE_FAILURE_BRANCHES.keys()) == set(LIFECYCLE_HAPPY_PATH) - {
        LifecycleState.NORMALIZED
    }
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.DISCOVERED] == LifecycleState.REJECTED
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.CLASSIFIED] == LifecycleState.AMBIGUOUS
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.PLANNED] == LifecycleState.BLOCKED
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.AUTHORIZED] == LifecycleState.FAILED
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.EXECUTING] == LifecycleState.CRASHED
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.OBSERVED] == LifecycleState.CONFLICTING
    assert LIFECYCLE_FAILURE_BRANCHES[LifecycleState.VERIFIED] == LifecycleState.INVALIDATED
