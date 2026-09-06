"""
Record dataclasses for the Arena Agent pack.

Every class here corresponds to a template in the companion Markdown
template pack:

    KnowledgeUnit           <-> arena-knowledge-unit-table-template.md   (v2 §7/§8, v1 §6/§7)
    WorkItem                <-> arena-work-item-template.md              (v2 §27, v1 §27)
    DecisionRecord          <-> arena-decision-record-template.md        (v2 §23/§26.2, v1 §24/§25)
    CounterexampleRecord    <-> arena-counterexample-template.md         (v2 §22, v1 §22/§23/§36)
    RepoAudit               <-> arena-repo-reality-audit-template.md     (v2 §6/§28, v1 §5/§28)
    ChangeImpactAnalysis    <-> arena-change-impact-analysis-template.md (v2 §36, v1 §35)
    FinalReport             <-> arena-final-report-template.md           (v2 §40, v1 §39/§40)

Design notes
------------
- Dataclasses, not Pydantic: keeps the package dependency-free and the
  validation logic explicit and inspectable in `validation.py`, rather than
  hidden behind a framework's model-validator machinery. This matters for a
  pack whose entire point is "make every rule explicit and auditable."
- Every record carries a ``pack_version`` field (v2 §0.1 / §16 self
  provenance requirement) and a ``provenance`` dict for the minimum
  provenance fields the pack requires (v2 §16 / v1 §15).
- Records are plain data containers; *why* a value is legal or not lives in
  ``validation.py`` so the two concerns (shape vs. rule) stay separated,
  mirroring the pack's own "observation vs interpretation" discipline.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from . import __pack_version__
from .vocab import (
    AuthorizationState,
    ClaimStatus,
    Confidence,
    Coverage,
    CounterexampleStage,
    DecisionStatus,
    DivergenceClass,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    ExtractionClass,
    WIKI_PAGE_TITLES,
    ImpactClass,
    LifecycleState,
    OverallStatus,
    PresenceClass,
    ResolutionStatus,
    TrustTier,
    VerificationGate,
    VerificationMethod,
    VerificationResult,
    WikiPageNumber,
    normalize_overall_status,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_provenance() -> dict[str, Any]:
    """Minimum provenance skeleton per v2 §16 / v1 §15.

    Field order and membership deliberately mirror §16's literal list
    verbatim: source, source_type, repository, branch, commit, path,
    location, extraction_method, timestamp, classification, confidence,
    related_items, pack_version (§0.1, new in v2). ``classification`` was
    added by conformance-audit Recommendation R12 -- it was previously
    missing entirely (a genuine spec-vs-implementation gap, not merely an
    untested one): the sibling top-level ``evidence_class`` field on
    ``KnowledgeUnit``/``WorkItem`` records the record's *own* classification,
    but §16 additionally asks the *provenance block itself* to carry a
    classification value (e.g. for a provenance entry attached to a node
    that isn't itself a full record, such as a graph node/edge), which
    nothing previously populated. Defaults to ``None``, exactly like the
    other not-yet-supplied fields here, so adding this key cannot change
    the *meaning* of any provenance dict that predates this field --
    ``.get("classification")`` on an old, on-disk record simply returns
    ``None``, identical to how a freshly-constructed one starts out.
    """
    return {
        "source": None,
        "source_type": None,
        "repository": None,
        "branch": None,
        "commit": None,
        "path": None,
        "location": None,
        "extraction_method": None,
        "timestamp": _utcnow_iso(),
        "classification": None,
        "confidence": None,
        "related_items": [],
        "pack_version": __pack_version__,
    }



# ---------------------------------------------------------------------------
# Knowledge Unit
# ---------------------------------------------------------------------------


@dataclass
class KnowledgeUnit:
    """
    An atomic, classified knowledge item. v2 §7/§8/§16/§19/§29 (v1 §6/§7/§16/§19/§29).

    ``id`` should be of the form ``ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>``
    (see ``arena_agent.ids.new_generic_id``). Validity of shape/rules is
    checked by ``arena_agent.validation``, not enforced in ``__init__`` —
    this keeps constructing a record (even a knowingly-invalid one, e.g.
    while iteratively filling it in) always possible, while validation is
    an explicit, separate step before a unit is considered usable.

    ``authority_implications`` is free-text only -- see ``arena_agent``'s
    package docstring ("Scope: no Authority Contract enforcement") for the
    disclosed, deliberate scope boundary around v2 §11 (conformance audit
    Recommendation R7): this package never derives a capability from an
    authority or exercises one, so it has no authority-value
    representation or attenuation relation (``derive(A, C) ⪯ A``) to check
    this field against.
    """

    id: str
    meaning: str
    evidence_class: EvidenceClass
    confidence: Confidence
    source_location: str = ""
    extraction_class: Optional[ExtractionClass] = None
    scope: str = ""
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    forbidden_dependencies: list[str] = field(default_factory=list)
    trust_level: str = ""
    authority_implications: str = ""
    resource_implications: str = ""
    lifecycle_state: LifecycleState = LifecycleState.DISCOVERED
    invariants: list[str] = field(default_factory=list)
    positive_cases: list[str] = field(default_factory=list)
    negative_cases: list[str] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)
    verification_obligation: str = ""
    implementation_status: PresenceClass = PresenceClass.UNKNOWN
    evidence_state: EvidenceState = EvidenceState.MISSING
    open_decision_ids: list[str] = field(default_factory=list)
    related_items: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=_default_provenance)
    pack_version: str = __pack_version__


# ---------------------------------------------------------------------------
# Work Item
# ---------------------------------------------------------------------------


@dataclass
class LifecycleLogEntry:
    """
    One append-only entry in a Work Item's lifecycle log. v2 §27 Lifecycle
    Log. Stages are recorded, never overwritten (v2 §24.4 "no silent
    overwrites" / v1 "never silently rewrite history").
    """

    stage: WorkItemStage  # see vocab.WorkItemStage -- v2 §31 "Separate: PLAN, AUTHORIZATION, EXECUTION, OBSERVATION, VERIFICATION"
    timestamp: str = field(default_factory=_utcnow_iso)
    actor: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    """One row of the Verification Gates table. v2 §35 (v1 §38)."""

    gate: VerificationGate
    method: Optional[VerificationMethod] = None
    result: VerificationResult = VerificationResult.NOT_TESTED
    evidence: str = ""


@dataclass
class Ownership:
    """Work-item claim/ownership record. v2 §24.1 (new in v2)."""

    owner: Optional[str] = None
    claimed_at: Optional[str] = None
    status: ClaimStatus = ClaimStatus.RELEASED


@dataclass
class WorkItem:
    """
    An executable unit of work derived from one or more Knowledge Units.
    v2 §27 (v1 §27/§31).

    ``required_authority``/``forbidden_authority`` are free-text only --
    see ``arena_agent``'s package docstring ("Scope: no External Effect
    Contract") for the disclosed, deliberate scope boundary around v2
    §13: this package never invokes an external effect, so it has no
    Proposal->...->Verification pipeline object or durability-boundary
    check to attach to these fields (conformance audit Recommendation R8).
    The same two fields are also the closest concept in this record to v2
    §11's Authority Contract (conformance audit Recommendation R7) -- see
    ``arena_agent``'s package docstring ("Scope: no Authority Contract
    enforcement") for why this package has no authority-value
    representation or attenuation relation (``derive(A, C) ⪯ A``) to check
    these fields against.

    ``durable_state``/``journal``/``recovery_behavior``/
    ``indeterminate_states_reconciliation_path`` (conformance audit
    Recommendation R18, row 3.6) are likewise free-text only, mirroring
    ``required_authority``/``forbidden_authority``/``resource_budget``'s
    existing precedent exactly: no dedicated completeness check, no CLI
    wiring, additive fields only. They document the §27 "### Persistence"
    template section's narrative content; they do not themselves
    implement a journal, a recovery procedure, or
    ``ExecutionState.INDETERMINATE``/``RECONCILED`` reconciliation logic
    -- that behavior, if ever built, belongs to a separate recommendation
    (R10, Phase 6), not this one.
    """

    id: str
    title: str
    responsibility: str
    source_unit_ids: list[str] = field(default_factory=list)
    evidence_class: EvidenceClass = EvidenceClass.UNKNOWN
    confidence: Confidence = Confidence.NONE
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    required_authority: str = ""
    forbidden_authority: str = ""
    resource_budget: dict[str, Any] = field(default_factory=dict)
    upstream: list[str] = field(default_factory=list)
    downstream: list[str] = field(default_factory=list)
    forbidden_dependencies: list[str] = field(default_factory=list)
    lifecycle_state: LifecycleState = LifecycleState.DISCOVERED
    execution_state: ExecutionState = ExecutionState.PLANNED
    authorization_state: AuthorizationState = AuthorizationState.NOT_REQUESTED
    evidence_state: EvidenceState = EvidenceState.MISSING
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    failure_modes: list[dict[str, str]] = field(default_factory=list)
    ownership: Ownership = field(default_factory=Ownership)
    gates: list[GateResult] = field(default_factory=list)
    lifecycle_log: list[LifecycleLogEntry] = field(default_factory=list)
    open_decision_ids: list[str] = field(default_factory=list)
    # v2 §27 "### Persistence" template section (conformance audit
    # Recommendation R18, row 3.6): four free-text narrative sub-fields,
    # additive only -- follows the exact precedent already set by
    # required_authority/forbidden_authority/resource_budget (also
    # free-text §27 sections with no dedicated completeness check).
    # Deliberately NOT a structured/append-only log: unlike
    # `lifecycle_log` (a genuinely different, pre-existing concept), the
    # template's own "Journal" sub-field is a single narrative line, not
    # a list of entries. These fields document the persistence/recovery
    # situation; they do not themselves implement a journal, a recovery
    # procedure, or INDETERMINATE/RECONCILED reconciliation logic --
    # that behavior (if ever built) is Recommendation R10's scope
    # (Phase 6), not this one.
    durable_state: str = ""
    journal: str = ""
    recovery_behavior: str = ""
    indeterminate_states_reconciliation_path: str = ""
    provenance: dict[str, Any] = field(default_factory=_default_provenance)
    pack_version: str = __pack_version__

    def log(self, stage: "WorkItemStage | str", actor: str = "", **details: Any) -> LifecycleLogEntry:
        """Append a lifecycle log entry (never mutate/replace past entries)."""
        entry = LifecycleLogEntry(stage=stage, actor=actor, details=details)
        self.lifecycle_log.append(entry)
        return entry

    def gate_map(self) -> dict[VerificationGate, GateResult]:
        return {g.gate: g for g in self.gates}

    def missing_gates(self) -> list[VerificationGate]:
        """Gates from the full VerificationGate vocabulary not yet recorded."""
        present = {g.gate for g in self.gates}
        return [g for g in VerificationGate if g not in present]


# ---------------------------------------------------------------------------
# Decision Record
# ---------------------------------------------------------------------------


@dataclass
class InterpretationOption:
    option_id: str
    description: str
    consequences: str = ""


@dataclass
class DecisionRecord:
    """
    Ambiguity/conflict record. v2 §23/§26.2 (v1 §24/§25).

    ``required_authority`` is free-text only -- see ``arena_agent``'s
    package docstring ("Scope: no Authority Contract enforcement") for the
    disclosed, deliberate scope boundary around v2 §11 (conformance audit
    Recommendation R7): this package never derives a capability from an
    authority or exercises one, so it has no authority-value
    representation or attenuation relation (``derive(A, C) ⪯ A``) to check
    this field against.

    ``decided_by_trust_tier`` (conformance audit Recommendation R1, row
    1.5) records which v2 §3 Trust Model tier ``decided_by`` occupies --
    ``TrustTier.HUMAN_GOVERNANCE`` / ``ARENA_SUPERVISOR`` / ``ARENA_AGENT``
    -- so that a Stop Condition override (§26.2's mandatory "authorizing
    party and their role in the trust hierarchy") can actually be checked
    against who is permitted to lift one, not merely *that* someone did.
    Scope, deliberately narrow: this field is validated only in relation
    to ``overrides_stop_condition`` (required, and ``ARENA_AGENT`` is
    rejected, when an override is present -- see
    ``validate_decision_record``); a non-override decision may set or
    omit it freely, with no finding either way -- it carries no validation
    obligation outside the override context. ``raised_by``,
    ``Ownership.owner``, and ``WorkItem``'s authorization CLI option are
    untouched: §3/§26.2 make no attribution claim about those, so
    generalizing ``TrustTier`` onto them would add scope §3 does not ask
    for. ``TrustTier`` is a closed-set actor-identity classification only
    -- it carries no ordering, magnitude, or "stronger than" relation, and
    must never be treated as a stand-in for the v2 §11 Authority
    Contract's attenuation algebra (see R7's disclosure above): "which
    hierarchy position issued this decision" and "how much authority a
    value carries" are different questions.
    """

    id: str
    question: str
    conflicting_statements: list[dict[str, str]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    related_unit_ids: list[str] = field(default_factory=list)
    related_work_item_ids: list[str] = field(default_factory=list)
    options: list[InterpretationOption] = field(default_factory=list)
    consequences: str = ""
    required_authority: str = ""
    status: DecisionStatus = DecisionStatus.OPEN
    chosen_option_id: Optional[str] = None
    decided_by: Optional[str] = None
    decided_by_trust_tier: Optional[TrustTier] = None
    decided_at: Optional[str] = None
    rationale: str = ""
    decision_provenance: str = ""
    # v2 §26.2 Authorized Override Protocol fields (new in v2; optional,
    # only populated when this decision exists specifically to authorize
    # an override of a Stop Condition).
    overrides_stop_condition: Optional[int] = None
    override_scope: str = ""
    override_residual_risk: str = ""
    supersedes_decision_id: Optional[str] = None
    raised_by: str = ""
    raised_at: str = field(default_factory=_utcnow_iso)
    pack_version: str = __pack_version__


# ---------------------------------------------------------------------------
# Unified Counterexample Object (v2 §22 — consolidates v1 §22/§23/§36)
# ---------------------------------------------------------------------------


@dataclass
class MinimizationRecord:
    """Stage-4 fields. v2 §22.4."""

    original_case: Any = None
    minimized_case: Any = None
    removed_structure: str = ""
    preserved_invariant: str = ""
    checklist: dict[str, bool] = field(
        default_factory=lambda: {
            "authority_condition_preserved": False,
            "resource_boundary_preserved": False,
            "state_transition_preserved": False,
            "persistence_condition_preserved": False,
            "scheduler_ordering_preserved": False,
            "effect_lifecycle_preserved": False,
            "first_divergence_unchanged": False,
        }
    )

    def all_preserved(self) -> bool:
        return all(self.checklist.values())


@dataclass
class CounterexampleRecord:
    """
    Unified failure/counterexample object, v2 §22. Moves through
    RAW_DIVERGENCE -> OBSERVED_FAILURE -> REPRODUCIBLE_DEFECT ->
    MINIMIZED_REPRODUCER, with each stage's field set a superset of the
    last. ``stage`` IS the record's status (v2 §22.5) — there is
    deliberately no separate status field to drift out of sync with
    populated fields.
    """

    id: str
    stage: CounterexampleStage = CounterexampleStage.RAW_DIVERGENCE

    # Stage 1: RAW-DIVERGENCE
    input: Any = None
    seed: Optional[str] = None
    generator_version: Optional[str] = None
    production_trace: Any = None
    reference_trace: Any = None
    normalized_observations: dict[str, Any] = field(default_factory=dict)
    first_divergence: str = ""
    divergence_classification: Optional[DivergenceClass] = None

    # Stage 2: OBSERVED-FAILURE
    identity: str = ""
    source_revision: str = ""
    environment: str = ""
    execution_trace: Any = None
    observations: dict[str, Any] = field(default_factory=dict)
    expected_behavior: str = ""
    actual_behavior: str = ""

    # Stage 3: REPRODUCIBLE-DEFECT
    reproduction_command: Optional[str] = None
    confirmed: bool = False

    # Stage 4: MINIMIZED-REPRODUCER
    minimization: Optional[MinimizationRecord] = None

    related_work_item_ids: list[str] = field(default_factory=list)
    related_unit_ids: list[str] = field(default_factory=list)
    related_decision_ids: list[str] = field(default_factory=list)
    resolution_status: ResolutionStatus = ResolutionStatus.OPEN
    fix_reference: str = ""
    provenance: dict[str, Any] = field(default_factory=_default_provenance)
    pack_version: str = __pack_version__


# ---------------------------------------------------------------------------
# Repository Reality Audit
# ---------------------------------------------------------------------------


@dataclass
class InventoryItem:
    """
    One row of a repo-audit inventory table. v2 §6/§6.1/§28.

    Scope limit (conformance audit Recommendation R4, row 1.14, permanent
    -- not something a future check can close): v2 §6.1 requires that a
    ``SAMPLED`` coverage tag "MUST NOT be used to justify a `PRESENT` or
    `ABSENT` classification for anything not actually inspected." That
    rule is about a real-world fact -- was *this specific item* actually
    inspected -- which no validator operating over persisted strings can
    independently establish. ``evidence`` being non-empty and
    ``coverage_method`` being populated (enforced by
    ``validate_repo_audit``'s ``PRESENT_WITHOUT_EVIDENCE`` /
    ``SAMPLED_WITHOUT_METHOD`` checks) are necessary, not sufficient,
    conditions for §6.1 compliance -- the same "necessary, not sufficient"
    boundary already disclosed for repository-evidence claims generally
    (conformance matrix row 1.13). A mechanical proxy (e.g. flagging
    duplicate ``evidence`` strings across items, or ``evidence`` that
    merely repeats ``coverage_method``) was considered and deliberately
    rejected: two SAMPLED items can legitimately share identical, true
    evidence text, and two items can have superficially distinct evidence
    that is equally uninspected -- either heuristic would create false
    confidence that §6.1's actual inspection requirement was verified,
    when only string distinctness was. This is disclosed here as a
    permanent verification boundary rather than closed with an invented
    check.
    """

    path: str
    kind: str  # e.g. "file", "dir", "module", "test", "workflow", "artifact", "doc"
    classification: PresenceClass = PresenceClass.UNKNOWN
    coverage: Coverage = Coverage.EXHAUSTIVE
    coverage_method: str = ""
    evidence: str = ""
    notes: str = ""



@dataclass
class RepoAudit:
    """Repository Reality Audit report. v2 §6/§6.1/§6.2/§28 (v1 §5/§28)."""

    id: str
    repository: str
    branch_requested: Optional[str] = None
    branch_inspected: Optional[str] = None
    commit: Optional[str] = None  # None/"UNKNOWN" per v2 §6.2 fallback
    commit_identity_known: bool = True
    identity_failure_reason: str = ""
    working_tree_clean: Optional[bool] = None
    auditor: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)
    inventory: list[InventoryItem] = field(default_factory=list)
    claimed_vs_observed: list[dict[str, str]] = field(default_factory=list)
    evidence_gaps: list[dict[str, str]] = field(default_factory=list)
    contradictions: list[dict[str, str]] = field(default_factory=list)
    recommended_next_inspection: str = ""
    repository_modified: bool = False  # MUST remain False (v2 §28: "Do not modify the repository")
    pack_version: str = __pack_version__

    def by_classification(self, cls: PresenceClass) -> list[InventoryItem]:
        return [i for i in self.inventory if i.classification == cls]


# ---------------------------------------------------------------------------
# Change-Impact Analysis
# ---------------------------------------------------------------------------


CHANGE_IMPACT_CATEGORIES: tuple[str, ...] = (
    "direct_dependents",
    "indirect_dependents",
    "invariants",
    "state_transitions",
    "authority_paths",
    "resource_accounting",
    "persistence_recovery",
    "serialization_compatibility",
    "tests",
    "reference_model",
    "differential_expectations",
    "documentation",
)


@dataclass
class ImpactCategoryResult:
    category: str
    classification: ImpactClass = ImpactClass.NONE
    details: str = ""
    evidence: str = ""


@dataclass
class ChangeImpactAnalysis:
    """Change-Impact Analysis. v2 §36 (v1 §35)."""

    id: str
    target_unit_id: str
    change_description: str = ""
    proposed_by: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)
    baseline_commit: Optional[str] = None
    categories: dict[str, ImpactCategoryResult] = field(
        default_factory=lambda: {
            cat: ImpactCategoryResult(category=cat) for cat in CHANGE_IMPACT_CATEGORIES
        }
    )
    open_decision_ids: list[str] = field(default_factory=list)
    approved: Optional[bool] = None
    approval_conditions: str = ""
    approved_by: Optional[str] = None
    pack_version: str = __pack_version__

    def unassessed_categories(self) -> list[str]:
        """Categories still at their default, unassessed state."""
        return [
            cat
            for cat, result in self.categories.items()
            if not result.details and not result.evidence
        ]

    def high_risk_categories(self) -> list[str]:
        risky = {
            ImpactClass.SEMANTIC,
            ImpactClass.SECURITY,
            ImpactClass.PERSISTENCE,
            ImpactClass.COMPATIBILITY,
        }
        return [cat for cat, result in self.categories.items() if result.classification in risky]


# ---------------------------------------------------------------------------
# Final Report
# ---------------------------------------------------------------------------


#: Core Arena Principle self-check, v2 §43 (non-normative summary --
#: see §0.4/§2 -- but still a concrete, checkable list the pack itself
#: gives, so it's modeled as real per-item data rather than left as a
#: static markdown checklist baked into the template only).
CORE_ARENA_PRINCIPLE_CHECKS: tuple[str, ...] = (
    "no_claim_without_provenance",
    "no_action_without_authority",
    "no_effect_without_authorization",
    "no_completion_without_observation",
    "no_verification_without_evidence",
    "no_semantic_change_without_a_decision",
    "no_implementation_claim_without_repository_proof",
    "no_recovery_claim_without_causal_state",
    "no_override_without_attribution",  # new in v2, §26.2
    "no_coordination_without_ownership",  # new in v2, §24
)


@dataclass
class FinalReport:
    """Arena Result / Final Report. v2 §39/§40 (v1 §39/§40)."""

    id: str
    repository: str = ""
    branch: str = ""
    commit: str = ""
    source: str = ""
    scope: str = ""
    related_audit_ids: list[str] = field(default_factory=list)
    related_work_item_ids: list[str] = field(default_factory=list)
    # Decision Records this report is accounting for (v2 §26.2/§39/§40;
    # Phase 5B Recommendation R17). Distinct from open_decision_ids (which
    # means "still OPEN, caps overall_status") and blocking_decision_id
    # (singular, only meaningful when overall_status == BLOCKED): a
    # *resolved* override decision -- the pack's own worked example, Stop
    # Condition 2 overridden so the operation can proceed to COMPLETE --
    # belongs in neither of those. This field lets a report self-declare
    # which decisions (including resolved overrides) it is accounting for,
    # mirroring the existing related_audit_ids/related_work_item_ids
    # pattern exactly, so validate_final_report has something concrete to
    # check stop_conditions_triggered against instead of nothing at all.
    related_decision_ids: list[str] = field(default_factory=list)
    objective: str = ""
    observed: str = ""
    inferred: str = ""
    changed: str = ""
    not_changed: str = ""
    knowledge_units: list[dict[str, str]] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    execution: list[dict[str, str]] = field(default_factory=list)
    verification_summary: str = ""
    failures: list[str] = field(default_factory=list)  # CounterexampleRecord ids
    stop_conditions_triggered: list[dict[str, Any]] = field(default_factory=list)
    open_decision_ids: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)
    # v2 §4.1 Ingested Content Contract (conformance audit Recommendation
    # R2, row 1.8): "If ingested content appears to instruct the agent
    # directly, this MUST be logged as an anomaly ... and reported in the
    # Final Report ... it is evidence about the source, not license to
    # act on it." Structured (list[dict[str, str]]) rather than flattened
    # prose, matching the knowledge_units/invariants/execution table-row
    # precedent -- preserves content_scan.ContentFlag's kind/matched_text/
    # context distinctly rather than collapsing them into one opaque
    # string. Deliberately never auto-populated: attachment is always an
    # explicit caller action (see cli.py's `scan-content --attach-to-report`),
    # never a side effect of merely running a scan, and an empty list
    # here never implies "scan not performed" or any other coverage claim
    # -- this model has no field linking a FinalReport to which source
    # content it claims to have scanned. Each entry is evidence about the
    # source, never itself a verification conclusion, a defect, or a
    # `failures` entry (v2 §4 Fundamental Separations, observation vs.
    # inference) -- populating this field must never affect
    # `overall_status` or `failures`.
    content_scan_anomalies: list[dict[str, str]] = field(default_factory=list)
    recommended_next_action: str = ""
    # Completion Contract checklist, v2 §39 (v1 §39). All must be True for
    # `overall_status` to legitimately be COMPLETE / COMPLETE-WITH-WARNINGS
    # -- see validate_final_report / derive_overall_status_ceiling.
    completion_checklist: dict[str, bool] = field(
        default_factory=lambda: {
            "scope_known": False,
            "source_identified": False,
            "repository_state_identified": False,
            "work_performed": False,
            "observed_result_captured": False,
            "invariants_checked": False,
            "evidence_recorded": False,
            "failures_classified": False,
            "open_ambiguities_recorded": False,
            "final_status_assigned": False,
        }
    )
    # Core Arena Principle self-check (v2 §43) -- see CORE_ARENA_PRINCIPLE_CHECKS.
    # Unlike completion_checklist this is advisory (§43 is explicitly marked
    # non-normative), so it is reported but does not by itself gate status.
    core_principle_checklist: dict[str, bool] = field(
        default_factory=lambda: {k: False for k in CORE_ARENA_PRINCIPLE_CHECKS}
    )
    overall_status: OverallStatus = OverallStatus.BLOCKED
    # Required substantiation when overall_status == BLOCKED (see
    # validate_final_report's UNJUSTIFIED_BLOCKED_STATUS check): a blocker
    # must point at *something* -- an open Decision Record, a triggered
    # Stop Condition already present in stop_conditions_triggered, or at
    # minimum a non-empty prose reason.
    blocking_reason: str = ""
    blocking_decision_id: Optional[str] = None
    timestamp: str = field(default_factory=_utcnow_iso)
    pack_version: str = __pack_version__

    def __post_init__(self) -> None:
        # Accept the legacy "PARTIAL" spelling (and any bare string) at
        # construction time so every FinalReport instance -- built by hand,
        # loaded from old JSON, or constructed by a test -- always holds a
        # real OverallStatus member from here on, rather than requiring
        # every call site to special-case the alias.
        self.overall_status = normalize_overall_status(self.overall_status)

    def __setattr__(self, name: str, value: Any) -> None:
        # Also normalize on every later assignment (report.overall_status =
        # "PARTIAL" / "complete" / OverallStatus.COMPLETE all end up as a
        # real OverallStatus member), not just at construction -- callers
        # commonly set this field directly after building the report rather
        # than re-constructing it.
        if name == "overall_status":
            value = normalize_overall_status(value)
        object.__setattr__(self, name, value)


@dataclass
class WikiChangeHistoryEntry:
    """
    One row of a WikiPage's change history (v2 §38 / Wiki Page template
    "Change History" table). Records what changed about the *page itself*
    -- narrative edits, references added/removed -- never a cached copy of
    a derived header, which must always be recomputed live from current
    records rather than snapshotted here (see WikiPage docstring).
    """

    timestamp: str = field(default_factory=_utcnow_iso)
    updated_by: str = ""
    change: str = ""
    is_semantic_change: bool = False
    related_decision_id: Optional[str] = None
    referenced_records_added: list[str] = field(default_factory=list)
    referenced_records_removed: list[str] = field(default_factory=list)


@dataclass
class WikiPage:
    """
    Arena Wiki page. v2 §19 (extraction contract) / §38 (Prompt: Arena Wiki
    Generator) / arena-wiki-page-template.md.

    This is an *authored projection* record, not a duplicate store of
    authoritative state: it persists only what is genuinely authored
    (narrative ``content``) or structurally assigned to the page
    (``page_number``, which records it references, dependencies, change
    history). It deliberately has NO fields for classification,
    implementation status, evidence status, or open-decision state --
    those are always derived live from the referenced KnowledgeUnit /
    DecisionRecord / RepoAudit / WorkItem records at render time (see
    ``validation.derive_wiki_header`` and ``reporting.render_wiki_page``),
    never cached here. Caching them here would let a wiki page assert a
    Knowledge Unit is IMPLEMENTED after the underlying unit reverts to
    PLANNED -- exactly the anti-pattern §38 exists to forbid ("never allow
    planned architecture to appear as implemented behavior").

    ``title`` is a read-only projection of ``page_number`` via
    ``WIKI_PAGE_TITLES`` -- it is not an independently stored/settable
    field, so a page number can never be paired with a title that
    contradicts the canonical §38 index.
    """

    id: str
    page_number: WikiPageNumber
    content: str = ""
    scope: str = ""
    source: str = ""
    repository_revision: str = ""
    knowledge_unit_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    work_item_ids: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # other WikiPage IDs
    last_updated: str = field(default_factory=_utcnow_iso)
    updated_by: str = ""
    change_history: list[WikiChangeHistoryEntry] = field(default_factory=list)
    pack_version: str = __pack_version__

    def __post_init__(self) -> None:
        if not isinstance(self.page_number, WikiPageNumber):
            self.page_number = WikiPageNumber(self.page_number)

    @property
    def title(self) -> str:
        return WIKI_PAGE_TITLES[self.page_number]


def to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass (and nested dataclasses/enums) to plain dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            result[f.name] = to_dict(getattr(obj, f.name))
        return result
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if hasattr(obj, "value") and hasattr(obj, "name") and not isinstance(obj, (str, int, float)):
        # Enum member
        return obj.value
    return obj
