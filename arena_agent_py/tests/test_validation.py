import pytest

from arena_agent.models import (
    ChangeImpactAnalysis,
    CounterexampleRecord,
    DecisionRecord,
    FinalReport,
    GateResult,
    InterpretationOption,
    InventoryItem,
    KnowledgeUnit,
    LifecycleLogEntry,
    MinimizationRecord,
    Ownership,
    RepoAudit,
    WorkItem,
)
from arena_agent.graph import GraphEdge, GraphNode, KnowledgeGraph
from arena_agent.validation import (
    Finding,
    Severity,
    derive_overall_status_ceiling,
    has_errors,
    validate_change_impact_analysis,
    validate_counterexample_promotion,
    validate_counterexample_record,
    validate_decision_record,
    validate_final_report,
    validate_knowledge_graph,
    validate_knowledge_unit,
    validate_lifecycle_transition,
    validate_repo_audit,
    validate_work_item,
)
from arena_agent.vocab import (
    AuthorizationState,
    ClaimStatus,
    Confidence,
    Coverage,
    CounterexampleStage,
    DecisionStatus,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    GraphEdgeType,
    GraphNodeType,
    ImpactClass,
    ExtractionClass,
    LIFECYCLE_FAILURE_BRANCHES,
    LIFECYCLE_HAPPY_PATH,
    LifecycleState,
    OverallStatus,
    PresenceClass,
    ResolutionStatus,
    TrustTier,
    VerificationGate,
    VerificationMethod,
    VerificationResult,
    WorkItemStage,
    normalize_overall_status,
    to_pack_overall_status_label,
)


# ---------------------------------------------------------------------------
# Provenance Contract (v2 §16)
# ---------------------------------------------------------------------------


def test_default_provenance_matches_pack_section_16_field_list_exactly():
    """Conformance audit R12 (v2 §16 Provenance Contract).

    While preparing this test, comparing `_default_provenance()`'s field
    set against §16's literal text surfaced a genuine spec-vs-implementation
    gap, not merely a missing test: the pack lists 13 minimum provenance
    fields --

        source, source_type, repository, branch, commit, path, location,
        extraction_method, timestamp, classification, confidence,
        related_items, pack_version

    -- but `_default_provenance()` previously had only 12, missing
    `classification` entirely. `KnowledgeUnit`/`WorkItem` do carry a
    sibling top-level `evidence_class` field, but that is a *record-level*
    classification, not a field *inside the provenance dict itself* --
    it does not satisfy §16's requirement that the provenance block carry
    its own `classification` value (relevant e.g. for provenance attached
    to something that isn't itself a full classified record, such as a
    graph node/edge's provenance string). `classification` has been added
    to `_default_provenance()` (default `None`, like its sibling
    not-yet-supplied fields) so this test now passes against a codebase
    that actually matches the pack, rather than merely asserting whatever
    the implementation happened to already do.
    """
    from arena_agent.models import _default_provenance

    pack_section_16_fields = {
        "source",
        "source_type",
        "repository",
        "branch",
        "commit",
        "path",
        "location",
        "extraction_method",
        "timestamp",
        "classification",
        "confidence",
        "related_items",
        "pack_version",
    }
    assert set(_default_provenance().keys()) == pack_section_16_fields
    assert len(pack_section_16_fields) == 13


def test_provenance_is_attached_by_default_to_every_provenance_bearing_record():
    """Confirms KnowledgeUnit, WorkItem, and CounterexampleRecord (the three
    dataclasses declared with `provenance: dict[str, Any] =
    field(default_factory=_default_provenance)`) all actually get the
    corrected 13-field shape by default, not just the bare function in
    isolation -- i.e. the fix is wired to every call site, not only to
    `_default_provenance()` itself.
    """
    u = KnowledgeUnit(id="ARENA-X-Y-Z", meaning="m", evidence_class=EvidenceClass.OBSERVED, confidence=Confidence.HIGH)
    w = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    c = CounterexampleRecord(id="ARENA-CE-1")

    for record in (u, w, c):
        assert "classification" in record.provenance
        assert record.provenance["classification"] is None  # unset by default, like its siblings


def test_provenance_classification_defaults_to_none_like_its_pack_neighbor_confidence():
    """Semantic check for R12, beyond mere key presence.

    Investigation performed before choosing a default (per explicit
    instruction not to assume `None` is correct without checking §16's
    value semantics):

    - §16 lists `classification` and `confidence` side by side, with
      `confidence` cross-referenced to §5.1's fixed scale and
      `classification` implicitly meaning a §5 `EVIDENCE-CLASS` value.
      Neither is qualified as "may be omitted" or "must be pre-filled".
    - `confidence` -- already present in `_default_provenance()` before
      this fix -- is itself never auto-populated anywhere in this
      codebase; it defaults to `None` and stays `None` until a caller
      supplies a real value. That is the established, working precedent
      for how this dict already treats a required-but-caller-supplied
      field.
    - `KnowledgeUnit`/`WorkItem` already have a *separate*, non-optional,
      always-populated top-level `evidence_class` field -- but that is a
      record-level classification, a different concept from a
      provenance-*block*-level classification (relevant e.g. to a graph
      node/edge's provenance string, which has no `evidence_class` field
      to borrow from at all). Deriving `classification` from
      `evidence_class` would silently conflate the two concepts the pack
      keeps textually separate (§5 "Source-of-Truth Classes" vs. §16
      "Provenance Contract" are different sections with different
      referents), so this implementation deliberately does not do that.

    Conclusion: `None` is the correct default -- consistent with its
    pack-adjacent sibling field, not merely convenient. This test pins
    that reasoning down as an executable check of both defaults together,
    so a future change desyncing them (e.g. auto-deriving one but not the
    other) would be caught.
    """
    from arena_agent.models import _default_provenance

    p = _default_provenance()
    assert p["classification"] is None
    assert p["confidence"] is None  # established precedent this default follows


def test_provenance_classification_can_hold_a_real_evidence_class_value():
    """Confirms `classification` can meaningfully hold what §16 actually
    intends (a §5 `EVIDENCE-CLASS` value), not just that the key exists as
    an always-`None` placeholder -- i.e. this is a semantic capability
    check, not only a shape check.
    """
    u = KnowledgeUnit(id="ARENA-X-Y-Z", meaning="m", evidence_class=EvidenceClass.OBSERVED, confidence=Confidence.HIGH)
    u.provenance["classification"] = EvidenceClass.VERIFIED
    assert u.provenance["classification"] is EvidenceClass.VERIFIED
    # Confirms this is deliberately a *different* axis from the record's
    # own evidence_class (§5 provenance-block classification vs. §5
    # record-level classification are related but distinct per §16 vs.
    # the §9.1 axis table) -- setting one must not silently mutate the
    # other.
    assert u.evidence_class is EvidenceClass.OBSERVED


def test_verified_with_low_confidence_is_an_error():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.VERIFIED,
        confidence=Confidence.LOW,
    )
    findings = validate_knowledge_unit(u)
    assert any(f.code == "CONFIDENCE_TOO_LOW_FOR_CLASS" for f in findings)
    assert has_errors(findings)


def test_verified_with_high_confidence_is_clean():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.VERIFIED,
        confidence=Confidence.HIGH,
        provenance={"commit": "abc123"},
    )
    findings = validate_knowledge_unit(u)
    assert not has_errors(findings)


@pytest.mark.parametrize("evidence_class", [EvidenceClass.DERIVED, EvidenceClass.ARCHITECTURAL_PROPOSAL])
def test_derived_or_architectural_proposal_with_none_confidence_is_an_error(evidence_class):
    """Conformance audit R3 (v2 §5.1): the pack's own Confidence table has
    an explicit row "Required for: LOW -> DERIVED, ARCHITECTURAL-PROPOSAL",
    but MIN_CONFIDENCE_FOR_CLASS previously had no entry for either class,
    so a DERIVED/ARCHITECTURAL-PROPOSAL unit with confidence NONE passed
    validation silently. This confirms the newly added floor actually
    fires. Deliberately does NOT touch VERIFIED/EXECUTED's existing floor
    (MEDIUM) -- the pack's table vs. its explicit constraint sentence for
    those two classes have a separate, disclosed textual tension (see
    matrix row 1.11) that R3 does not attempt to resolve.
    """
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=evidence_class,
        confidence=Confidence.NONE,
    )
    findings = validate_knowledge_unit(u)
    assert any(f.code == "CONFIDENCE_TOO_LOW_FOR_CLASS" for f in findings)
    assert has_errors(findings)


@pytest.mark.parametrize("evidence_class", [EvidenceClass.DERIVED, EvidenceClass.ARCHITECTURAL_PROPOSAL])
def test_derived_or_architectural_proposal_with_low_confidence_is_clean(evidence_class):
    """Companion positive case for R3: LOW is the pack's documented floor
    for these two classes (not MEDIUM/HIGH), so a unit at exactly LOW must
    NOT be flagged -- confirms the floor is LOW, not accidentally set too
    high.
    """
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=evidence_class,
        confidence=Confidence.LOW,
    )
    findings = validate_knowledge_unit(u)
    assert not any(f.code == "CONFIDENCE_TOO_LOW_FOR_CLASS" for f in findings)


@pytest.mark.parametrize("evidence_class", [EvidenceClass.UNKNOWN, EvidenceClass.EXAMPLE])
def test_unknown_or_example_with_none_confidence_is_never_flagged(evidence_class):
    """Companion negative-of-the-negative for R3: the pack's table gives
    UNKNOWN/EXAMPLE their own "Required for: NONE" row -- i.e. NONE is
    the *documented, correct* confidence for these two classes, not a
    violation. Confirms MIN_CONFIDENCE_FOR_CLASS has (and must keep) no
    entry for either, so R3's new floors don't overreach into classes the
    table explicitly permits NONE for.
    """
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=evidence_class,
        confidence=Confidence.NONE,
    )
    findings = validate_knowledge_unit(u)
    assert not any(f.code == "CONFIDENCE_TOO_LOW_FOR_CLASS" for f in findings)


def test_implemented_status_without_repo_evidence_is_an_error():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.ARCHITECTURAL_PROPOSAL,
        confidence=Confidence.LOW,
        implementation_status=PresenceClass.PRESENT,
    )
    findings = validate_knowledge_unit(u)
    assert any(f.code == "IMPLEMENTED_WITHOUT_REPO_EVIDENCE" for f in findings)


def test_conflicting_without_decision_record_is_an_error():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.CONFLICTING,
        confidence=Confidence.LOW,
    )
    findings = validate_knowledge_unit(u)
    assert any(f.code == "CONFLICTING_WITHOUT_DECISION_RECORD" for f in findings)


def test_forbidden_dependency_present_is_an_error():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.DERIVED,
        confidence=Confidence.LOW,
        dependencies=["ARENA-A-B-C"],
        forbidden_dependencies=["ARENA-A-B-C"],
    )
    findings = validate_knowledge_unit(u)
    assert any(f.code == "FORBIDDEN_DEPENDENCY_PRESENT" for f in findings)


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------


def test_forward_one_step_is_legal():
    findings = validate_lifecycle_transition(LifecycleState.DISCOVERED, LifecycleState.CLASSIFIED)
    assert not has_errors(findings)


def test_skipping_states_is_illegal_run_task_done_antipattern():
    findings = validate_lifecycle_transition(LifecycleState.DISCOVERED, LifecycleState.VERIFIED)
    assert has_errors(findings)
    assert any(f.code == "LIFECYCLE_SKIPPED_STATE" for f in findings)


def test_backward_transition_is_illegal():
    findings = validate_lifecycle_transition(LifecycleState.VERIFIED, LifecycleState.PLANNED)
    assert has_errors(findings)
    assert any(f.code == "LIFECYCLE_BACKWARD_TRANSITION" for f in findings)


def test_legal_failure_branch_is_accepted():
    findings = validate_lifecycle_transition(LifecycleState.EXECUTING, LifecycleState.CRASHED)
    assert not has_errors(findings)


def test_illegal_failure_branch_is_rejected():
    # CRASHED is only reachable from EXECUTING, not from PLANNED.
    findings = validate_lifecycle_transition(LifecycleState.PLANNED, LifecycleState.CRASHED)
    assert has_errors(findings)
    assert any(f.code == "LIFECYCLE_ILLEGAL_TRANSITION" for f in findings)


@pytest.mark.parametrize("from_state,to_state", list(LIFECYCLE_FAILURE_BRANCHES.items()))
def test_every_documented_failure_branch_transition_is_individually_legal(from_state, to_state):
    """Conformance audit R6 (v2 §9.1): `test_illegal_failure_branch_is_rejected`
    and `test_legal_failure_branch_is_accepted` only exercised one of the 7
    documented happy-path-state -> failure-branch transitions
    (EXECUTING -> CRASHED). This closes the remaining 6 by asserting every
    entry in `LIFECYCLE_FAILURE_BRANCHES` -- not just one representative
    sample of it -- is actually accepted as legal by the validator itself,
    so a future accidental edit to the failure-branch table or the
    validator can't silently desync the two without a test failing.
    """
    findings = validate_lifecycle_transition(from_state, to_state)
    assert not has_errors(findings), (
        f"{from_state.value} -> {to_state.value} is documented in "
        "LIFECYCLE_FAILURE_BRANCHES as a legal failure transition but "
        f"validate_lifecycle_transition rejected it: {findings}"
    )


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (happy_state, failure_state)
        for happy_state in LIFECYCLE_HAPPY_PATH
        for failure_state in LIFECYCLE_FAILURE_BRANCHES.values()
        if LIFECYCLE_FAILURE_BRANCHES.get(happy_state) != failure_state
    ],
)
def test_failure_branch_from_wrong_source_state_is_illegal(from_state, to_state):
    """Conformance audit R6 companion check (v2 §9.1): each documented
    failure state is reachable from exactly ONE happy-path state -- not
    from any other. This exhaustively checks every (wrong-source,
    failure-state) combination outside the one legal pairing per branch,
    so a validator bug that accepted a failure transition from an
    unrelated state couldn't slip past a test suite that only ever
    checked the single documented pairing.
    """
    findings = validate_lifecycle_transition(from_state, to_state)
    assert has_errors(findings), (
        f"{from_state.value} -> {to_state.value} is NOT the documented "
        "pairing for this failure state, but validate_lifecycle_transition "
        "accepted it without error."
    )


def test_noop_transition_is_always_legal():
    findings = validate_lifecycle_transition(LifecycleState.PLANNED, LifecycleState.PLANNED)
    assert findings == []


# ---------------------------------------------------------------------------
# Work Item
# ---------------------------------------------------------------------------


def _full_gates(result: VerificationResult = VerificationResult.PASS_) -> list[GateResult]:
    return [
        GateResult(gate=g, method=VerificationMethod.MANUAL_REVIEW, result=result, evidence="ok")
        for g in VerificationGate
    ]


def test_missing_gates_is_a_warning():
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    findings = validate_work_item(item)
    assert any(f.code == "VERIFICATION_GATES_INCOMPLETE" for f in findings)


def test_pass_without_evidence_is_an_error():
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.gates = [GateResult(gate=VerificationGate.IDENTITY, result=VerificationResult.PASS_)]
    findings = validate_work_item(item)
    assert any(f.code == "PASS_WITHOUT_EVIDENCE" for f in findings)


def test_executing_without_owner_is_an_error():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.EXECUTING,
    )
    findings = validate_work_item(item)
    assert any(f.code == "EXECUTING_WITHOUT_OWNER" for f in findings)


def test_verified_without_lifecycle_log_is_an_error():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.VERIFIED,
        gates=_full_gates(),
        postconditions=["output matches spec"],
    )
    findings = validate_work_item(item)
    assert any(f.code == "VERIFIED_WITHOUT_LIFECYCLE_LOG" for f in findings)


def test_fully_valid_verified_work_item_has_no_errors():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.VERIFIED,
        execution_state=ExecutionState.COMPLETED,
        authorization_state=AuthorizationState.GRANTED,
        evidence_state=EvidenceState.VALIDATED,
        gates=_full_gates(),
        postconditions=["output matches spec"],
        ownership=Ownership(owner="agent-1", claimed_at="now", status=ClaimStatus.ACTIVE),
    )
    item.log("execution", actor="agent-1")
    item.log("observation", actor="agent-1")
    item.log("verification", actor="agent-1")
    findings = validate_work_item(item)
    assert not has_errors(findings)


@pytest.mark.parametrize(
    "stage_value",
    ["plan", "authorization", "execution", "observation", "verification"],
)
def test_lifecycle_log_entry_with_a_real_stage_is_not_flagged(stage_value):
    # Positive path for Phase 5B Recommendation R19 (row 4.4): all 5 of
    # v2 §31's separated stages -- exactly as this codebase has always
    # spelled them (lowercase, no Appendix A entry mandates otherwise) --
    # must continue to be accepted with no finding, boundary values
    # included (not just some arbitrary middle value).
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.log(stage_value, actor="agent-1")
    findings = validate_work_item(item)
    assert not any(f.code == "INVALID_LIFECYCLE_LOG_STAGE" for f in findings)


@pytest.mark.parametrize(
    "stage_value",
    ["excecution", "Execution", "EXECUTION", "cleanup", "", "6", None],
)
def test_lifecycle_log_entry_with_an_invalid_stage_is_rejected(stage_value):
    # Negative path for R19: a typo ("excecution"), a wrong-case variant
    # ("Execution"/"EXECUTION" -- proving the closed set is case-sensitive,
    # not just spelling-sensitive), an unrelated word ("cleanup"), an
    # empty string, a bare digit, and None must all be rejected the same
    # way DecisionRecord.overrides_stop_condition and
    # FinalReport.stop_conditions_triggered already reject out-of-set
    # values (R15) -- this closed set gets the same treatment, not a
    # weaker one.
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.lifecycle_log.append(LifecycleLogEntry(stage=stage_value, actor="agent-1"))
    findings = validate_work_item(item)
    assert any(f.code == "INVALID_LIFECYCLE_LOG_STAGE" for f in findings)


def test_lifecycle_log_entry_stage_accepts_the_enum_member_directly():
    # Semantic check (not just shape): a WorkItemStage enum member itself
    # (not merely its string value) must be accepted, since cli.py's call
    # sites now pass WorkItemStage members directly rather than bare
    # strings.
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.log(WorkItemStage.PLAN, actor="agent-1")
    assert item.lifecycle_log[0].stage == WorkItemStage.PLAN
    assert item.lifecycle_log[0].stage == "plan"
    findings = validate_work_item(item)
    assert not any(f.code == "INVALID_LIFECYCLE_LOG_STAGE" for f in findings)


def test_resource_conservation_violation_detected():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        resource_budget={
            "tool_calls": {"initial_total": 10, "available": 5, "reserved": 2, "consumed": 2}
            # 5+2+2=9 != 10 -> should be flagged
        },
    )
    findings = validate_work_item(item)
    assert any(f.code == "RESOURCE_CONSERVATION_VIOLATED" for f in findings)


def test_resource_conservation_respected_passes():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        resource_budget={
            "tool_calls": {"initial_total": 10, "available": 6, "reserved": 2, "consumed": 2}
        },
    )
    findings = validate_work_item(item)
    assert not any(f.code == "RESOURCE_CONSERVATION_VIOLATED" for f in findings)


# ---------------------------------------------------------------------------
# Decision Record
# ---------------------------------------------------------------------------


def test_resolved_without_attribution_is_an_error():
    d = DecisionRecord(
        id="ARENA-DECISION-20260101-001",
        question="q",
        status=DecisionStatus.RESOLVED,
        chosen_option_id="A",
        options=[InterpretationOption(option_id="A", description="d")],
    )
    findings = validate_decision_record(d)
    assert any(f.code == "RESOLVED_WITHOUT_ATTRIBUTION" for f in findings)


def test_override_without_attribution_is_an_error():
    d = DecisionRecord(
        id="ARENA-DECISION-20260101-001",
        question="q",
        overrides_stop_condition=2,
    )
    findings = validate_decision_record(d)
    assert any(f.code == "OVERRIDE_WITHOUT_ATTRIBUTION" for f in findings)


def test_valid_override_with_attribution_and_scope_is_clean():
    d = DecisionRecord(
        id="ARENA-DECISION-20260101-001",
        question="q",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        decided_by_trust_tier=TrustTier.ARENA_SUPERVISOR,
        override_scope="this work item only",
        chosen_option_id="A",
        options=[InterpretationOption(option_id="A", description="d")],
        status=DecisionStatus.RESOLVED,
    )
    findings = validate_decision_record(d)
    assert not has_errors(findings)


def test_invalid_stop_condition_number_rejected():
    d = DecisionRecord(id="ARENA-DECISION-20260101-001", question="q", overrides_stop_condition=99)
    findings = validate_decision_record(d)
    assert any(f.code == "INVALID_STOP_CONDITION_NUMBER" for f in findings)


# ---------------------------------------------------------------------------
# Counterexample staging
# ---------------------------------------------------------------------------


def test_promote_to_observed_failure_requires_behavior_fields():
    record = CounterexampleRecord(id="ARENA-CE-20260101-001", first_divergence="x")
    findings = validate_counterexample_promotion(record, CounterexampleStage.OBSERVED_FAILURE)
    assert any(f.code == "OBSERVED_FAILURE_MISSING_FIELDS" for f in findings)


def test_promote_to_reproducible_defect_requires_confirmation():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        first_divergence="x",
        expected_behavior="e",
        actual_behavior="a",
        stage=CounterexampleStage.OBSERVED_FAILURE,
        reproduction_command="run.sh",
        confirmed=False,
    )
    findings = validate_counterexample_promotion(record, CounterexampleStage.REPRODUCIBLE_DEFECT)
    assert any(f.code == "REPRODUCIBLE_DEFECT_NOT_CONFIRMED" for f in findings)


def test_promote_to_reproducible_defect_succeeds_when_confirmed():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        first_divergence="x",
        expected_behavior="e",
        actual_behavior="a",
        stage=CounterexampleStage.OBSERVED_FAILURE,
        reproduction_command="run.sh",
        confirmed=True,
    )
    findings = validate_counterexample_promotion(record, CounterexampleStage.REPRODUCIBLE_DEFECT)
    assert not has_errors(findings)


def test_backward_promotion_rejected():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001", stage=CounterexampleStage.REPRODUCIBLE_DEFECT
    )
    findings = validate_counterexample_promotion(record, CounterexampleStage.RAW_DIVERGENCE)
    assert any(f.code == "COUNTEREXAMPLE_BACKWARD_PROMOTION" for f in findings)


def test_minimization_requires_full_checklist():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        stage=CounterexampleStage.REPRODUCIBLE_DEFECT,
        minimization=MinimizationRecord(),  # all False by default
    )
    findings = validate_counterexample_promotion(record, CounterexampleStage.MINIMIZED_REPRODUCER)
    assert any(f.code == "MINIMIZATION_CHECKLIST_INCOMPLETE" for f in findings)


def test_minimization_succeeds_with_full_checklist():
    m = MinimizationRecord()
    for k in m.checklist:
        m.checklist[k] = True
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        stage=CounterexampleStage.REPRODUCIBLE_DEFECT,
        minimization=m,
    )
    findings = validate_counterexample_promotion(record, CounterexampleStage.MINIMIZED_REPRODUCER)
    assert not has_errors(findings)


# ---------------------------------------------------------------------------
# Repo Audit
# ---------------------------------------------------------------------------


def test_present_without_evidence_is_an_error():
    audit = RepoAudit(
        id="ARENA-AUDIT-20260101-001",
        repository="repo",
        inventory=[InventoryItem(path="src/", kind="dir", classification=PresenceClass.PRESENT)],
    )
    findings = validate_repo_audit(audit)
    assert any(f.code == "PRESENT_WITHOUT_EVIDENCE" for f in findings)


def test_modified_repository_is_an_error():
    audit = RepoAudit(id="ARENA-AUDIT-20260101-001", repository="repo", repository_modified=True)
    findings = validate_repo_audit(audit)
    assert any(f.code == "AUDIT_MODIFIED_REPOSITORY" for f in findings)


def test_unknown_identity_no_reason_is_a_warning():
    """Conformance audit R5 (v2 §6.2): a Repository Reality Audit that
    reports commit_identity_known=False (the repository-identity fallback
    path) MUST also record identity_failure_reason -- silently reporting
    "identity unknown" with no explanation is itself an anti-pattern this
    pack exists to catch. Until now UNKNOWN_IDENTITY_NO_REASON existed in
    validation.py but had zero test coverage.
    """
    audit = RepoAudit(
        id="ARENA-AUDIT-20260101-001",
        repository="repo",
        commit=None,
        commit_identity_known=False,
        identity_failure_reason="",
    )
    findings = validate_repo_audit(audit)
    assert any(f.code == "UNKNOWN_IDENTITY_NO_REASON" for f in findings)
    assert any(f.severity == Severity.WARNING for f in findings if f.code == "UNKNOWN_IDENTITY_NO_REASON")


def test_unknown_identity_with_reason_recorded_is_not_flagged():
    """Companion negative-of-the-negative case for R5: when the fallback
    path is used *and* a reason is recorded, no UNKNOWN_IDENTITY_NO_REASON
    finding should fire -- the check is specifically about the missing
    explanation, not about the fallback itself being disallowed.
    """
    audit = RepoAudit(
        id="ARENA-AUDIT-20260101-001",
        repository="repo",
        commit=None,
        commit_identity_known=False,
        identity_failure_reason="detached HEAD, no upstream tracking ref",
    )
    findings = validate_repo_audit(audit)
    assert not any(f.code == "UNKNOWN_IDENTITY_NO_REASON" for f in findings)


def test_sampled_without_method_is_a_warning():
    audit = RepoAudit(
        id="ARENA-AUDIT-20260101-001",
        repository="repo",
        inventory=[
            InventoryItem(
                path="deep/",
                kind="dir",
                classification=PresenceClass.PRESENT,
                coverage=Coverage.SAMPLED,
                evidence="seen",
            )
        ],
    )
    findings = validate_repo_audit(audit)
    assert any(f.code == "SAMPLED_WITHOUT_METHOD" for f in findings)


# ---------------------------------------------------------------------------
# Change Impact Analysis
# ---------------------------------------------------------------------------


def test_unassessed_categories_is_an_error():
    analysis = ChangeImpactAnalysis(id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C")
    findings = validate_change_impact_analysis(analysis)
    assert any(f.code == "IMPACT_CATEGORIES_UNASSESSED" for f in findings)


def test_fully_assessed_none_impact_is_clean():
    analysis = ChangeImpactAnalysis(id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C")
    for cat in analysis.categories:
        analysis.categories[cat].classification = ImpactClass.NONE
        analysis.categories[cat].details = "no impact"
    findings = validate_change_impact_analysis(analysis)
    assert not has_errors(findings)


def test_approved_with_unmitigated_high_risk_is_an_error():
    analysis = ChangeImpactAnalysis(id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C")
    for cat in analysis.categories:
        analysis.categories[cat].classification = ImpactClass.NONE
        analysis.categories[cat].details = "no impact"
    analysis.categories["invariants"].classification = ImpactClass.SEMANTIC
    analysis.categories["invariants"].details = ""  # no mitigation
    analysis.approved = True
    findings = validate_change_impact_analysis(analysis)
    assert any(f.code == "APPROVED_WITH_UNMITIGATED_RISK" for f in findings)


def test_change_impact_target_with_active_claim_by_another_agent_is_flagged():
    # Positive path for Phase 5B Recommendation R21 (row 4.11): v2 §36
    # requires flagging a conflict, per §24.1, when the changed unit has
    # open claims from other agents.
    target = WorkItem(
        id="ARENA-A-B-C",
        title="t",
        responsibility="r",
        ownership=Ownership(owner="agent-1", claimed_at="now", status=ClaimStatus.ACTIVE),
    )
    analysis = ChangeImpactAnalysis(
        id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C", proposed_by="agent-2"
    )
    findings = validate_change_impact_analysis(analysis, work_items={"ARENA-A-B-C": target})
    assert any(f.code == "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM" for f in findings)


def test_change_impact_target_claimed_by_the_same_proposer_is_not_a_conflict():
    # Negative-adjacent path: the proposer *is* the current claim owner --
    # this is the same agent continuing its own work, not a cross-agent
    # conflict, so §36's rule must not fire.
    target = WorkItem(
        id="ARENA-A-B-C",
        title="t",
        responsibility="r",
        ownership=Ownership(owner="agent-1", claimed_at="now", status=ClaimStatus.ACTIVE),
    )
    analysis = ChangeImpactAnalysis(
        id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C", proposed_by="agent-1"
    )
    findings = validate_change_impact_analysis(analysis, work_items={"ARENA-A-B-C": target})
    assert not any(f.code == "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM" for f in findings)


def test_change_impact_target_with_released_claim_is_not_a_conflict():
    # Negative path: a RELEASED (or EXPIRED) claim is not an "open claim"
    # per §24.1 -- only ACTIVE counts. Proves the check reads
    # ownership.status, not merely whether an owner string is present.
    target = WorkItem(
        id="ARENA-A-B-C",
        title="t",
        responsibility="r",
        ownership=Ownership(owner="agent-1", claimed_at="now", status=ClaimStatus.RELEASED),
    )
    analysis = ChangeImpactAnalysis(
        id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C", proposed_by="agent-2"
    )
    findings = validate_change_impact_analysis(analysis, work_items={"ARENA-A-B-C": target})
    assert not any(f.code == "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM" for f in findings)


def test_change_impact_conflict_check_is_skipped_without_a_work_items_mapping():
    # Negative path: omitting work_items (the default) must not silently
    # assert "no conflict" as if it had been checked -- it must simply not
    # run, mirroring validate_wiki_references's optional-mapping
    # semantics. This analysis targets a genuinely claimed work item, but
    # since no mapping is supplied to prove it, no finding is produced --
    # this is "not checked", not "checked and clean".
    analysis = ChangeImpactAnalysis(
        id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C", proposed_by="agent-2"
    )
    findings = validate_change_impact_analysis(analysis)
    assert not any(f.code == "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM" for f in findings)


def test_change_impact_conflict_check_is_skipped_when_target_is_not_in_the_mapping():
    # Negative path: target_unit_id absent from a *supplied* mapping (the
    # unit wasn't found / wasn't a WorkItem) must also not produce a
    # finding -- an unresolved target is not evidence of a conflict.
    analysis = ChangeImpactAnalysis(
        id="ARENA-IMPACT-20260101-001", target_unit_id="ARENA-A-B-C", proposed_by="agent-2"
    )
    findings = validate_change_impact_analysis(analysis, work_items={})
    assert not any(f.code == "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM" for f in findings)


# ---------------------------------------------------------------------------
# Final Report / Completion Contract
# ---------------------------------------------------------------------------


def test_complete_without_full_checklist_is_an_error():
    report = FinalReport(id="ARENA-REPORT-1", overall_status="COMPLETE")
    findings = validate_final_report(report)
    assert any(f.code == "INCOMPLETE_COMPLETION_CHECKLIST" for f in findings)
    assert any(f.code == "STATUS_MASQUERADING" for f in findings)
    assert has_errors(findings)


def test_complete_with_full_checklist_is_clean():
    report = FinalReport(id="ARENA-REPORT-1", overall_status="COMPLETE")
    for k in report.completion_checklist:
        report.completion_checklist[k] = True
    findings = validate_final_report(report)
    assert not has_errors(findings)


# ---------------------------------------------------------------------------
# Counterexample record self-consistency (v2 §22.1-22.4), as opposed to
# validate_counterexample_promotion which checks the *transition*.
# ---------------------------------------------------------------------------


def test_counterexample_record_missing_first_divergence_is_an_error():
    record = CounterexampleRecord(id="ARENA-CE-20260101-001", first_divergence="")
    findings = validate_counterexample_record(record)
    assert any(f.code == "MISSING_FIRST_DIVERGENCE" for f in findings)


def test_counterexample_record_at_observed_failure_requires_expected_actual():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        first_divergence="d1",
        stage=CounterexampleStage.OBSERVED_FAILURE,
        expected_behavior="",
        actual_behavior="",
    )
    findings = validate_counterexample_record(record)
    assert any(f.code == "OBSERVED_FAILURE_MISSING_FIELDS" for f in findings)


def test_counterexample_record_fully_populated_at_its_stage_is_clean():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        first_divergence="d1",
        stage=CounterexampleStage.OBSERVED_FAILURE,
        expected_behavior="expected",
        actual_behavior="actual",
    )
    findings = validate_counterexample_record(record)
    assert not has_errors(findings)


def test_counterexample_record_reproducible_defect_requires_command_and_confirmation():
    record = CounterexampleRecord(
        id="ARENA-CE-20260101-001",
        first_divergence="d1",
        stage=CounterexampleStage.REPRODUCIBLE_DEFECT,
        expected_behavior="e",
        actual_behavior="a",
        reproduction_command=None,
        confirmed=False,
    )
    findings = validate_counterexample_record(record)
    codes = {f.code for f in findings}
    assert "REPRODUCIBLE_DEFECT_NO_COMMAND" in codes
    assert "REPRODUCIBLE_DEFECT_NOT_CONFIRMED" in codes


# ---------------------------------------------------------------------------
# Knowledge Graph validation (v2 §34)
# ---------------------------------------------------------------------------


def test_graph_with_no_contradictions_or_divergences_is_clean():
    g = KnowledgeGraph()
    g.add_node(GraphNode(id="N1", node_type=GraphNodeType.COMPONENT, label="core", planned=True, provenance="unit-1"))
    g.add_node(GraphNode(id="N2", node_type=GraphNodeType.COMPONENT, label="core", planned=False, provenance="audit-1"))
    findings = validate_knowledge_graph(g)
    assert findings == []


def test_graph_contradiction_edge_is_flagged_as_warning_not_silently_resolved():
    g = KnowledgeGraph()
    g.add_node(GraphNode(id="N1", node_type=GraphNodeType.CLAIM, label="a", planned=True, provenance="unit-1"))
    g.add_node(GraphNode(id="N2", node_type=GraphNodeType.CLAIM, label="b", planned=True, provenance="unit-2"))
    g.add_edge(GraphEdge(id="E1", from_id="N1", edge_type=GraphEdgeType.CONTRADICTS, to_id="N2", provenance="unit-1"))
    findings = validate_knowledge_graph(g)
    assert any(f.code == "GRAPH_HAS_CONTRADICTIONS" and f.severity == Severity.WARNING for f in findings)
    assert not has_errors(findings)  # a contradiction is a fact to surface, not itself a rule violation


def test_graph_planned_node_without_observed_counterpart_is_flagged():
    g = KnowledgeGraph()
    g.add_node(GraphNode(id="N1", node_type=GraphNodeType.REQUIREMENT, label="must-do-x", planned=True, provenance="unit-1"))
    findings = validate_knowledge_graph(g)
    assert any(f.code == "GRAPH_HAS_PLANNED_NOT_OBSERVED" for f in findings)


def test_graph_derived_edge_without_notes_is_flagged():
    g = KnowledgeGraph()
    g.add_node(GraphNode(id="N1", node_type=GraphNodeType.COMPONENT, label="a", planned=False, provenance="audit-1"))
    g.add_node(GraphNode(id="N2", node_type=GraphNodeType.COMPONENT, label="b", planned=False, provenance="audit-1"))
    g.add_edge(
        GraphEdge(id="E1", from_id="N1", edge_type=GraphEdgeType.DEPENDS_ON, to_id="N2", provenance="inferred", derived=True, notes="")
    )
    findings = validate_knowledge_graph(g)
    assert any(f.code == "DERIVED_EDGE_WITHOUT_EXPLANATION" for f in findings)


# ---------------------------------------------------------------------------
# v2 §9.1 independent-axis enforcement (found during pack-conformance audit:
# lifecycle_state previously could reach AUTHORIZED/VERIFIED milestones
# while authorization_state/evidence_state sat at their collapsed defaults,
# which is exactly the "single generic status field" anti-pattern §9.1
# forbids).
# ---------------------------------------------------------------------------


def test_authorized_lifecycle_state_without_granted_authorization_state_is_an_error():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.AUTHORIZED,
        # authorization_state left at its default NOT-REQUESTED
    )
    findings = validate_work_item(item)
    assert any(f.code == "AUTHORIZED_WITHOUT_GRANTED_AUTHORIZATION_STATE" for f in findings)


def test_authorized_lifecycle_state_with_granted_or_attenuated_is_clean_on_that_axis():
    for auth in (AuthorizationState.GRANTED, AuthorizationState.ATTENUATED):
        item = WorkItem(
            id="ARENA-WORK-1",
            title="t",
            responsibility="r",
            lifecycle_state=LifecycleState.AUTHORIZED,
            authorization_state=auth,
        )
        findings = validate_work_item(item)
        assert not any(f.code == "AUTHORIZED_WITHOUT_GRANTED_AUTHORIZATION_STATE" for f in findings)


def test_executing_without_execution_state_update_is_a_warning_not_an_error():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.EXECUTING,
        ownership=Ownership(owner="agent-1", claimed_at="now", status=ClaimStatus.ACTIVE),
        # execution_state left at its default PLANNED
    )
    findings = validate_work_item(item)
    matches = [f for f in findings if f.code == "EXECUTING_WITHOUT_EXECUTION_STATE_UPDATE"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_verified_without_validated_evidence_state_is_an_error():
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        lifecycle_state=LifecycleState.VERIFIED,
        evidence_state=EvidenceState.CAPTURED,  # not VALIDATED
    )
    findings = validate_work_item(item)
    assert any(f.code == "VERIFIED_WITHOUT_SUFFICIENT_EVIDENCE_STATE" for f in findings)


# ---------------------------------------------------------------------------
# Follow-on hardening: extraction_class, override_residual_risk,
# related-ID fields, resolution_status/fix_reference (audit findings
# #2, #4, #5, #7).
# ---------------------------------------------------------------------------


def test_missing_extraction_class_is_a_warning():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.MEDIUM,
        # extraction_class left at its default None
    )
    findings = validate_knowledge_unit(u)
    matches = [f for f in findings if f.code == "MISSING_EXTRACTION_CLASS"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_extraction_class_set_clears_the_warning():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.MEDIUM,
        extraction_class=ExtractionClass.DEFINITION,
    )
    findings = validate_knowledge_unit(u)
    assert not any(f.code == "MISSING_EXTRACTION_CLASS" for f in findings)


def test_extraction_class_is_a_real_enum_not_a_bare_string():
    u = KnowledgeUnit(
        id="ARENA-X-Y-Z",
        meaning="claim",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.MEDIUM,
        extraction_class=ExtractionClass.INVARIANT,
    )
    assert isinstance(u.extraction_class, ExtractionClass)
    assert u.extraction_class.value == "INVARIANT"


def test_override_without_residual_risk_is_a_warning():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=3,
        override_scope="this work item",
        # override_residual_risk left at its default ""
    )
    findings = validate_decision_record(d)
    matches = [f for f in findings if f.code == "OVERRIDE_WITHOUT_RESIDUAL_RISK"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_override_with_residual_risk_and_scope_is_clean_on_that_axis():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=3,
        override_scope="this work item",
        override_residual_risk="accepted risk: component X may be unstable until Y lands",
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_RESIDUAL_RISK" for f in findings)
    assert not any(f.code == "OVERRIDE_WITHOUT_SCOPE" for f in findings)


def test_decision_record_supports_related_unit_and_work_item_ids():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_unit_ids=["ARENA-UNIT-1"],
        related_work_item_ids=["ARENA-WORK-1"],
    )
    assert d.related_unit_ids == ["ARENA-UNIT-1"]
    assert d.related_work_item_ids == ["ARENA-WORK-1"]


# ---------------------------------------------------------------------------
# Override affected-unit linkage (v2 §26.2, conformance audit
# Recommendation R16, row 3.4)
#
# Scope, locked with the user before any implementation existed:
#   - An override with no related_unit_ids/related_work_item_ids at all is
#     not machine-auditable against a specific affected record -- flagged
#     as OVERRIDE_WITHOUT_LINKED_UNIT (WARNING, matching
#     OVERRIDE_WITHOUT_SCOPE/OVERRIDE_WITHOUT_RESIDUAL_RISK's existing
#     severity tier for adjacent §26.2 completeness gaps -- the override
#     itself is still valid and attributed, just less traceable).
#   - A related_unit_ids/related_work_item_ids entry that does not resolve
#     against an optionally-supplied {id: record} mapping is
#     RELATED_UNIT_NOT_FOUND/RELATED_WORK_ITEM_NOT_FOUND (ERROR), mirroring
#     validate_final_report's existing RELATED_DECISION_NOT_FOUND pattern
#     exactly (dict mapping, not a bare iterable, so "not supplied" is
#     distinguishable from "supplied but dangling"; silent skip, not a
#     manufactured pass, when the mapping is omitted).
#   - Deliberately NOT implemented (disclosed gap, not an oversight): §26.2
#     states "an override never retroactively changes a classification"
#     (its own worked example: overriding Stop Condition #2 does not make
#     a component's classification become IMPLEMENTED/PRESENT). Detecting
#     that a classification was in fact *strengthened because of* an
#     override would require a causal/temporal comparison this codebase
#     cannot make: neither KnowledgeUnit.implementation_status/
#     evidence_class nor WorkItem.evidence_class carry any history or
#     snapshot to compare a "before" value against (unlike lifecycle_state,
#     which has lifecycle_log). Inferring strengthening from the *current*
#     value alone (e.g. flagging overrides_stop_condition == 2 alongside a
#     related unit currently classified PRESENT) was explicitly considered
#     and rejected: the current value could have predated the override
#     entirely, and asserting a causal link the data cannot support is
#     exactly the kind of invented proxy already rejected for a materially
#     identical reason in InventoryItem's docstring (Recommendation R4,
#     row 1.14 -- "two SAMPLED items can legitimately share identical, true
#     evidence" -- a mechanical proxy would create false confidence that an
#     actual normative requirement was verified, when only a coincidental
#     data shape was).
# ---------------------------------------------------------------------------


def test_override_without_any_linked_unit_or_work_item_is_a_warning():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        # related_unit_ids / related_work_item_ids left at their defaults: []
    )
    findings = validate_decision_record(d)
    matches = [f for f in findings if f.code == "OVERRIDE_WITHOUT_LINKED_UNIT"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_override_with_a_related_unit_id_is_not_flagged_for_missing_linkage():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        related_unit_ids=["ARENA-UNIT-1"],
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_LINKED_UNIT" for f in findings)


def test_override_with_a_related_work_item_id_is_not_flagged_for_missing_linkage():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        related_work_item_ids=["ARENA-WORK-1"],
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_LINKED_UNIT" for f in findings)


def test_decision_without_an_override_is_never_flagged_for_missing_linkage():
    """A DecisionRecord that isn't an override at all has nothing to link --
    OVERRIDE_WITHOUT_LINKED_UNIT must only fire when overrides_stop_condition
    is actually set."""
    d = DecisionRecord(id="ARENA-DEC-1", question="q", raised_by="agent-1")
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_LINKED_UNIT" for f in findings)


def test_related_unit_id_check_is_skipped_without_a_units_mapping():
    """Mirrors validate_final_report's decisions-mapping precedent: if the
    caller doesn't supply units, dangling related_unit_ids are not checked
    at all -- silence, not a manufactured pass."""
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_unit_ids=["ARENA-UNIT-DOES-NOT-EXIST"],
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "RELATED_UNIT_NOT_FOUND" for f in findings)


def test_dangling_related_unit_id_is_flagged_when_units_mapping_supplied():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_unit_ids=["ARENA-UNIT-DOES-NOT-EXIST"],
    )
    findings = validate_decision_record(d, units={})
    matches = [f for f in findings if f.code == "RELATED_UNIT_NOT_FOUND"]
    assert matches
    assert matches[0].severity == Severity.ERROR


def test_related_unit_id_that_resolves_is_not_flagged():
    unit = KnowledgeUnit(id="ARENA-UNIT-1", meaning="m", evidence_class=EvidenceClass.OBSERVED, confidence=Confidence.HIGH)
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_unit_ids=["ARENA-UNIT-1"],
    )
    findings = validate_decision_record(d, units={"ARENA-UNIT-1": unit})
    assert not any(f.code == "RELATED_UNIT_NOT_FOUND" for f in findings)


def test_related_work_item_id_check_is_skipped_without_a_work_items_mapping():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_work_item_ids=["ARENA-WORK-DOES-NOT-EXIST"],
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "RELATED_WORK_ITEM_NOT_FOUND" for f in findings)


def test_dangling_related_work_item_id_is_flagged_when_work_items_mapping_supplied():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_work_item_ids=["ARENA-WORK-DOES-NOT-EXIST"],
    )
    findings = validate_decision_record(d, work_items={})
    matches = [f for f in findings if f.code == "RELATED_WORK_ITEM_NOT_FOUND"]
    assert matches
    assert matches[0].severity == Severity.ERROR


def test_related_work_item_id_that_resolves_is_not_flagged():
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        related_work_item_ids=["ARENA-WORK-1"],
    )
    findings = validate_decision_record(d, work_items={"ARENA-WORK-1": item})
    assert not any(f.code == "RELATED_WORK_ITEM_NOT_FOUND" for f in findings)


def test_current_classification_values_alone_never_produce_a_strengthening_finding():
    """Disclosed scope boundary: a related unit currently classified
    PRESENT/IMPLEMENTED alongside an override of Stop Condition #2 (the
    pack's own worked example of an illegitimate retroactive
    classification change) produces no finding from this function --
    validate_decision_record has no way to know whether that
    classification predates the override, and must not invent a causal
    claim the data cannot support."""
    unit = KnowledgeUnit(
        id="ARENA-UNIT-1",
        meaning="m",
        evidence_class=EvidenceClass.IMPLEMENTED,
        confidence=Confidence.MEDIUM,
        implementation_status=PresenceClass.PRESENT,
    )
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        related_unit_ids=["ARENA-UNIT-1"],
    )
    findings = validate_decision_record(d, units={"ARENA-UNIT-1": unit})
    # No finding of any kind references "strengthen" or a classification
    # mismatch -- only the (here, satisfied) linkage/dangling-reference
    # checks this function actually implements.
    assert not any("strengthen" in f.message.lower() for f in findings)
    assert not any(f.code == "RELATED_UNIT_NOT_FOUND" for f in findings)
    assert not any(f.code == "OVERRIDE_WITHOUT_LINKED_UNIT" for f in findings)


# ---------------------------------------------------------------------------
# Override trust-tier attribution (v2 §3 Trust Model / §26.2, conformance
# audit Recommendation R1, row 1.5)
#
# Scope, locked with the user before any implementation existed:
#   - §26.2 requires an override decision to record "the authorizing party
#     AND their role in the trust hierarchy" -- decided_by already covers
#     the party; decided_by_trust_tier (new, optional field) covers the
#     role. Narrow scope: this is validated only in relation to
#     overrides_stop_condition, mirroring OVERRIDE_WITHOUT_ATTRIBUTION's
#     existing override-only gating exactly. raised_by, Ownership.owner,
#     and WorkItem's authorization CLI option are untouched -- §3/§26.2
#     make no attribution claim about those.
#   - OVERRIDE_WITHOUT_TRUST_TIER (ERROR): an override with no
#     decided_by_trust_tier recorded at all. Same severity tier as
#     OVERRIDE_WITHOUT_ATTRIBUTION (both are the "authorizing party and
#     their role" bullet -- the two halves of one mandatory element, not
#     an ERROR/WARNING split within it).
#   - OVERRIDE_BY_AGENT_SELF (ERROR): an override whose
#     decided_by_trust_tier is explicitly ARENA_AGENT. Directly enforces
#     §26.2's literal text: "A Stop Condition MUST NOT be lifted by the
#     agent's own initiative." This checks the declared trust-tier
#     classification, not string-matching decided_by (free text is not a
#     reliable place to detect self-authorization).
#   - A non-override decision has no trust-tier obligation at all: it may
#     set or omit decided_by_trust_tier freely, with no finding either
#     way -- the field carries no validation meaning outside the override
#     context (see DecisionRecord's docstring).
#   - TrustTier itself carries NO ordering/magnitude/"stronger than"
#     relation -- it must never be conflated with the v2 §11 Authority
#     Contract's attenuation algebra (derive(A, C) ⪯ A), which this
#     package deliberately does not implement (Recommendation R7). This
#     is a closed-set actor-identity classification only.
# ---------------------------------------------------------------------------


def test_override_without_trust_tier_is_an_error():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="supervisor-1",
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        # decided_by_trust_tier left at its default None
    )
    findings = validate_decision_record(d)
    matches = [f for f in findings if f.code == "OVERRIDE_WITHOUT_TRUST_TIER"]
    assert matches
    assert matches[0].severity == Severity.ERROR


@pytest.mark.parametrize("tier", [TrustTier.HUMAN_GOVERNANCE, TrustTier.ARENA_SUPERVISOR])
def test_override_with_human_governance_or_supervisor_trust_tier_is_not_flagged(tier):
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="authorizer-1",
        decided_by_trust_tier=tier,
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_TRUST_TIER" for f in findings)
    assert not any(f.code == "OVERRIDE_BY_AGENT_SELF" for f in findings)


def test_override_authorized_by_the_agent_tier_itself_is_an_error():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="agent-1",
        decided_by_trust_tier=TrustTier.ARENA_AGENT,
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
    )
    findings = validate_decision_record(d)
    matches = [f for f in findings if f.code == "OVERRIDE_BY_AGENT_SELF"]
    assert matches
    assert matches[0].severity == Severity.ERROR
    # The agent DID supply a trust tier -- OVERRIDE_WITHOUT_TRUST_TIER must
    # not also fire; these are two distinct findings for two distinct
    # failure modes (absent vs. explicitly disallowed), not the same check.
    assert not any(f.code == "OVERRIDE_WITHOUT_TRUST_TIER" for f in findings)


def test_decision_without_an_override_is_never_flagged_for_missing_trust_tier():
    """A DecisionRecord that isn't an override at all has no trust-tier
    obligation -- OVERRIDE_WITHOUT_TRUST_TIER must only fire when
    overrides_stop_condition is actually set."""
    d = DecisionRecord(id="ARENA-DEC-1", question="q", raised_by="agent-1")
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_TRUST_TIER" for f in findings)
    assert not any(f.code == "OVERRIDE_BY_AGENT_SELF" for f in findings)


def test_non_override_decision_with_a_trust_tier_set_is_not_flagged_either_way():
    """A non-override decision may optionally carry decided_by_trust_tier
    (e.g. recorded for informational completeness) with no validation
    consequence either way -- the field has no meaning outside the
    override context, so setting it must not manufacture a finding that
    wouldn't otherwise exist, even if the value happens to be
    ARENA_AGENT (self-override is only meaningful for an actual
    override)."""
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        decided_by="agent-1",
        decided_by_trust_tier=TrustTier.ARENA_AGENT,
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "OVERRIDE_WITHOUT_TRUST_TIER" for f in findings)
    assert not any(f.code == "OVERRIDE_BY_AGENT_SELF" for f in findings)


def test_override_without_attribution_and_without_trust_tier_reports_both_independently():
    """decided_by (the party) and decided_by_trust_tier (their role) are
    the two halves of one §26.2 bullet -- both must be checked
    independently, not one subsuming the other: an override missing both
    must report both findings, not just one."""
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
    )
    findings = validate_decision_record(d)
    codes = {f.code for f in findings}
    assert "OVERRIDE_WITHOUT_ATTRIBUTION" in codes
    assert "OVERRIDE_WITHOUT_TRUST_TIER" in codes


def test_trust_tier_ordering_is_never_used_anywhere_in_validation_source():
    """TrustTier is a closed-set actor-identity classification, not a
    magnitude: unlike every enum in this codebase (all of which subclass
    ``str`` via ``_StrEnum`` and therefore inherit an incidental
    lexicographic ``<``/``>`` as a base-class artifact, not a declared
    domain semantic), no code path in validation.py may actually use
    ordering comparison on a TrustTier value -- doing so would smuggle in
    the v2 §11 Authority Contract's attenuation algebra
    (``derive(A, C) ⪯ A``) this package deliberately does not implement
    (Recommendation R7). This is an AST-based check of validation.py's own
    source (not a check of the enum class itself, since the inherited
    ``str.__lt__`` is unavoidable and not itself the concern) -- it
    confirms no ``<``, ``>``, ``<=``, or ``>=`` comparison anywhere in that
    module has a TrustTier-related name on either side.
    """
    import ast
    import inspect

    import arena_agent.validation as validation_module

    source = inspect.getsource(validation_module)
    tree = ast.parse(source)
    trust_tier_names = {"TrustTier", "decided_by_trust_tier", "trust_tier"}

    def mentions_trust_tier(node: ast.AST) -> bool:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in trust_tier_names:
                return True
            if isinstance(sub, ast.Attribute) and sub.attr in trust_tier_names:
                return True
        return False

    ordering_ops = (ast.Lt, ast.Gt, ast.LtE, ast.GtE)
    offending: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            has_ordering_op = any(isinstance(op, ordering_ops) for op in node.ops)
            if has_ordering_op and any(mentions_trust_tier(o) for o in operands):
                offending.append(ast.dump(node))

    assert offending == [], (
        f"validation.py contains an ordering comparison involving TrustTier: {offending}"
    )


def test_fully_valid_override_with_trust_tier_is_clean():
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        overrides_stop_condition=2,
        decided_by="human-governance-1",
        decided_by_trust_tier=TrustTier.HUMAN_GOVERNANCE,
        override_scope="this work item only",
        override_residual_risk="accepted risk: component remains ABSENT",
        related_unit_ids=["ARENA-UNIT-1"],
    )
    findings = validate_decision_record(d)
    assert not has_errors(findings)


def test_superseded_decision_without_forward_link_is_a_warning():
    """Conformance audit R11 (v2 §15.1 / §23 usage notes): a DecisionRecord
    marked SUPERSEDED without supersedes_decision_id has no traceable link
    to whatever superseded it -- i.e. HISTORICAL/superseded evidence is not
    silently treated as still-current, but the forward link that would let
    a reader actually find the newer record is missing. This closes the
    previously-untested SUPERSEDED_WITHOUT_FORWARD_LINK finding.
    """
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        status=DecisionStatus.SUPERSEDED,
        # supersedes_decision_id left at its default None
    )
    findings = validate_decision_record(d)
    matches = [f for f in findings if f.code == "SUPERSEDED_WITHOUT_FORWARD_LINK"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_superseded_decision_with_forward_link_is_clean_on_that_axis():
    """Companion negative-of-the-negative case for R11: a SUPERSEDED
    decision that *does* record supersedes_decision_id must not be flagged.
    """
    d = DecisionRecord(
        id="ARENA-DEC-1",
        question="q",
        raised_by="agent-1",
        status=DecisionStatus.SUPERSEDED,
        supersedes_decision_id="ARENA-DEC-2",
    )
    findings = validate_decision_record(d)
    assert not any(f.code == "SUPERSEDED_WITHOUT_FORWARD_LINK" for f in findings)


def test_non_superseded_decision_is_never_flagged_for_missing_forward_link():
    """A decision that is merely OPEN or RESOLVED (not SUPERSEDED) has no
    forward-link obligation at all -- confirms the check is scoped
    specifically to the SUPERSEDED status axis, not fired unconditionally.
    """
    d = DecisionRecord(id="ARENA-DEC-1", question="q", raised_by="agent-1", status=DecisionStatus.OPEN)
    findings = validate_decision_record(d)
    assert not any(f.code == "SUPERSEDED_WITHOUT_FORWARD_LINK" for f in findings)


def test_counterexample_resolution_status_is_a_real_enum_not_a_bare_string():
    record = CounterexampleRecord(
        id="ARENA-CE-1",
        resolution_status=ResolutionStatus.FIXED,
        fix_reference="commit abc123",
    )
    assert isinstance(record.resolution_status, ResolutionStatus)
    assert record.resolution_status.value == "FIXED"
    assert record.fix_reference == "commit abc123"


def test_counterexample_resolution_status_defaults_to_open():
    record = CounterexampleRecord(id="ARENA-CE-1")
    assert record.resolution_status == ResolutionStatus.OPEN
    assert record.fix_reference == ""


# ---------------------------------------------------------------------------
# Final Report: overall_status derivation ceiling, legacy PARTIAL alias,
# BLOCKED substantiation (reporting/export conformance follow-on).
# ---------------------------------------------------------------------------


def _fully_checked_report(**kwargs) -> FinalReport:
    r = FinalReport(id="ARENA-REPORT-1", **kwargs)
    for k in r.completion_checklist:
        r.completion_checklist[k] = True
    return r


def test_legacy_partial_spelling_normalizes_to_incomplete_at_construction():
    r = FinalReport(id="ARENA-REPORT-1", overall_status="PARTIAL")
    assert r.overall_status == OverallStatus.INCOMPLETE
    assert isinstance(r.overall_status, OverallStatus)


def test_legacy_partial_spelling_normalizes_on_later_assignment_too():
    r = FinalReport(id="ARENA-REPORT-1")
    r.overall_status = "PARTIAL"
    assert r.overall_status == OverallStatus.INCOMPLETE
    r.overall_status = "complete"  # case-insensitive
    assert r.overall_status == OverallStatus.COMPLETE


def test_normalize_overall_status_accepts_enum_passthrough():
    assert normalize_overall_status(OverallStatus.BLOCKED) is OverallStatus.BLOCKED


def test_to_pack_overall_status_label_collapses_to_three_pack_values():
    assert to_pack_overall_status_label(OverallStatus.COMPLETE) == "COMPLETE"
    assert to_pack_overall_status_label(OverallStatus.BLOCKED) == "BLOCKED"
    assert to_pack_overall_status_label(OverallStatus.COMPLETE_WITH_WARNINGS) == "PARTIAL"
    assert to_pack_overall_status_label(OverallStatus.INCOMPLETE) == "PARTIAL"


def _report_with_ceiling(ceiling: str) -> FinalReport:
    """
    Build a FinalReport whose evidence genuinely supports exactly the given
    ceiling ("COMPLETE" / "COMPLETE-WITH-WARNINGS" / "INCOMPLETE"), for the
    exhaustive negative-path matrix below. Uses only the report's own
    fields (no `other_findings`) so the ceiling is fully determined by
    what's asserted here.
    """
    if ceiling == "INCOMPLETE":
        return FinalReport(id="ARENA-REPORT-1")  # checklist not full
    if ceiling == "COMPLETE-WITH-WARNINGS":
        return _fully_checked_report(evidence_gaps=["something unresolved"])
    if ceiling == "COMPLETE":
        return _fully_checked_report()
    raise ValueError(ceiling)  # pragma: no cover - test-authoring guard


@pytest.mark.parametrize(
    "claimed,ceiling,should_accept",
    [
        # claimed status,        evidence ceiling,          accept?
        ("COMPLETE",              "COMPLETE",               True),
        ("COMPLETE",              "COMPLETE-WITH-WARNINGS", False),
        ("COMPLETE",              "INCOMPLETE",             False),
        ("COMPLETE-WITH-WARNINGS", "COMPLETE-WITH-WARNINGS", True),
        ("COMPLETE-WITH-WARNINGS", "INCOMPLETE",             False),
        ("INCOMPLETE",            "INCOMPLETE",             True),
        ("INCOMPLETE",            "COMPLETE-WITH-WARNINGS", True),
        ("INCOMPLETE",            "COMPLETE",               True),
    ],
)
def test_status_masquerading_negative_path_matrix(claimed, ceiling, should_accept):
    """
    Authoritative contract test for the claimed-status / evidence-ceiling
    relationship (v2 §39/§43 STATUS_MASQUERADING). Covers every
    non-BLOCKED combination the reviewed matrix calls out, including the
    two directions that are easy to get backwards:

    - claiming *above* the ceiling is always rejected (rows where
      should_accept is False), and
    - claiming *at or below* the ceiling is always accepted -- a
      conservative claim (e.g. INCOMPLETE when the evidence would actually
      support COMPLETE) is legitimate and must NOT be flagged as
      masquerading merely because the evidence could support something
      better.
    """
    r = _report_with_ceiling(ceiling)
    r.overall_status = claimed
    findings = validate_final_report(r)
    masquerading = any(f.code == "STATUS_MASQUERADING" for f in findings)
    assert masquerading is (not should_accept), (
        f"claimed={claimed} ceiling={ceiling}: expected "
        f"{'no' if should_accept else 'a'} STATUS_MASQUERADING finding, "
        f"got findings={[f.code for f in findings]}"
    )
    if should_accept:
        assert not has_errors(findings), [f.code for f in findings]


@pytest.mark.parametrize(
    "blocker_kwargs,should_accept",
    [
        ({"blocking_reason": "Waiting on ARENA-DECISION-7 to resolve the API surface."}, True),
        ({}, False),  # BLOCKED claimed with no substantiation at all
    ],
)
def test_blocked_negative_path_matrix(blocker_kwargs, should_accept):
    """
    BLOCKED is orthogonal to the completion ceiling (it is never returned
    by derive_overall_status_ceiling and is checked independently): accept
    only when a blocker is actually demonstrated, reject otherwise --
    regardless of what the completion checklist looks like.
    """
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", **blocker_kwargs)
    findings = validate_final_report(r)
    unjustified = any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)
    assert unjustified is (not should_accept)
    if should_accept:
        assert not has_errors(findings), [f.code for f in findings]


def test_ceiling_is_incomplete_when_checklist_is_not_full():
    r = FinalReport(id="ARENA-REPORT-1")
    assert derive_overall_status_ceiling(r) == OverallStatus.INCOMPLETE


def test_ceiling_is_incomplete_when_checklist_full_but_errors_present():
    r = _fully_checked_report()
    other = [Finding(Severity.ERROR, "SOME_ERROR", "boom")]
    assert derive_overall_status_ceiling(r, other) == OverallStatus.INCOMPLETE


def test_ceiling_is_complete_with_warnings_when_evidence_gaps_remain():
    r = _fully_checked_report(evidence_gaps=["something unresolved"])
    assert derive_overall_status_ceiling(r) == OverallStatus.COMPLETE_WITH_WARNINGS


def test_ceiling_is_complete_with_warnings_when_open_decisions_remain():
    r = _fully_checked_report(open_decision_ids=["ARENA-DECISION-1"])
    assert derive_overall_status_ceiling(r) == OverallStatus.COMPLETE_WITH_WARNINGS


def test_ceiling_is_complete_with_warnings_when_other_findings_include_warning():
    r = _fully_checked_report()
    other = [Finding(Severity.WARNING, "SOME_WARNING", "heads up")]
    assert derive_overall_status_ceiling(r, other) == OverallStatus.COMPLETE_WITH_WARNINGS


def test_ceiling_is_complete_when_checklist_full_and_nothing_outstanding():
    r = _fully_checked_report()
    assert derive_overall_status_ceiling(r) == OverallStatus.COMPLETE


def test_claiming_complete_above_the_ceiling_is_status_masquerading():
    r = _fully_checked_report(evidence_gaps=["gap"], overall_status="COMPLETE")
    findings = validate_final_report(r)
    assert any(f.code == "STATUS_MASQUERADING" for f in findings)
    assert has_errors(findings)


def test_claiming_complete_with_warnings_above_incomplete_ceiling_is_masquerading():
    r = FinalReport(id="ARENA-REPORT-1", overall_status="COMPLETE-WITH-WARNINGS")
    findings = validate_final_report(r)
    assert any(f.code == "STATUS_MASQUERADING" for f in findings)
    assert any(f.code == "INCOMPLETE_COMPLETION_CHECKLIST" for f in findings)


def test_claiming_at_or_below_the_ceiling_is_not_masquerading():
    r = _fully_checked_report(evidence_gaps=["gap"], overall_status="COMPLETE-WITH-WARNINGS")
    findings = validate_final_report(r)
    assert not any(f.code == "STATUS_MASQUERADING" for f in findings)
    assert not has_errors(findings)


def test_open_decisions_produce_a_warning_finding():
    r = _fully_checked_report(open_decision_ids=["ARENA-DECISION-1"], overall_status="COMPLETE-WITH-WARNINGS")
    findings = validate_final_report(r)
    matches = [f for f in findings if f.code == "OPEN_REQUIRED_DECISION"]
    assert matches
    assert matches[0].severity == Severity.WARNING


def test_blocked_without_any_substantiation_is_an_error():
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED")
    findings = validate_final_report(r)
    assert any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)
    assert has_errors(findings)


def test_blocked_with_blocking_reason_is_substantiated():
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", blocking_reason="waiting on decision X")
    findings = validate_final_report(r)
    assert not any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)


def test_blocked_with_unverified_blocking_decision_id_is_not_accepted_or_silently_rejected():
    # An ID alone is a pointer, not proof: without the actual DecisionRecord
    # to confirm it's OPEN, this must not be treated as substantiated --
    # but it also shouldn't be flatly rejected the way "nothing at all" is.
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", blocking_decision_id="ARENA-DECISION-1")
    findings = validate_final_report(r)
    assert any(f.code == "BLOCKING_DECISION_NOT_VERIFIED" for f in findings)
    assert any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)


def test_blocked_with_verified_open_decision_is_substantiated():
    decision = DecisionRecord(id="ARENA-DECISION-1", question="q", raised_by="agent-1", status=DecisionStatus.OPEN)
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", blocking_decision_id="ARENA-DECISION-1")
    findings = validate_final_report(r, blocking_decision=decision)
    assert not any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)
    assert not any(f.code == "BLOCKING_DECISION_NOT_OPEN" for f in findings)


def test_blocked_with_verified_resolved_decision_is_rejected():
    decision = DecisionRecord(
        id="ARENA-DECISION-1", question="q", raised_by="agent-1", status=DecisionStatus.RESOLVED
    )
    r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", blocking_decision_id="ARENA-DECISION-1")
    findings = validate_final_report(r, blocking_decision=decision)
    assert any(f.code == "BLOCKING_DECISION_NOT_OPEN" for f in findings)
    assert any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)
    assert has_errors(findings)


def test_blocking_reason_placeholder_text_is_not_meaningful():
    for junk in ("TBD", "x", "blocked", "N/A", "..."):
        r = FinalReport(id="ARENA-REPORT-1", overall_status="BLOCKED", blocking_reason=junk)
        findings = validate_final_report(r)
        assert any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings), junk
        assert any(f.code == "BLOCKING_REASON_NOT_MEANINGFUL" for f in findings), junk


def test_blocking_reason_with_real_substance_is_meaningful():
    r = FinalReport(
        id="ARENA-REPORT-1",
        overall_status="BLOCKED",
        blocking_reason="Waiting on ARENA-DECISION-7 to resolve API surface before proceeding.",
    )
    findings = validate_final_report(r)
    assert not any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)
    assert not any(f.code == "BLOCKING_REASON_NOT_MEANINGFUL" for f in findings)


def test_blocked_with_unoverridden_stop_condition_is_substantiated():
    r = FinalReport(
        id="ARENA-REPORT-1",
        overall_status="BLOCKED",
        stop_conditions_triggered=[{"condition": 3, "overridden": False}],
    )
    findings = validate_final_report(r)
    assert not any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)


def test_blocked_with_only_overridden_stop_conditions_is_still_unsubstantiated():
    r = FinalReport(
        id="ARENA-REPORT-1",
        overall_status="BLOCKED",
        stop_conditions_triggered=[{"condition": 3, "overridden": True}],
    )
    findings = validate_final_report(r)
    assert any(f.code == "UNJUSTIFIED_BLOCKED_STATUS" for f in findings)


@pytest.mark.parametrize("condition_number", [1, 13])
def test_stop_conditions_triggered_with_a_real_condition_number_is_not_flagged(
    condition_number,
):
    # v2 §26.1 defines exactly 13 numbered Stop Conditions; both ends of
    # that closed range must be accepted, not just some arbitrary middle
    # value, since off-by-one boundary errors are the most common way a
    # "1-13" check goes wrong.
    r = FinalReport(
        id="ARENA-REPORT-1",
        overall_status="BLOCKED",
        stop_conditions_triggered=[{"condition": condition_number, "overridden": False}],
    )
    findings = validate_final_report(r)
    assert not any(f.code == "INVALID_STOP_CONDITION_NUMBER" for f in findings)


@pytest.mark.parametrize("condition_number", [0, 14, 99, "3", None])
def test_stop_conditions_triggered_with_an_invalid_condition_number_is_rejected(
    condition_number,
):
    # Negative path for Phase 5B Recommendation R15: stop_conditions_triggered
    # previously accepted any value at all in its "condition" key -- an
    # out-of-range integer, a stringified number, or a missing/None value
    # all passed validation silently. All must now be rejected the same
    # way DecisionRecord.overrides_stop_condition already rejects an
    # out-of-range override.
    r = FinalReport(
        id="ARENA-REPORT-1",
        overall_status="BLOCKED",
        stop_conditions_triggered=[{"condition": condition_number, "overridden": False}],
    )
    findings = validate_final_report(r)
    assert any(f.code == "INVALID_STOP_CONDITION_NUMBER" for f in findings)


def test_stop_conditions_triggered_invalid_number_is_flagged_even_when_not_blocked():
    # The check must not be gated on overall_status == BLOCKED: a Stop
    # Condition can be triggered-then-overridden on a report that goes on
    # to claim COMPLETE, and the condition number claim still needs
    # provenance regardless of what status the report ultimately claims.
    r = _fully_checked_report(overall_status="COMPLETE")
    r.stop_conditions_triggered = [{"condition": 14, "overridden": True}]
    findings = validate_final_report(r)
    assert any(f.code == "INVALID_STOP_CONDITION_NUMBER" for f in findings)


# ---------------------------------------------------------------------------
# Phase 5B Recommendation R17 (row 3.5, v2 §26.2): a report's related
# Decision Records that override a Stop Condition must have that condition
# number actually reflected in stop_conditions_triggered -- an override MUST
# NOT make the trigger invisible in the Final Report. `decisions` is a
# {id: DecisionRecord} mapping (mirrors validate_wiki_references' dict shape)
# so the check can tell "not supplied" apart from "supplied but dangling".
# These are negative-path tests demonstrating the gap *before* any
# implementation change, per the same discipline used for R3/R15/R19/R21.
# ---------------------------------------------------------------------------


def _resolved_override_decision(**kwargs) -> DecisionRecord:
    defaults = dict(
        id="ARENA-DECISION-20260101-001",
        question="Proceed past Stop Condition 2?",
        raised_by="agent-1",
        overrides_stop_condition=2,
        status=DecisionStatus.RESOLVED,
        chosen_option_id="opt-a",
        decided_by="human-governance-1",
        decided_by_trust_tier=TrustTier.HUMAN_GOVERNANCE,
        override_scope="this work item only",
        override_residual_risk="component may not exist yet; proceeding with PLANNED status",
    )
    defaults.update(kwargs)
    return DecisionRecord(**defaults)


def _decisions_map(*decisions: DecisionRecord) -> dict[str, DecisionRecord]:
    return {d.id: d for d in decisions}


def test_final_report_omitting_a_related_overridden_stop_condition_is_flagged():
    # Case 3 from the R17 negative-path checklist, and the exact gap
    # demonstrated during investigation: a fully valid, fully-attributed
    # override decision (zero findings on its own) paired with a Final
    # Report that never mentions the Stop Condition it overrode at all --
    # currently silent, which is precisely what v2 §26.2 forbids ("MUST
    # still appear ... never a way to make the Stop invisible"). ERROR,
    # not WARNING: §26.2 states this with "MUST".
    d = _resolved_override_decision()
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[d.id],
        stop_conditions_triggered=[],
    )
    findings = validate_final_report(r, decisions=_decisions_map(d))
    override_findings = [f for f in findings if f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT"]
    assert len(override_findings) == 1
    assert override_findings[0].severity == Severity.ERROR


def test_final_report_that_lists_the_overridden_condition_is_not_flagged():
    # Case 2 from the checklist: the same override decision, but this time
    # the report *does* carry the condition number in
    # stop_conditions_triggered -- the accountable, correct shape -- so no
    # finding should fire. The report may still legitimately reach
    # COMPLETE once the override is properly reflected.
    d = _resolved_override_decision()
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[d.id],
        stop_conditions_triggered=[{"condition": 2, "overridden": True}],
    )
    findings = validate_final_report(r, decisions=_decisions_map(d))
    assert not any(f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT" for f in findings)
    assert not any(f.code == "RELATED_DECISION_NOT_FOUND" for f in findings)


def test_final_report_override_check_is_skipped_without_a_decisions_mapping():
    # Same "skip if unresolved, don't fabricate a pass" semantics used by
    # R21's work_items mapping: if the caller does not supply the decisions
    # a report claims to relate to, neither check (dangling-reference or
    # override-visibility) must silently assume either compliance or
    # violation -- both simply do not run.
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=["ARENA-DECISION-20260101-001"],
        stop_conditions_triggered=[],
    )
    findings = validate_final_report(r)
    assert not any(f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT" for f in findings)
    assert not any(f.code == "RELATED_DECISION_NOT_FOUND" for f in findings)


def test_final_report_decision_without_an_override_is_not_flagged():
    # Case 1 from the checklist: a related decision that does not override
    # any Stop Condition at all (overrides_stop_condition is None) must
    # never trigger the override-visibility check -- it has nothing to be
    # reflected in stop_conditions_triggered.
    d = DecisionRecord(
        id="ARENA-DECISION-20260101-002",
        question="Which interpretation of an ambiguous spec sentence applies?",
        raised_by="agent-1",
        status=DecisionStatus.RESOLVED,
        chosen_option_id="opt-a",
        decided_by="human-governance-1",
    )
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[d.id],
        stop_conditions_triggered=[],
    )
    findings = validate_final_report(r, decisions=_decisions_map(d))
    assert not any(f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT" for f in findings)


def test_final_report_flags_each_missing_override_independently():
    # Case 8 from the checklist: two related override decisions, only one
    # reflected -- the omitted one must still be flagged even though the
    # report is not wholly silent about overrides in general.
    d_reflected = _resolved_override_decision(
        id="ARENA-DECISION-20260101-003", overrides_stop_condition=2
    )
    d_omitted = _resolved_override_decision(
        id="ARENA-DECISION-20260101-004", overrides_stop_condition=5
    )
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[d_reflected.id, d_omitted.id],
        stop_conditions_triggered=[{"condition": 2, "overridden": True}],
    )
    findings = validate_final_report(r, decisions=_decisions_map(d_reflected, d_omitted))
    override_findings = [f for f in findings if f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT"]
    assert len(override_findings) == 1
    assert "5" in override_findings[0].message


def test_final_report_with_dangling_related_decision_id_is_flagged():
    # Case 7 from the checklist: related_decision_ids names an ID that
    # doesn't resolve in the supplied mapping -- a report must not point
    # at a decision that isn't there, the same rule already applied to
    # WikiPage references (WIKI_REFERENCE_NOT_FOUND).
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=["ARENA-DECISION-99990101-999"],
        stop_conditions_triggered=[],
    )
    findings = validate_final_report(r, decisions={})
    assert any(f.code == "RELATED_DECISION_NOT_FOUND" for f in findings)
    assert any(f.severity == Severity.ERROR for f in findings if f.code == "RELATED_DECISION_NOT_FOUND")


def test_final_report_unrelated_decision_alongside_a_reflected_override_is_clean():
    # The regression test explicitly called out: an unrelated Decision B
    # (no override at all) alongside Decision A's correctly-reflected
    # override must not introduce any finding of its own.
    a = _resolved_override_decision(id="ARENA-DECISION-20260101-005", overrides_stop_condition=3)
    b = DecisionRecord(
        id="ARENA-DECISION-20260101-006",
        question="Unrelated ambiguity",
        raised_by="agent-1",
    )
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[a.id, b.id],
        stop_conditions_triggered=[{"condition": 3, "overridden": True}],
    )
    findings = validate_final_report(r, decisions=_decisions_map(a, b))
    assert not any(f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT" for f in findings)
    assert not any(f.code == "RELATED_DECISION_NOT_FOUND" for f in findings)


def test_final_report_unrelated_status_strengthening_alongside_override_remains_valid():
    # Case 5 from the checklist: an overridden Stop Condition coexisting
    # with an otherwise legitimate, unrelated completion-checklist item
    # must not be suppressed or masked by the override machinery -- the
    # two are independent claims, and this report should reach COMPLETE
    # cleanly once the override is properly reflected.
    d = _resolved_override_decision()
    r = _fully_checked_report(
        overall_status="COMPLETE",
        related_decision_ids=[d.id],
        stop_conditions_triggered=[{"condition": 2, "overridden": True}],
        known_limitations=["unrelated, independently-documented limitation"],
    )
    findings = validate_final_report(r, decisions=_decisions_map(d))
    assert not any(f.code == "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT" for f in findings)
    assert not any(f.severity == Severity.ERROR for f in findings)


def test_core_arena_principle_checklist_defaults_to_all_false_and_is_advisory():
    r = _fully_checked_report(overall_status="COMPLETE")
    assert all(v is False for v in r.core_principle_checklist.values())
    # Advisory (§43 is non-normative) -- an unchecked principle checklist
    # must not by itself block a legitimately-earned COMPLETE.
    findings = validate_final_report(r)
    assert not has_errors(findings)
