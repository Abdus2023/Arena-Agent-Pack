"""
Rule enforcement for the Arena Agent pack.

This module is the difference between "a dataclass that happens to have a
field called evidence_class" and an actual implementation of the pack's
contracts. Every function here corresponds to a specific MUST/MUST NOT rule
and returns a list of ``Finding`` objects rather than raising on the first
problem — consistent with the pack's own instruction to *report* gaps and
violations rather than fail silently or fail totally opaquely (v2 §39
Completion Contract: failures must be *classified*, not just detected).

Nothing in this module invents evidence or resolves ambiguity on the
caller's behalf; it only checks whether the rules the pack states are
actually satisfied by the data it's given.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Iterable, Optional

from .graph import KnowledgeGraph
from .ids import InvalidArenaId, validate_generic_id
from .models import (
    ChangeImpactAnalysis,
    CounterexampleRecord,
    DecisionRecord,
    FinalReport,
    KnowledgeUnit,
    RepoAudit,
    WikiPage,
    WorkItem,
)
from .vocab import (
    CONFIDENCE_ORDER,
    COUNTEREXAMPLE_STAGE_ORDER,
    EXECUTION_TRANSITIONS,
    LIFECYCLE_FAILURE_BRANCHES,
    LIFECYCLE_HAPPY_PATH,
    MIN_CONFIDENCE_FOR_CLASS,
    STOP_CONDITIONS,
    AuthorizationState,
    ClaimStatus,
    Confidence,
    CounterexampleStage,
    DecisionStatus,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    LifecycleState,
    OverallStatus,
    PresenceClass,
    TrustTier,
    VerificationResult,
    WikiPageNumber,
    WorkItemStage,
    normalize_overall_status,
)


class Severity(str, Enum):
    ERROR = "ERROR"  # violates a MUST / MUST NOT — the pack requires a STOP (v2 §26.1)
    WARNING = "WARNING"  # violates a SHOULD, or is incomplete but not forbidden
    INFO = "INFO"


@dataclass
class Finding:
    severity: Severity
    code: str
    message: str
    ref: str = ""  # pack section reference, e.g. "v2 §5.1"

    def __str__(self) -> str:  # pragma: no cover - trivial
        tag = f"[{self.severity.value}] {self.code}"
        return f"{tag}: {self.message} ({self.ref})" if self.ref else f"{tag}: {self.message}"


def _confidence_ge(a: Confidence, b: Confidence) -> bool:
    return CONFIDENCE_ORDER.index(a) >= CONFIDENCE_ORDER.index(b)


# ---------------------------------------------------------------------------
# Knowledge Unit validation
# ---------------------------------------------------------------------------


def validate_knowledge_unit(unit: KnowledgeUnit) -> list[Finding]:
    findings: list[Finding] = []

    # v2 §19 / Knowledge Unit Table template: "every unit has exactly one
    # Extraction classification" -- this was previously untyped (a bare
    # Optional[str], no enum, not settable via CLI at all) so nothing could
    # actually be checked here; now that it's ExtractionClass-typed, flag
    # when it's still unset.
    if unit.extraction_class is None:
        findings.append(
            Finding(
                Severity.WARNING,
                "MISSING_EXTRACTION_CLASS",
                f"Unit {unit.id!r} has no extraction_class set. The Knowledge Unit Table "
                "contract (v2 §19) requires exactly one Wiki extraction category per unit.",
                "v2 §19",
            )
        )

    # v2 §5.1: confidence floor per evidence class.
    min_conf = MIN_CONFIDENCE_FOR_CLASS.get(unit.evidence_class)
    if min_conf is not None and not _confidence_ge(unit.confidence, min_conf):
        findings.append(
            Finding(
                Severity.ERROR,
                "CONFIDENCE_TOO_LOW_FOR_CLASS",
                f"Unit {unit.id!r} is classified {unit.evidence_class.value} but has "
                f"confidence {unit.confidence.value}; minimum required is "
                f"{min_conf.value}. Downgrade classification instead of keeping "
                f"weak confidence on a strong claim.",
                "v2 §5.1",
            )
        )

    # v2 §6 / v1 §5 Repository Reality Rule: IMPLEMENTED status requires a
    # repository-evidence trail, not just a classification label.
    if unit.implementation_status == PresenceClass.PRESENT and not unit.provenance.get(
        "commit"
    ):
        findings.append(
            Finding(
                Severity.ERROR,
                "IMPLEMENTED_WITHOUT_REPO_EVIDENCE",
                f"Unit {unit.id!r} claims implementation_status=PRESENT but has no "
                "commit-bound provenance. PRESENT must never be inferred from "
                "documentation alone.",
                "v2 §6 / v1 §5",
            )
        )

    if unit.evidence_class == EvidenceClass.CONFLICTING and not unit.open_decision_ids:
        findings.append(
            Finding(
                Severity.ERROR,
                "CONFLICTING_WITHOUT_DECISION_RECORD",
                f"Unit {unit.id!r} is classified CONFLICTING but has no linked "
                "decision record. Ambiguity must not be left unresolved-but-untracked.",
                "v2 §23 / v1 §24",
            )
        )

    if unit.evidence_class == EvidenceClass.UNKNOWN and unit.confidence != Confidence.NONE:
        findings.append(
            Finding(
                Severity.WARNING,
                "UNKNOWN_WITH_NONZERO_CONFIDENCE",
                f"Unit {unit.id!r} is classified UNKNOWN but confidence is "
                f"{unit.confidence.value}, not NONE. If there is enough evidence "
                "to be confident, UNKNOWN may be the wrong classification.",
                "v2 §5.1",
            )
        )

    for dep in unit.dependencies:
        if dep in unit.forbidden_dependencies:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "FORBIDDEN_DEPENDENCY_PRESENT",
                    f"Unit {unit.id!r} depends on {dep!r} which is also listed as "
                    "a forbidden dependency.",
                    "v2 §14 / v1 §17",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Lifecycle transition validation (v2 §9, unifies v1 §8/§9/§42)
# ---------------------------------------------------------------------------


def validate_lifecycle_transition(
    from_state: LifecycleState, to_state: LifecycleState
) -> list[Finding]:
    """
    Check that a proposed lifecycle transition is legal under the canonical
    model (v2 §9.1): forward-only on the happy path, or into the single
    failure branch reachable from the current state. No other transition
    (e.g. skipping a state, moving backward, or jumping to an unrelated
    failure branch) is permitted without being modeled as a new refinement
    (v2 §9.2) -- which this validator cannot see, so it flags it instead of
    guessing.
    """
    findings: list[Finding] = []

    if from_state == to_state:
        return findings  # no-op transition, always legal

    happy = LIFECYCLE_HAPPY_PATH
    if from_state in happy and to_state in happy:
        from_idx = happy.index(from_state)
        to_idx = happy.index(to_state)
        if to_idx <= from_idx:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "LIFECYCLE_BACKWARD_TRANSITION",
                    f"Transition {from_state.value} -> {to_state.value} moves "
                    "backward or sideways on the canonical happy path. If this is "
                    "a legitimate re-entry (e.g. re-classification), model it "
                    "explicitly rather than silently rewinding lifecycle_state.",
                    "v2 §9.1",
                )
            )
        elif to_idx - from_idx > 1:
            skipped = ", ".join(s.value for s in happy[from_idx + 1 : to_idx])
            findings.append(
                Finding(
                    Severity.ERROR,
                    "LIFECYCLE_SKIPPED_STATE",
                    f"Transition {from_state.value} -> {to_state.value} skips "
                    f"canonical state(s) [{skipped}] without recording them. "
                    "This is exactly the 'RUN_TASK -> DONE' compound-transition "
                    "anti-pattern: every constituent transition must be defined "
                    "and passed through explicitly, not jumped over.",
                    "v2 §9.3 Compound Transition Rule",
                )
            )
        return findings

    # Check failure-branch legality.
    expected_failure = LIFECYCLE_FAILURE_BRANCHES.get(from_state)
    if expected_failure is not None and to_state == expected_failure:
        return findings  # legal failure transition

    findings.append(
        Finding(
            Severity.ERROR,
            "LIFECYCLE_ILLEGAL_TRANSITION",
            f"Transition {from_state.value} -> {to_state.value} is not part of "
            "the canonical lifecycle model (happy path or its single defined "
            "failure branch). If this is a refined sub-state, declare the "
            "mapping per v2 §9.2 rather than using an unmapped transition.",
            "v2 §9.1 / §9.2",
        )
    )
    return findings


def validate_execution_transition(
    from_state: ExecutionState, to_state: ExecutionState
) -> list[Finding]:
    """
    Check that a proposed ExecutionState transition is legal under §15's
    own diagram (conformance audit Recommendation R10, row 2.2):

        PLANNED -> STARTED -> ISSUED -> COMPLETED
                                 |
                                 +-> FAILED
                                 |
                                 +-> INDETERMINATE -> RECONCILED

    Unlike ``validate_lifecycle_transition``'s single linear happy path,
    ExecutionState genuinely branches at ISSUED (three legal successors),
    so this checks against the closed transition graph in
    ``vocab.EXECUTION_TRANSITIONS`` rather than a single ordered sequence.

    The rule this exists to enforce is §15's explicit sentence: "Issued +
    no completion -> INDETERMINATE -> Authoritative reconciliation ->
    Resolved outcome" -- i.e. ``ISSUED -> RECONCILED`` directly, skipping
    ``INDETERMINATE``, is illegal. This is the same "RUN_TASK -> DONE"
    compound-transition anti-pattern already named for LifecycleState
    (§9.3), applied to this independent axis.

    Deliberately out of scope (disclosed gap, not an oversight -- see
    ``tests/test_execution_transition.py``'s module docstring): detecting
    that an ``ISSUED`` item has gone *stale* with no terminal follow-up at
    all. §15 states "missing completion evidence does not automatically
    mean 'not executed'" but defines no staleness threshold or policy for
    when a still-``ISSUED`` item should be treated as needing
    reconciliation ("unless the governing specification explicitly
    defines another semantics" -- it doesn't here). This function only
    checks the objectively stated transition-legality rule; it cannot and
    does not infer staleness from elapsed time or from lifecycle_state
    progression (e.g. reaching OBSERVED/VERIFIED), since either would
    invent a policy the pack does not itself establish.
    """
    findings: list[Finding] = []

    if from_state == to_state:
        return findings  # no-op transition, always legal

    legal_successors = EXECUTION_TRANSITIONS.get(from_state, ())
    if to_state in legal_successors:
        return findings

    if from_state == ExecutionState.ISSUED and to_state == ExecutionState.RECONCILED:
        findings.append(
            Finding(
                Severity.ERROR,
                "EXECUTION_STATE_SKIPPED_INDETERMINATE",
                f"Transition {from_state.value} -> {to_state.value} skips "
                "INDETERMINATE. v2 §15: 'Issued + no completion -> "
                "INDETERMINATE -> Authoritative reconciliation -> Resolved "
                "outcome' -- INDETERMINATE must be passed through and "
                "recorded explicitly, not jumped over, exactly like the "
                "§9.3 compound-transition rule already enforced for "
                "lifecycle_state.",
                "v2 §15",
            )
        )
        return findings

    findings.append(
        Finding(
            Severity.ERROR,
            "EXECUTION_STATE_ILLEGAL_TRANSITION",
            f"Transition {from_state.value} -> {to_state.value} is not part "
            "of the canonical execution-state model (v2 §15): PLANNED -> "
            "STARTED -> ISSUED, then ISSUED -> COMPLETED / FAILED / "
            "INDETERMINATE -> RECONCILED. No other transition is defined.",
            "v2 §15",
        )
    )
    return findings


# ---------------------------------------------------------------------------
# Work Item validation
# ---------------------------------------------------------------------------


def validate_work_item(item: WorkItem) -> list[Finding]:
    findings: list[Finding] = []

    # v2 §35.3: every gate must be assigned a result; none silently omitted.
    missing = item.missing_gates()
    if missing:
        findings.append(
            Finding(
                Severity.WARNING,
                "VERIFICATION_GATES_INCOMPLETE",
                f"Work item {item.id!r} is missing {len(missing)} verification "
                f"gate(s): {', '.join(g.value for g in missing)}. Every gate must "
                "be assigned a result (PASS/FAIL/PARTIAL/.../NOT-APPLICABLE), "
                "never silently omitted.",
                "v2 §35.3 / v1 §38",
            )
        )

    # v2 §35.3: a PASS with no method or evidence is indistinguishable from
    # an unsubstantiated claim.
    for g in item.gates:
        if g.result == VerificationResult.PASS_ and not (g.method and g.evidence):
            findings.append(
                Finding(
                    Severity.ERROR,
                    "PASS_WITHOUT_EVIDENCE",
                    f"Work item {item.id!r} gate {g.gate.value!r} is marked PASS "
                    "but has no method and/or no evidence recorded.",
                    "v2 §35.3",
                )
            )

    # v2 §12 Action Contract / v2 §2 Core Contract: execution_state should
    # not silently be treated as complete without postconditions defined.
    if item.lifecycle_state == LifecycleState.VERIFIED and not item.postconditions:
        findings.append(
            Finding(
                Severity.WARNING,
                "VERIFIED_WITHOUT_POSTCONDITIONS",
                f"Work item {item.id!r} is VERIFIED but declares no "
                "postconditions -- there is nothing recorded that verification "
                "actually checked against.",
                "v2 §12",
            )
        )

    # v2 §24.1 Coordination Contract: an item mid-EXECUTING must have an owner.
    if item.lifecycle_state == LifecycleState.EXECUTING and not item.ownership.owner:
        findings.append(
            Finding(
                Severity.ERROR,
                "EXECUTING_WITHOUT_OWNER",
                f"Work item {item.id!r} is EXECUTING but has no recorded owner. "
                "An item must be claimed before execution so a second agent "
                "cannot silently duplicate the work.",
                "v2 §24.1",
            )
        )

    # v2 §9.1: lifecycle_state, execution_state, authorization_state, and
    # evidence_state are independent axes that "MUST be recorded
    # independently" -- reaching a lifecycle milestone without its
    # corresponding axis actually being updated is precisely the "single
    # generic status field" collapse the pack forbids, even though nothing
    # about the *lifecycle* transition itself is illegal.
    if item.lifecycle_state == LifecycleState.AUTHORIZED and item.authorization_state not in (
        AuthorizationState.GRANTED,
        AuthorizationState.ATTENUATED,
    ):
        findings.append(
            Finding(
                Severity.ERROR,
                "AUTHORIZED_WITHOUT_GRANTED_AUTHORIZATION_STATE",
                f"Work item {item.id!r} has lifecycle_state=AUTHORIZED but "
                f"authorization_state={item.authorization_state.value!r}. Reaching the "
                "AUTHORIZED lifecycle milestone requires authorization_state to "
                "independently reflect GRANTED (or ATTENUATED) -- use "
                "`work authorize` to record it, don't rely on lifecycle_state alone.",
                "v2 §9.1",
            )
        )

    if item.lifecycle_state in (
        LifecycleState.EXECUTING,
        LifecycleState.OBSERVED,
        LifecycleState.VERIFIED,
    ) and item.execution_state == ExecutionState.PLANNED:
        findings.append(
            Finding(
                Severity.WARNING,
                "EXECUTING_WITHOUT_EXECUTION_STATE_UPDATE",
                f"Work item {item.id!r} has lifecycle_state={item.lifecycle_state.value} "
                "but execution_state is still the default PLANNED. These are independent "
                "axes (v2 §9.1) -- use `work set-execution-state` to record the durable "
                "status of the issued action, not just the lifecycle milestone.",
                "v2 §9.1 / §14",
            )
        )

    if item.lifecycle_state == LifecycleState.VERIFIED and item.evidence_state != EvidenceState.VALIDATED:
        findings.append(
            Finding(
                Severity.ERROR,
                "VERIFIED_WITHOUT_SUFFICIENT_EVIDENCE_STATE",
                f"Work item {item.id!r} has lifecycle_state=VERIFIED but "
                f"evidence_state={item.evidence_state.value!r}. VERIFIED requires "
                "evidence_state=VALIDATED specifically -- CAPTURED means evidence was "
                "recorded but not yet checked against verification obligations, which is "
                "not sufficient. Use `work set-evidence-state` to record VALIDATED explicitly.",
                "v2 §9.1",
            )
        )

    # v2 §31 (Work Planner prompt): "Separate: PLAN, AUTHORIZATION,
    # EXECUTION, OBSERVATION, VERIFICATION" -- a closed 5-value set (see
    # vocab.WorkItemStage). LifecycleLogEntry.stage is a bare str/
    # WorkItemStage field (row 4.4, Recommendation R19): a hand-constructed
    # or JSON-round-tripped entry with a typo'd or unrelated stage value
    # (e.g. "excecution", "Execution", "cleanup") previously passed
    # validation with no finding at all. Checked here, not at
    # LifecycleLogEntry construction, for the same reason WikiPage's
    # page_number gets the analogous defensive re-check in
    # validate_wiki_page_local rather than only trusting __post_init__:
    # this function must not assume every LifecycleLogEntry it sees was
    # actually built through WorkItem.log() rather than loaded/hand-built.
    for log_entry in item.lifecycle_log:
        try:
            WorkItemStage(log_entry.stage)
        except ValueError:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "INVALID_LIFECYCLE_LOG_STAGE",
                    f"Work item {item.id!r} has a lifecycle_log entry with "
                    f"stage={log_entry.stage!r}, which is not one of the 5 "
                    "stages v2 §31 requires this separation to cover: "
                    "plan, authorization, execution, observation, "
                    "verification. An unrecognized stage value (e.g. a "
                    "typo) is indistinguishable from a real 6th stage "
                    "unless it is rejected explicitly.",
                    "v2 §31",
                )
            )

    # v1 §12 / v2 §12: "not complete merely because the tool returned
    # successfully" -- completion requires lifecycle_log evidence of the
    # observation/verification stages, not just a final state flag.
    if item.lifecycle_state == LifecycleState.VERIFIED:
        stages_logged = {entry.stage for entry in item.lifecycle_log}
        for required_stage in ("execution", "observation", "verification"):
            if required_stage not in stages_logged:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "VERIFIED_WITHOUT_LIFECYCLE_LOG",
                        f"Work item {item.id!r} is VERIFIED but its lifecycle log "
                        f"has no {required_stage!r} entry. A final state without "
                        "a corresponding log entry is an unsubstantiated claim.",
                        "v2 §27 Lifecycle Log / Core Contract §2",
                    )
                )

    findings.extend(
        Finding(f.severity, f.code, f"[{item.id}] {f.message}", f.ref)
        for f in _validate_resource_budget(item)
    )

    return findings


def _validate_resource_budget(item: WorkItem) -> list[Finding]:
    """
    v2 §10.1 resource conservation snapshot invariant:
        initial_total = available(t) + reserved(t) + consumed(t)
    Checked only when the work item's resource_budget dict actually declares
    these keys -- this pack does not require resource accounting for every
    work item, only checks it when present (per §10: "any execution that
    consumes resources must identify them explicitly" -- if it wasn't
    identified, there is nothing to check here, and that omission itself is
    a separate, softer concern).
    """
    findings: list[Finding] = []
    budget = item.resource_budget
    if not budget:
        return findings

    for resource, snapshot in budget.items():
        if not isinstance(snapshot, dict):
            continue
        required_keys = {"initial_total", "available", "reserved", "consumed"}
        if not required_keys.issubset(snapshot.keys()):
            continue
        total = snapshot["available"] + snapshot["reserved"] + snapshot["consumed"]
        if total != snapshot["initial_total"]:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "RESOURCE_CONSERVATION_VIOLATED",
                    f"resource {resource!r}: available+reserved+consumed "
                    f"({total}) != initial_total ({snapshot['initial_total']}). "
                    "Check for double refunds, resource teleportation, or "
                    "un-modeled release transitions.",
                    "v2 §10.1",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Claim expiry (v2 §24.1, conformance audit Recommendation R14)
# ---------------------------------------------------------------------------


def check_claim_expiry(
    item: WorkItem,
    max_age: timedelta,
    now: Optional[datetime] = None,
) -> list[Finding]:
    """
    v2 §24.1: "Claims expire per the governing operational policy (not
    fixed by this pack); an expired claim reverts the item to `PLANNED`
    and MUST record the original agent's partial evidence rather than
    discarding it."

    This is a PURE detection hook, matching every other ``check_*``/
    ``validate_*`` function in this module (``validate_lifecycle_transition``,
    ``validate_work_item``, etc.): it inspects ``item`` and returns
    ``Finding``s, it never mutates anything. It does NOT set
    ``item.ownership.status = ClaimStatus.EXPIRED``, does NOT change
    ``item.lifecycle_state``, and does NOT call (or attempt to bypass)
    ``validate_lifecycle_transition``.

    That last point is a deliberate, disclosed scope boundary, not an
    oversight (conformance matrix row 2.16, investigated and reconciled
    with the user before this function was written): §24.1 states an
    expired claim "reverts the item to `PLANNED`," but
    ``validate_lifecycle_transition`` already treats ``EXECUTING ->
    PLANNED`` as an ERROR-severity ``LIFECYCLE_BACKWARD_TRANSITION`` under
    §9.1's own canonical model -- ``PLANNED`` is not ``EXECUTING``'s
    defined failure branch (``CRASHED`` is). The pack itself never
    reconciles §24.1 against its own §9.1 backward-transition rule. This
    implementation does not silently decide that one of those two
    sections overrides the other: it reports that a claim has expired,
    per the caller's own policy, and leaves applying the actual
    consequence -- including whatever lifecycle transition the caller's
    governing operational policy actually requires, and preserving the
    original agent's partial evidence -- as an explicit, caller-controlled
    operation. This mirrors this module's other pure-check/explicit-mutate
    separation (e.g. ``cli.py``'s ``work set-state`` command calls
    ``validate_lifecycle_transition`` first and only mutates after
    checking).

    ``max_age`` is the caller-supplied expiry policy (v2 §24.1: "not
    fixed by this pack") -- a ``timedelta``, the smallest interface that
    honors "policy not fixed by this pack" without over-generalizing into
    an opaque callable predicate. ``now`` is evaluation-time context, not
    policy, and is a separate, optional parameter (defaulting to the real
    current time) so callers can pass a fixed clock for deterministic
    tests.

    Boundary semantics: ``age <= max_age`` is not expired; ``age >
    max_age`` is expired.

    Only an ``ACTIVE`` claim can be expired -- a ``RELEASED`` claim is not
    held by anyone, and an already-``EXPIRED`` claim is not re-flagged (no
    duplicate finding, no invented second expiry). An ``ACTIVE`` claim
    with no (or an unparsable) ``claimed_at`` timestamp is reported as its
    own distinct, differently-coded malformed-data problem -- never
    silently treated as expired (which would invent an expiry decision
    the policy was never actually asked to make) and never silently
    treated as not-expired (which would hide a real data problem).

    This function does not reference ``ExecutionState.INDETERMINATE``/
    ``RECONCILED`` anywhere -- that reconciliation *behavior* is
    Recommendation R10's separate, untouched territory (Phase 6, the next
    item after R14), not this one.
    """
    findings: list[Finding] = []
    ownership = item.ownership

    if ownership.status != ClaimStatus.ACTIVE:
        return findings  # nothing to expire: unclaimed, released, or already expired

    if not ownership.claimed_at:
        findings.append(
            Finding(
                Severity.WARNING,
                "CLAIM_ACTIVE_WITHOUT_TIMESTAMP",
                f"Work item {item.id!r} has an ACTIVE claim by "
                f"{ownership.owner!r} with no claimed_at timestamp -- claim "
                "expiry cannot be evaluated against a policy without one.",
                "v2 §24.1",
            )
        )
        return findings

    try:
        claimed_at_dt = datetime.fromisoformat(ownership.claimed_at)
    except ValueError:
        findings.append(
            Finding(
                Severity.WARNING,
                "CLAIM_TIMESTAMP_UNPARSEABLE",
                f"Work item {item.id!r} has an ACTIVE claim by "
                f"{ownership.owner!r} whose claimed_at value "
                f"({ownership.claimed_at!r}) is not a parseable ISO-8601 "
                "timestamp -- claim expiry cannot be evaluated against it.",
                "v2 §24.1",
            )
        )
        return findings

    if now is None:
        now = datetime.now(timezone.utc)
    if claimed_at_dt.tzinfo is None:
        claimed_at_dt = claimed_at_dt.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age = now - claimed_at_dt
    if age > max_age:
        findings.append(
            Finding(
                Severity.WARNING,
                "CLAIM_EXPIRED",
                f"Work item {item.id!r}'s claim by {ownership.owner!r} "
                f"(claimed_at={ownership.claimed_at!r}) has been ACTIVE for "
                f"{age}, exceeding the supplied policy of {max_age}. v2 "
                "§24.1: an expired claim reverts the item to PLANNED and "
                "MUST record the original agent's partial evidence rather "
                "than discarding it -- applying that consequence is a "
                "separate, explicit, caller-controlled operation; this "
                "finding only reports that the policy's threshold was "
                "exceeded.",
                "v2 §24.1",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Decision Record validation
# ---------------------------------------------------------------------------


def validate_decision_record(
    decision: DecisionRecord,
    units: Optional[dict[str, KnowledgeUnit]] = None,
    work_items: Optional[dict[str, WorkItem]] = None,
) -> list[Finding]:
    """
    ``units``/``work_items`` (both optional; conformance audit
    Recommendation R16, v2 §26.2, row 3.4): ``{id: record}`` mappings the
    caller has already loaded for the records named by
    ``decision.related_unit_ids``/``related_work_item_ids``, mirroring
    ``validate_final_report``'s existing ``decisions`` mapping pattern
    exactly (a dict, not a bare iterable, specifically so this function can
    tell "not supplied" apart from "supplied but this ID isn't in it"). If
    a mapping is omitted (None), the corresponding dangling-reference check
    is skipped entirely -- silence, not a manufactured pass, consistent
    with every other optional cross-record check in this module.

    R16 disposition, locked with the user before implementation (see
    ``tests/test_validation.py``'s R16 test-block docstring for the full
    reasoning): §26.2 requires an override to be traceable to the record
    it affects. This function implements exactly two things:

    1. ``OVERRIDE_WITHOUT_LINKED_UNIT`` (WARNING): an override
       (``overrides_stop_condition`` set) that names no
       ``related_unit_ids``/``related_work_item_ids`` at all is not
       machine-auditable against any specific affected record. Matches the
       existing severity tier for adjacent §26.2 completeness gaps
       (``OVERRIDE_WITHOUT_SCOPE``/``OVERRIDE_WITHOUT_RESIDUAL_RISK``) --
       the override itself is still valid and attributed, just less
       traceable.
    2. ``RELATED_UNIT_NOT_FOUND``/``RELATED_WORK_ITEM_NOT_FOUND`` (ERROR,
       only when the corresponding mapping is supplied): a related ID that
       does not resolve is the same class of defect
       ``RELATED_DECISION_NOT_FOUND``/``WIKI_REFERENCE_NOT_FOUND`` already
       treat as ERROR elsewhere in this module. This check is
       unconditional on whether the decision is an override at all --
       ``related_unit_ids``/``related_work_item_ids`` are general-purpose
       fields, not override-only ones.

    Deliberately NOT implemented here (disclosed gap, not an oversight):
    detecting that a related unit's/work item's ``implementation_status``
    or ``evidence_class`` was *strengthened* by (i.e. causally as a result
    of) the override -- §26.2's own worked example ("overriding Stop
    Condition 2 ... does not make the component IMPLEMENTED"). Neither
    ``KnowledgeUnit.implementation_status``/``evidence_class`` nor
    ``WorkItem.evidence_class`` carry any history/snapshot to compare a
    "before the override" value against (unlike ``lifecycle_state``, which
    has ``lifecycle_log``), so no validator here can honestly distinguish
    "this classification was strengthened because of the override" from
    "this classification already had this value beforehand." Inferring
    strengthening from the *current* value alone (e.g. flagging
    ``overrides_stop_condition == 2`` alongside a related unit currently
    classified ``PRESENT``) was explicitly considered and rejected as an
    invented proxy that would assert a causal relationship the data cannot
    support -- the same class of shortcut already disclosed and rejected
    for a materially identical reason in ``InventoryItem``'s docstring
    (Recommendation R4, row 1.14).

    R1 disposition (conformance audit Recommendation R1, v2 §3 / §26.2,
    row 1.5), locked with the user before implementation: §26.2 requires
    an override to record "the authorizing party AND their role in the
    trust hierarchy" -- ``decided_by`` already covers the party;
    ``decided_by_trust_tier`` (``TrustTier``, optional field on
    ``DecisionRecord``) covers the role. This function implements exactly
    two things, scoped narrowly to the override context only:

    3. ``OVERRIDE_WITHOUT_TRUST_TIER`` (ERROR): an override with no
       ``decided_by_trust_tier`` recorded at all. Same severity tier as
       ``OVERRIDE_WITHOUT_ATTRIBUTION`` -- both are the two halves of
       §26.2's one "authorizing party and their role" bullet, not an
       ERROR/WARNING split within it.
    4. ``OVERRIDE_BY_AGENT_SELF`` (ERROR): an override whose
       ``decided_by_trust_tier`` is explicitly ``TrustTier.ARENA_AGENT``.
       Directly enforces §26.2's literal text: "A Stop Condition MUST NOT
       be lifted by the agent's own initiative." Checks the *declared*
       trust-tier classification, not string-matching ``decided_by``
       (free text is not a reliable place to detect self-authorization).

    A non-override decision has no trust-tier obligation: it may set or
    omit ``decided_by_trust_tier`` freely, with no finding either way --
    the field carries no validation meaning outside the override context
    (see ``DecisionRecord``'s docstring). ``raised_by``,
    ``Ownership.owner``, and ``WorkItem``'s authorization CLI option are
    deliberately untouched -- §3/§26.2 make no attribution claim about
    those, so generalizing ``TrustTier`` onto them would add scope §3
    does not ask for.

    ``TrustTier`` itself carries NO ordering, magnitude, or "stronger
    than" relation -- it is a closed-set actor-identity classification
    only, and must never be conflated with the v2 §11 Authority
    Contract's attenuation algebra (``derive(A, C) ⪯ A``), which this
    package deliberately does not implement (see the package docstring,
    "Scope: no Authority Contract enforcement", Recommendation R7).
    "Which hierarchy position issued this decision" and "how much
    authority a value carries" are different questions.
    """
    findings: list[Finding] = []

    if decision.status == DecisionStatus.RESOLVED:
        if decision.chosen_option_id is None:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "RESOLVED_WITHOUT_CHOICE",
                    f"Decision {decision.id!r} is RESOLVED but has no "
                    "chosen_option_id recorded.",
                    "v2 §23",
                )
            )
        elif decision.options and decision.chosen_option_id not in {
            o.option_id for o in decision.options
        }:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "RESOLVED_WITH_UNKNOWN_CHOICE",
                    f"Decision {decision.id!r} chosen_option_id "
                    f"{decision.chosen_option_id!r} does not match any listed option.",
                    "v2 §23",
                )
            )
        if not decision.decided_by:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "RESOLVED_WITHOUT_ATTRIBUTION",
                    f"Decision {decision.id!r} is RESOLVED but has no decided_by "
                    "attribution -- resolutions must be attributable to authority, "
                    "never silent.",
                    "v2 §23 / §26.2",
                )
            )

    if decision.overrides_stop_condition is not None:
        if not (1 <= decision.overrides_stop_condition <= 13):
            findings.append(
                Finding(
                    Severity.ERROR,
                    "INVALID_STOP_CONDITION_NUMBER",
                    f"Decision {decision.id!r} references stop condition "
                    f"#{decision.overrides_stop_condition}, but only 1-13 are "
                    "defined.",
                    "v2 §26.1",
                )
            )
        if not decision.decided_by:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "OVERRIDE_WITHOUT_ATTRIBUTION",
                    f"Decision {decision.id!r} overrides a Stop Condition but has "
                    "no attributed authorizing party. Overrides must always be "
                    "attributed (v2 §26.2).",
                    "v2 §26.2",
                )
            )
        if decision.decided_by_trust_tier is None:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "OVERRIDE_WITHOUT_TRUST_TIER",
                    f"Decision {decision.id!r} overrides a Stop Condition but does "
                    "not record decided_by_trust_tier. §26.2 requires the "
                    "authorizing party AND their role in the trust hierarchy (v2 "
                    "§3) -- decided_by covers the party, decided_by_trust_tier "
                    "covers the role; both halves of this one mandatory element "
                    "are required.",
                    "v2 §3 / §26.2",
                )
            )
        elif decision.decided_by_trust_tier == TrustTier.ARENA_AGENT:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "OVERRIDE_BY_AGENT_SELF",
                    f"Decision {decision.id!r} overrides a Stop Condition but "
                    "decided_by_trust_tier is ARENA_AGENT. v2 §26.2 states: 'A "
                    "Stop Condition MUST NOT be lifted by the agent's own "
                    "initiative.' Only HUMAN_GOVERNANCE or ARENA_SUPERVISOR may "
                    "authorize an override.",
                    "v2 §26.2",
                )
            )
        if not decision.override_scope:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "OVERRIDE_WITHOUT_SCOPE",
                    f"Decision {decision.id!r} overrides a Stop Condition but does "
                    "not declare an override_scope (this instance / this work item "
                    "/ standing policy).",
                    "v2 §26.2",
                )
            )
        if not decision.override_residual_risk:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "OVERRIDE_WITHOUT_RESIDUAL_RISK",
                    f"Decision {decision.id!r} overrides a Stop Condition but does not "
                    "record override_residual_risk. §26.2 requires the authorizing party "
                    "to explicitly state the residual risk being accepted -- this is one "
                    "of the four mandatory elements alongside the condition number, "
                    "authorizing party, and scope, not optional narrative.",
                    "v2 §26.2",
                )
            )
        if not decision.related_unit_ids and not decision.related_work_item_ids:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "OVERRIDE_WITHOUT_LINKED_UNIT",
                    f"Decision {decision.id!r} overrides a Stop Condition but names no "
                    "related_unit_ids or related_work_item_ids -- the override is not "
                    "traceable to any specific affected record. v2 §26.2 requires an "
                    "override to be auditable; an unlinked override remains observable "
                    "(it is still attributed, scoped, and risk-accepted) but its "
                    "operational scope cannot be directly established from this record "
                    "alone.",
                    "v2 §26.2",
                )
            )

    # v2 §26.2 / Recommendation R16: related_unit_ids/related_work_item_ids
    # are general-purpose fields (not override-only), so a dangling
    # reference is checked unconditionally, exactly like
    # validate_final_report's RELATED_DECISION_NOT_FOUND check -- only when
    # the corresponding mapping is actually supplied (silence otherwise).
    if units is not None:
        for uid in decision.related_unit_ids:
            if uid not in units:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "RELATED_UNIT_NOT_FOUND",
                        f"Decision {decision.id!r} references related unit {uid!r}, "
                        "which does not exist (or was not supplied for verification). "
                        "A decision must not point at a unit that isn't there -- the "
                        "same rule already applied to related decisions "
                        "(RELATED_DECISION_NOT_FOUND) and wiki references "
                        "(WIKI_REFERENCE_NOT_FOUND).",
                        "v2 §26.2",
                    )
                )

    if work_items is not None:
        for wid in decision.related_work_item_ids:
            if wid not in work_items:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "RELATED_WORK_ITEM_NOT_FOUND",
                        f"Decision {decision.id!r} references related work item "
                        f"{wid!r}, which does not exist (or was not supplied for "
                        "verification). A decision must not point at a work item "
                        "that isn't there -- the same rule already applied to related "
                        "decisions (RELATED_DECISION_NOT_FOUND) and wiki references "
                        "(WIKI_REFERENCE_NOT_FOUND).",
                        "v2 §26.2",
                    )
                )

    if decision.status == DecisionStatus.SUPERSEDED and not decision.supersedes_decision_id:
        findings.append(
            Finding(
                Severity.WARNING,
                "SUPERSEDED_WITHOUT_FORWARD_LINK",
                f"Decision {decision.id!r} is marked SUPERSEDED but does not "
                "record which decision superseded it via supersedes_decision_id "
                "on the *new* record -- verify the newer record links back.",
                "v2 §23 usage notes",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Counterexample staging validation (v2 §22)
# ---------------------------------------------------------------------------


def validate_counterexample_promotion(
    record: CounterexampleRecord, target_stage: CounterexampleStage
) -> list[Finding]:
    """
    Check whether ``record`` may be promoted from its current stage to
    ``target_stage``, per the promotion requirements in v2 §22.1-22.4.
    Returns findings; does not mutate the record. Caller applies the
    promotion only if there are no ERROR-severity findings.
    """
    findings: list[Finding] = []
    order = COUNTEREXAMPLE_STAGE_ORDER
    cur_idx = order.index(record.stage)
    tgt_idx = order.index(target_stage)

    if tgt_idx <= cur_idx:
        findings.append(
            Finding(
                Severity.ERROR,
                "COUNTEREXAMPLE_BACKWARD_PROMOTION",
                f"{record.id!r}: cannot 'promote' from {record.stage.value} to "
                f"{target_stage.value} -- stages only move forward.",
                "v2 §22.5",
            )
        )
        return findings

    if tgt_idx - cur_idx > 1:
        findings.append(
            Finding(
                Severity.WARNING,
                "COUNTEREXAMPLE_SKIPPED_STAGE",
                f"{record.id!r}: promoting from {record.stage.value} directly to "
                f"{target_stage.value} skips intermediate stage(s). Allowed, but "
                "ensure the intermediate fields were genuinely not applicable "
                "rather than simply skipped.",
                "v2 §22",
            )
        )

    if target_stage == CounterexampleStage.OBSERVED_FAILURE:
        if not record.expected_behavior or not record.actual_behavior:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "OBSERVED_FAILURE_MISSING_FIELDS",
                    f"{record.id!r}: promoting to OBSERVED-FAILURE requires "
                    "expected_behavior and actual_behavior to be populated.",
                    "v2 §22.2",
                )
            )

    if target_stage == CounterexampleStage.REPRODUCIBLE_DEFECT:
        if not record.reproduction_command:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "REPRODUCIBLE_DEFECT_NO_COMMAND",
                    f"{record.id!r}: promoting to REPRODUCIBLE-DEFECT requires a "
                    "reproduction_command.",
                    "v2 §22.3",
                )
            )
        if not record.confirmed:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "REPRODUCIBLE_DEFECT_NOT_CONFIRMED",
                    f"{record.id!r}: an OBSERVED-FAILURE is not automatically a "
                    "REPRODUCIBLE-DEFECT -- an independent re-run must confirm "
                    "the same first_divergence before promotion (set confirmed=True).",
                    "v2 §22.3",
                )
            )

    if target_stage == CounterexampleStage.MINIMIZED_REPRODUCER:
        if record.minimization is None or not record.minimization.all_preserved():
            findings.append(
                Finding(
                    Severity.ERROR,
                    "MINIMIZATION_CHECKLIST_INCOMPLETE",
                    f"{record.id!r}: promoting to MINIMIZED-REPRODUCER requires "
                    "the full minimization safety checklist to be satisfied "
                    "(authority condition, resource boundary, state transition, "
                    "persistence condition, scheduler ordering, effect lifecycle, "
                    "and unchanged first_divergence all preserved).",
                    "v2 §22.4",
                )
            )

    return findings


def promote_counterexample(
    record: CounterexampleRecord, target_stage: CounterexampleStage
) -> list[Finding]:
    """Validate and, if there are no ERRORs, actually promote the record's stage."""
    findings = validate_counterexample_promotion(record, target_stage)
    if not any(f.severity == Severity.ERROR for f in findings):
        record.stage = target_stage
    return findings


def validate_counterexample_record(record: CounterexampleRecord) -> list[Finding]:
    """
    Check that ``record`` is internally consistent *at its current stage*
    (v2 §22.1-22.4's required-field sets) -- unlike
    ``validate_counterexample_promotion``, which checks readiness to move
    *forward* to a different stage. This is what `ce validate`/`ce show`
    run: it catches a record whose stage was advanced (e.g. by hand-editing
    the JSON store) without the fields that stage requires ever having been
    populated, which promotion-time checks alone would not catch after the
    fact.
    """
    findings: list[Finding] = []

    if not record.first_divergence:
        findings.append(
            Finding(
                Severity.ERROR,
                "MISSING_FIRST_DIVERGENCE",
                f"{record.id!r}: first_divergence is required from Stage 1 "
                "(RAW-DIVERGENCE) onward and must never be blank.",
                "v2 §22.1",
            )
        )

    order = COUNTEREXAMPLE_STAGE_ORDER
    idx = order.index(record.stage)

    if idx >= order.index(CounterexampleStage.OBSERVED_FAILURE):
        if not record.expected_behavior or not record.actual_behavior:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "OBSERVED_FAILURE_MISSING_FIELDS",
                    f"{record.id!r}: stage {record.stage.value} requires "
                    "expected_behavior and actual_behavior to be populated "
                    "(required starting at OBSERVED-FAILURE).",
                    "v2 §22.2",
                )
            )

    if idx >= order.index(CounterexampleStage.REPRODUCIBLE_DEFECT):
        if not record.reproduction_command:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "REPRODUCIBLE_DEFECT_NO_COMMAND",
                    f"{record.id!r}: stage {record.stage.value} requires a "
                    "reproduction_command (required starting at REPRODUCIBLE-DEFECT).",
                    "v2 §22.3",
                )
            )
        if not record.confirmed:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "REPRODUCIBLE_DEFECT_NOT_CONFIRMED",
                    f"{record.id!r}: stage {record.stage.value} requires confirmed=True "
                    "-- an independent re-run must have reproduced the same "
                    "first_divergence.",
                    "v2 §22.3",
                )
            )

    if idx >= order.index(CounterexampleStage.MINIMIZED_REPRODUCER):
        if record.minimization is None or not record.minimization.all_preserved():
            findings.append(
                Finding(
                    Severity.ERROR,
                    "MINIMIZATION_CHECKLIST_INCOMPLETE",
                    f"{record.id!r}: stage MINIMIZED-REPRODUCER requires the full "
                    "minimization safety checklist to be satisfied.",
                    "v2 §22.4",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Repo Audit validation
# ---------------------------------------------------------------------------


def validate_repo_audit(audit: RepoAudit) -> list[Finding]:
    findings: list[Finding] = []

    if audit.repository_modified:
        findings.append(
            Finding(
                Severity.ERROR,
                "AUDIT_MODIFIED_REPOSITORY",
                f"Audit {audit.id!r} recorded repository_modified=True. A "
                "Repository Reality Audit must never modify the repository.",
                "v2 §28 / v1 §28",
            )
        )

    if not audit.commit_identity_known and not audit.identity_failure_reason:
        findings.append(
            Finding(
                Severity.WARNING,
                "UNKNOWN_IDENTITY_NO_REASON",
                f"Audit {audit.id!r} has commit_identity_known=False but no "
                "identity_failure_reason recorded.",
                "v2 §6.2",
            )
        )

    # Together, PRESENT_WITHOUT_EVIDENCE and SAMPLED_WITHOUT_METHOD enforce
    # the *shape* prerequisites §6.1 needs (evidence exists; sampling is
    # described) -- they are necessary, not sufficient, conditions for
    # §6.1's actual requirement, which is a real-world fact ("was this
    # specific item actually inspected?") that no validator over persisted
    # strings can independently establish. This is a permanent, disclosed
    # verification boundary (conformance audit Recommendation R4, row
    # 1.14), not a gap a future check can close -- see InventoryItem's
    # docstring for the full disclosure, including why a mechanical proxy
    # (e.g. flagging duplicate evidence strings) was considered and
    # rejected as producing false confidence rather than real verification.
    for item in audit.inventory:
        if item.classification == PresenceClass.PRESENT and not item.evidence:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "PRESENT_WITHOUT_EVIDENCE",
                    f"Audit {audit.id!r}: inventory item {item.path!r} is "
                    "classified PRESENT but has no evidence recorded.",
                    "v2 §6 / v1 §5",
                )
            )
        if item.coverage.value == "SAMPLED" and not item.coverage_method:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "SAMPLED_WITHOUT_METHOD",
                    f"Audit {audit.id!r}: inventory item {item.path!r} is tagged "
                    "SAMPLED coverage but does not describe the sampling method.",
                    "v2 §6.1",
                )
            )

    conflicting_items = audit.by_classification(PresenceClass.CONFLICTING)
    conflicting_paths = {i.path for i in conflicting_items}
    documented_paths = {c.get("path") or c.get("component", "") for c in audit.contradictions}
    undocumented = conflicting_paths - documented_paths
    if undocumented:
        findings.append(
            Finding(
                Severity.WARNING,
                "CONFLICTING_ITEMS_NOT_IN_CONTRADICTIONS_SECTION",
                f"Audit {audit.id!r}: {len(undocumented)} CONFLICTING inventory "
                "item(s) are not reflected in the contradictions section: "
                f"{sorted(undocumented)}",
                "v2 §28 return format",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Change-Impact Analysis validation
# ---------------------------------------------------------------------------


def validate_change_impact_analysis(
    analysis: ChangeImpactAnalysis,
    work_items: Optional[dict[str, WorkItem]] = None,
) -> list[Finding]:
    """
    ``work_items`` (optional): a ``{id: WorkItem}`` mapping the caller has
    already loaded, used only to check the §36 "flag conflict before
    proceeding" rule below (row 4.11, Recommendation R21) -- this function
    never touches storage itself. Mirrors ``validate_wiki_references``'s
    optional-mapping pattern: when the mapping is omitted (None), or when
    ``target_unit_id`` is not a key in it, no conflict finding is produced
    -- absence of evidence is not evidence of absence, so an unresolved
    target is silently skipped rather than treated as either a pass or a
    conflict.

    Scope note: §24.1 ("Ownership / Claiming") defines open claims only in
    terms of ``WorkItem.ownership`` -- ``KnowledgeUnit`` has no ownership
    field at all in this implementation. So this check can only ever fire
    when ``target_unit_id`` resolves to a ``WorkItem``; a Change-Impact
    Analysis targeting a Knowledge Unit currently has no ownership state
    to conflict with, which is a real, disclosed scope limit of this
    check, not a silent gap being ignored.
    """
    findings: list[Finding] = []

    if work_items is not None:
        target = work_items.get(analysis.target_unit_id)
        if (
            target is not None
            and target.ownership.status == ClaimStatus.ACTIVE
            and target.ownership.owner
            and target.ownership.owner != analysis.proposed_by
        ):
            findings.append(
                Finding(
                    Severity.WARNING,
                    "CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM",
                    f"Analysis {analysis.id!r} proposes a change to "
                    f"{analysis.target_unit_id!r}, which is actively claimed "
                    f"by {target.ownership.owner!r} -- a different agent than "
                    f"proposed_by={analysis.proposed_by!r}. v2 §24.1 permits "
                    "proposing a Change-Impact Analysis against a claimed "
                    "item, but v2 §36 requires the conflict to be flagged "
                    "before proceeding, not silently allowed.",
                    "v2 §36 / §24.1",
                )
            )

    unassessed = analysis.unassessed_categories()
    if unassessed:
        findings.append(
            Finding(
                Severity.ERROR,
                "IMPACT_CATEGORIES_UNASSESSED",
                f"Analysis {analysis.id!r} has unassessed categories: "
                f"{', '.join(unassessed)}. All 12 categories must be explicitly "
                "assessed -- use classification NONE with a stated reason if "
                "truly not applicable, never leave it blank.",
                "v2 §36",
            )
        )

    risky = analysis.high_risk_categories()
    if analysis.approved and risky:
        unmitigated = [
            cat
            for cat in risky
            if not analysis.categories[cat].details
            and not analysis.open_decision_ids
        ]
        if unmitigated:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "APPROVED_WITH_UNMITIGATED_RISK",
                    f"Analysis {analysis.id!r} is approved but high-risk "
                    f"categories {unmitigated} have no mitigation details and no "
                    "linked decision record.",
                    "v2 §36 Approval Gate",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Final Report / Completion Contract validation (v2 §39, v1 §39)
# ---------------------------------------------------------------------------


# Linear quality ordering for the three non-BLOCKED statuses only. BLOCKED
# is deliberately excluded -- it is an evidence-backed *condition*, not a
# lower point on this scale (see derive_overall_status_ceiling docstring).
_STATUS_RANK: dict[OverallStatus, int] = {
    OverallStatus.INCOMPLETE: 0,
    OverallStatus.COMPLETE_WITH_WARNINGS: 1,
    OverallStatus.COMPLETE: 2,
}


def derive_overall_status_ceiling(
    report: FinalReport, other_findings: Iterable[Finding] = ()
) -> OverallStatus:
    """
    Compute the highest status this report's evidence actually supports,
    independent of what it *claims*.

    Rule (v2 §39 Completion Contract, applied as a status-derivation rule
    rather than a pass/fail gate on COMPLETE alone):

    - Completion checklist incomplete             -> INCOMPLETE
    - Checklist complete, but ERROR findings exist -> INCOMPLETE
    - Checklist complete, no ERROR, but WARNINGs
      or evidence_gaps/open_decision_ids remain    -> COMPLETE-WITH-WARNINGS
    - Checklist complete, no ERROR, no WARNING,
      no evidence gaps, no open decisions          -> COMPLETE

    ``other_findings`` lets a caller fold in findings already computed
    elsewhere (e.g. from the units/work items/counterexamples the report
    references) without this function re-deriving them; it only looks at
    severities, so passing findings from unrelated records is harmless
    but pointless -- callers should pass findings that are actually
    material to *this* report's claims.

    BLOCKED is intentionally never returned by this function: whether a
    report is BLOCKED is not a ceiling implied by absence of evidence, it
    is a separate claim that itself needs its own substantiation check
    (see UNJUSTIFIED_BLOCKED_STATUS below).
    """
    if not all(report.completion_checklist.values()):
        return OverallStatus.INCOMPLETE

    combined = list(other_findings)
    if has_errors(combined):
        return OverallStatus.INCOMPLETE

    material_warning = (
        any(f.severity == Severity.WARNING for f in combined)
        or bool(report.evidence_gaps)
        or bool(report.open_decision_ids)
    )
    if material_warning:
        return OverallStatus.COMPLETE_WITH_WARNINGS

    return OverallStatus.COMPLETE


_BLOCKING_REASON_PLACEHOLDERS = {
    "tbd", "todo", "unknown", "blocked", "n/a", "na", "pending",
    "none", "x", "...", "?", "wip", "in progress", "later", "stuck",
}


def _is_meaningful_blocking_reason(text: str) -> bool:
    """
    Heuristic, not a semantic check -- this is free-text prose, so there is
    no way to machine-verify it is *true*. But "non-empty" alone accepts
    junk like "x" or "TBD" as if it were real provenance, which defeats the
    point of requiring a reason at all. This rejects the empty string, a
    small list of common non-answer placeholders (case/punctuation
    insensitive), and anything under ~15 characters (shorter than a
    minimally complete sentence fragment). It cannot confirm the reason is
    accurate, only that it isn't an obvious non-answer -- real
    substantiation for BLOCKED still means one of: this reason, a
    referenced OPEN Decision Record, or an unoverridden Stop Condition.
    """
    normalized = text.strip().strip(".!?").lower()
    if not normalized or normalized in _BLOCKING_REASON_PLACEHOLDERS:
        return False
    return len(normalized) >= 15


def validate_final_report(
    report: FinalReport,
    other_findings: Iterable[Finding] = (),
    blocking_decision: Optional[DecisionRecord] = None,
    decisions: Optional[dict[str, DecisionRecord]] = None,
) -> list[Finding]:
    """
    Validate a Final Report against the v2 §39 Completion Contract and the
    §43 Core Arena Principle's "no claim without provenance" rule as
    applied to the report's own overall_status claim.

    ``other_findings`` (optional): findings already computed for the
    records this report references (units/work items/counterexamples/
    decisions), folded into the COMPLETE/COMPLETE-WITH-WARNINGS ceiling
    derivation. If omitted, the ceiling is derived from this report's own
    fields only (evidence_gaps, open_decision_ids, completion_checklist).

    ``blocking_decision`` (optional): the actual DecisionRecord referenced
    by ``report.blocking_decision_id``, if the caller has loaded it (the
    CLI does this via the store; this module never touches storage
    itself -- persistence answers "does it exist", this function only
    answers "is what's claimed here actually demonstrated"). Only a
    decision with ``status == OPEN`` counts as substantiating BLOCKED --
    referencing an ID alone is a pointer, not a demonstrated blocker. If
    omitted while ``blocking_decision_id`` is set, that reference is
    treated as unverified (not automatically accepted, not automatically
    rejected) and BLOCKED must be substantiated some other way instead.

    ``decisions`` (optional; Phase 5B Recommendation R17, v2 §26.2): a
    ``{id: DecisionRecord}`` mapping for the records named by
    ``report.related_decision_ids``, if the caller has loaded them --
    mirrors ``validate_wiki_references``'s dict-mapping pattern exactly
    (a dict, not a bare iterable, specifically so this function can tell
    "not supplied" apart from "supplied but this ID isn't in it"). If
    ``decisions`` is omitted (None), ``related_decision_ids`` is not
    checked at all (silence, not a manufactured pass) -- consistent with
    every other optional cross-record check in this module. If supplied,
    two things are checked for every ID in ``report.related_decision_ids``:
    the ID must resolve in the mapping (``RELATED_DECISION_NOT_FOUND`` if
    not -- a report must not point at a decision that isn't there, the
    same rule ``validate_wiki_references`` already applies to WikiPage
    references), and for every resolved decision whose
    ``overrides_stop_condition`` is set, that same condition number must
    appear in ``report.stop_conditions_triggered``
    (``OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT`` if not) -- §26.2's
    explicit requirement that "the fact that a Stop Condition was
    triggered and then overridden MUST still appear in the Final Report...
    not a way to make the Stop invisible." Both are ERROR severity: §26.2
    states this with "MUST", and a dangling reference is the same class of
    defect ``WIKI_REFERENCE_NOT_FOUND`` already treats as ERROR elsewhere
    in this module.
    """
    findings: list[Finding] = []
    status = normalize_overall_status(report.overall_status)

    # v2 §26.1 defines a closed set of exactly 13 numbered Stop Conditions
    # (see vocab.STOP_CONDITIONS). DecisionRecord.overrides_stop_condition
    # is already range-checked against this closed set
    # (INVALID_STOP_CONDITION_NUMBER); stop_conditions_triggered is the
    # other place a Stop Condition number appears and, unlike the override
    # field, was not checked against the closed set at all -- an entry
    # could name a nonexistent condition (e.g. #14, or a non-integer) and
    # pass silently. This runs unconditionally (not just when
    # status == BLOCKED) because stop_conditions_triggered can legitimately
    # be non-empty on a report that is not itself BLOCKED (e.g. a condition
    # was triggered, then overridden, and the report went on to COMPLETE).
    for entry in report.stop_conditions_triggered:
        condition_number = entry.get("condition")
        if condition_number not in STOP_CONDITIONS:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "INVALID_STOP_CONDITION_NUMBER",
                    f"Report {report.id!r} lists a triggered Stop Condition "
                    f"entry with condition={condition_number!r}, but only "
                    f"1-13 are defined (v2 §26.1). stop_conditions_triggered "
                    "must reference the closed Stop Condition vocabulary, "
                    "the same as DecisionRecord.overrides_stop_condition.",
                    "v2 §26.1",
                )
            )

    # v2 §4.1 Ingested Content Contract (conformance audit Recommendation
    # R2, row 1.8): shape-only check, mirroring PRESENT_WITHOUT_EVIDENCE's
    # style -- confirms each attached anomaly entry actually carries the
    # "kind" a caller would need to distinguish an anti-pattern phrase
    # from a directive pattern. Runs unconditionally (not gated on
    # overall_status), matching INVALID_STOP_CONDITION_NUMBER above, since
    # content_scan_anomalies can be populated on a report regardless of
    # its status. Deliberately does NOT assert or imply that
    # content_scan_anomalies is complete/exhaustive coverage of everything
    # scannable -- nothing in this model links a FinalReport to which
    # source content it claims to cover, so no coverage claim would be
    # justified. An anomaly's mere presence is also never itself an
    # ERROR: §4.1 states it is "evidence about the source, not license to
    # act on it," not proof of a defect.
    for i, entry in enumerate(report.content_scan_anomalies):
        if not entry.get("kind"):
            findings.append(
                Finding(
                    Severity.WARNING,
                    "MALFORMED_CONTENT_SCAN_ANOMALY",
                    f"Report {report.id!r}: content_scan_anomalies[{i}] has no "
                    "'kind' field, so it cannot be distinguished as an "
                    "anti_pattern_phrase or a directive_pattern.",
                    "v2 §4.1",
                )
            )

    # v2 §26.2 (Phase 5B Recommendation R17, row 3.5): an overridden Stop
    # Condition MUST still appear in the Final Report -- an override is a
    # way to proceed past it accountably, never a way to make it invisible.
    # Only runs when the caller supplies the decisions mapping (see
    # docstring); reported condition numbers are compared as a set so a
    # report is free to record additional detail (e.g. an "overridden":
    # true/false flag) without affecting this check either way. This runs
    # unconditionally (not gated on overall_status), matching
    # INVALID_STOP_CONDITION_NUMBER above, because the pack's own worked
    # example is a report that proceeds to COMPLETE after an override, not
    # one that stays BLOCKED.
    if decisions is not None:
        reported_conditions = {
            entry.get("condition") for entry in report.stop_conditions_triggered
        }
        for decision_id in report.related_decision_ids:
            decision = decisions.get(decision_id)
            if decision is None:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "RELATED_DECISION_NOT_FOUND",
                        f"Report {report.id!r} references related decision "
                        f"{decision_id!r}, which does not exist (or was not "
                        "supplied for verification). A report must not point "
                        "at a decision that isn't there -- the same rule "
                        "validate_wiki_references already applies to WikiPage "
                        "references (WIKI_REFERENCE_NOT_FOUND).",
                        "v2 §26.2/§39",
                    )
                )
                continue
            condition_number = decision.overrides_stop_condition
            if condition_number is None:
                continue
            if condition_number not in reported_conditions:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT",
                        f"Report {report.id!r} relates to decision "
                        f"{decision.id!r}, which overrides Stop Condition "
                        f"#{condition_number}, but that condition does not "
                        "appear anywhere in stop_conditions_triggered. v2 "

                        "§26.2 requires an overridden Stop Condition to "
                        "still appear in the Final Report -- an override "
                        "changes what the agent may do next, it never makes "
                        "the trigger invisible.",
                        "v2 §26.2",
                    )
                )

    if status == OverallStatus.BLOCKED:
        substantiated = False

        if report.blocking_decision_id:
            if blocking_decision is None:
                findings.append(
                    Finding(
                        Severity.WARNING,
                        "BLOCKING_DECISION_NOT_VERIFIED",
                        f"Report {report.id!r} references blocking_decision_id="
                        f"{report.blocking_decision_id!r} but no DecisionRecord was "
                        "supplied to confirm it is actually OPEN. A referenced ID is "
                        "a pointer, not proof -- pass the loaded DecisionRecord to "
                        "validate_final_report to verify it.",
                        "v2 §39/§43",
                    )
                )
            elif blocking_decision.id != report.blocking_decision_id:
                findings.append(
                    Finding(
                        Severity.WARNING,
                        "BLOCKING_DECISION_ID_MISMATCH",
                        f"Report {report.id!r} has blocking_decision_id="
                        f"{report.blocking_decision_id!r} but the DecisionRecord "
                        f"supplied for verification is {blocking_decision.id!r}.",
                        "v2 §39/§43",
                    )
                )
            elif blocking_decision.status == DecisionStatus.OPEN:
                substantiated = True
            else:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "BLOCKING_DECISION_NOT_OPEN",
                        f"Report {report.id!r} claims BLOCKED on decision "
                        f"{report.blocking_decision_id!r}, but that decision's status "
                        f"is {blocking_decision.status.value}, not OPEN. A resolved or "
                        "superseded decision cannot still be an active blocker.",
                        "v2 §23/§39",
                    )
                )

        if not substantiated:
            for s in report.stop_conditions_triggered:
                if not s.get("overridden", False):
                    substantiated = True
                    break

        if not substantiated:
            if report.blocking_reason and _is_meaningful_blocking_reason(report.blocking_reason):
                substantiated = True
            elif report.blocking_reason and report.blocking_reason.strip():
                findings.append(
                    Finding(
                        Severity.WARNING,
                        "BLOCKING_REASON_NOT_MEANINGFUL",
                        f"Report {report.id!r} has a blocking_reason set "
                        f"({report.blocking_reason!r}) but it reads as a placeholder "
                        "or is too short to audit -- state what is actually blocking "
                        "progress, not just that something is.",
                        "v2 §39/§43",
                    )
                )

        if not substantiated:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "UNJUSTIFIED_BLOCKED_STATUS",
                    f"Report {report.id!r} claims overall_status=BLOCKED but "
                    "substantiates it with none of: a verified OPEN Decision Record "
                    "(blocking_decision_id + blocking_decision confirming OPEN), an "
                    "unoverridden triggered Stop Condition (stop_conditions_triggered), "
                    "or a meaningful, non-placeholder blocking_reason. BLOCKED asserts "
                    "something actively prevents completion; that assertion needs "
                    "provenance the same as any other claim (v2 §43).",
                    "v2 §39/§43",
                )
            )
        return findings

    all_checked = all(report.completion_checklist.values())
    ceiling = derive_overall_status_ceiling(report, other_findings)

    # Only an issue if the *claimed* status implies the checklist should be
    # complete (COMPLETE / COMPLETE-WITH-WARNINGS). Honestly claiming
    # INCOMPLETE while the checklist is genuinely incomplete is exactly the
    # correct, non-masquerading claim -- it must not itself be flagged.
    if not all_checked and status in (OverallStatus.COMPLETE, OverallStatus.COMPLETE_WITH_WARNINGS):
        unmet = [k for k, v in report.completion_checklist.items() if not v]
        findings.append(
            Finding(
                Severity.ERROR,
                "INCOMPLETE_COMPLETION_CHECKLIST",
                f"Report {report.id!r} claims overall_status={status.value} but "
                f"these Completion Contract items are unmet: {unmet}. Per v2 "
                "§39, a task is complete only when every checklist item is "
                "satisfied -- there is no partial-credit COMPLETE.",
                "v2 §39",
            )
        )

    if _STATUS_RANK.get(status, -1) > _STATUS_RANK.get(ceiling, -1):
        findings.append(
            Finding(
                Severity.ERROR,
                "STATUS_MASQUERADING",
                f"Report {report.id!r} claims overall_status={status.value} but "
                f"its demonstrated evidence supports at most {ceiling.value}. "
                "A report may claim no stronger status than its evidence "
                "permits -- requested/planned completion is not the same as "
                "demonstrated completion (v2 §39/§43).",
                "v2 §39/§43",
            )
        )

    if report.evidence_gaps:
        findings.append(
            Finding(
                Severity.INFO,
                "EVIDENCE_GAPS_RECORDED",
                f"Report {report.id!r} lists {len(report.evidence_gaps)} evidence "
                f"gap(s): {report.evidence_gaps}. These are folded into the "
                "COMPLETE-WITH-WARNINGS ceiling rather than blocking on their "
                "own -- see derive_overall_status_ceiling.",
                "v2 §39",
            )
        )

    if report.open_decision_ids:
        findings.append(
            Finding(
                Severity.WARNING,
                "OPEN_REQUIRED_DECISION",
                f"Report {report.id!r} lists {len(report.open_decision_ids)} still-open "
                f"decision(s): {report.open_decision_ids}. An open decision caps this "
                "report at COMPLETE-WITH-WARNINGS at best; resolve it (or supersede "
                "it) before claiming COMPLETE.",
                "v2 §23/§39",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Knowledge Graph validation (v2 §34)
# ---------------------------------------------------------------------------


def validate_knowledge_graph(graph: KnowledgeGraph) -> list[Finding]:
    """
    Post-hoc integrity/attention checks on a graph. Structural integrity
    (dangling edges, missing provenance) is already refused at add_node /
    add_edge time by graph.GraphIntegrityError, so those can't normally
    appear here -- this instead surfaces the two things the pack says must
    never be *silently* auto-resolved: contradictions and planned/observed
    divergences. Both are reported as findings, not errors, because a
    contradiction or an unimplemented planned node is not itself a defect
    in the graph -- it is exactly the kind of fact the graph exists to
    surface for a human/agent to resolve elsewhere (e.g. via a Decision
    Record). Silently having none of these findings surfaced would be the
    actual violation.
    """
    findings: list[Finding] = []

    contradictions = graph.contradictions()
    if contradictions:
        findings.append(
            Finding(
                Severity.WARNING,
                "GRAPH_HAS_CONTRADICTIONS",
                f"{len(contradictions)} 'contradicts' edge(s) present: "
                f"{[c.id for c in contradictions]}. Contradictions must be "
                "surfaced (e.g. via a Decision Record), not silently ignored "
                "or auto-resolved.",
                "v2 §34",
            )
        )

    divergences = graph.divergences()
    if divergences:
        findings.append(
            Finding(
                Severity.WARNING,
                "GRAPH_HAS_PLANNED_NOT_OBSERVED",
                f"{len(divergences)} planned node(s) have no corresponding "
                f"observed node with the same label: {[n.id for n, _ in divergences]}. "
                "This may be legitimate (not yet built) or may indicate a "
                "stale/abandoned plan -- do not assume either without evidence.",
                "v2 §34/§6/§9.4",
            )
        )

    derived_without_note = [e for e in graph.edges.values() if e.derived and not e.notes]
    if derived_without_note:
        findings.append(
            Finding(
                Severity.WARNING,
                "DERIVED_EDGE_WITHOUT_EXPLANATION",
                f"{len(derived_without_note)} DERIVED edge(s) have no notes explaining "
                f"the inference: {[e.id for e in derived_without_note]}. A DERIVED edge "
                "must be distinguishable from a directly-sourced one, including why it "
                "was inferred.",
                "v2 §34",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Aggregate helper
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Wiki Page (v2 §19/§38, arena-wiki-page-template.md)
# ---------------------------------------------------------------------------


@dataclass
class WikiHeader:
    """
    The rendered header block a Wiki page shows (arena-wiki-page-template.md
    "Required Header Block": Classification / Implementation status /
    Evidence status / Open decisions). Always computed fresh by
    ``derive_wiki_header`` from the records a WikiPage currently
    references -- this type is never persisted as part of WikiPage itself
    (see WikiPage's docstring for why: a cached header can silently go
    stale the moment the underlying records change).
    """

    classifications: list[str]  # distinct EvidenceClass values across referenced units, sorted
    implementation_statuses: list[str]  # distinct PresenceClass values across referenced units, sorted
    evidence_statuses: list[str]  # distinct EvidenceState values across referenced units, sorted
    open_decision_ids: list[str]  # decision IDs among referenced decisions whose status is OPEN
    dependencies: list[str]


def derive_wiki_header(
    page: WikiPage,
    knowledge_units: Iterable[KnowledgeUnit] = (),
    decisions: Iterable[DecisionRecord] = (),
) -> WikiHeader:
    """
    Compute a WikiPage's header block live from the records it currently
    references. This is the enforcement point for v2 §38's rule ("never
    allow planned architecture to appear as implemented behavior"): a page
    cannot assert a classification/implementation-status/evidence-status/
    open-decision list that isn't a live rollup of its referenced records,
    because those fields don't exist as independently settable WikiPage
    fields at all -- there is nothing to drift out of sync in the first
    place.

    Callers (the CLI, `render_wiki_page`) are expected to load the records
    named by ``page.knowledge_unit_ids`` / ``page.decision_ids`` and pass
    them in here; this function does not touch storage itself, consistent
    with every other validator in this module.
    """
    classifications = sorted({u.evidence_class.value for u in knowledge_units})
    implementation_statuses = sorted({u.implementation_status.value for u in knowledge_units})
    evidence_statuses = sorted({u.evidence_state.value for u in knowledge_units})
    open_decision_ids = sorted(d.id for d in decisions if d.status == DecisionStatus.OPEN)
    return WikiHeader(
        classifications=classifications,
        implementation_statuses=implementation_statuses,
        evidence_statuses=evidence_statuses,
        open_decision_ids=open_decision_ids,
        dependencies=list(page.dependencies),
    )


def validate_wiki_page(page: WikiPage) -> list[Finding]:
    """
    Layer 1: WikiPage-local validation.

    Checks only what can be determined from the page itself, with no
    access to any other record -- this function never touches storage and
    never receives other records as arguments. It checks:

      - page_number is one of the closed 00-17 set (defensive: WikiPage's
        own __post_init__ already coerces/rejects this, but a hand-crafted
        dict loaded outside that path should still be caught here);
      - title is non-empty (always true given a valid page_number, since
        it's a derived property, but asserted here rather than assumed);
      - content is non-empty;
      - every referenced ID (knowledge_unit_ids/decision_ids/audit_ids/
        work_item_ids) has valid ARENA-<...> ID syntax -- NOT whether it
        resolves to a real record, which requires other records and is
        therefore layer 2 (``validate_wiki_references``);
      - every dependency ID has valid ARENA-WIKI-<NN> syntax and the page
        does not list itself as its own dependency;
      - last_updated and every change_history entry's timestamp are
        non-empty;
      - page 14 (Implementation Inventory) references at least one
        Knowledge Unit or Repo Audit, and page 15 (Decisions) references
        at least one Decision Record -- these are shape checks on the
        page's own reference lists, not existence checks on what they
        point at.

    A WikiPage cannot override the state of the records it references --
    there is no code path here (or anywhere in WikiPage) that writes back
    to a KnowledgeUnit/DecisionRecord/RepoAudit/WorkItem; this function
    only reads the page's own fields.
    """
    findings: list[Finding] = []

    try:
        page_number = page.page_number if isinstance(page.page_number, WikiPageNumber) else WikiPageNumber(page.page_number)
    except ValueError:
        findings.append(
            Finding(
                Severity.ERROR,
                "WIKI_PAGE_INVALID_PAGE_NUMBER",
                f"Wiki page {page.id!r} has page_number {page.page_number!r}, which is not "
                "one of the closed 00-17 canonical index (v2 §38). Every Wiki page must "
                "belong to exactly one of the 18 canonical slots.",
                "v2 §38",
            )
        )
        return findings  # nothing else here is meaningful without a valid page number

    if not page.title.strip():  # pragma: no cover - title is derived and always non-empty for a valid enum
        findings.append(
            Finding(Severity.ERROR, "WIKI_PAGE_MISSING_TITLE", f"Wiki page {page.id!r} has no title.", "v2 §38")
        )

    if not page.content.strip():
        findings.append(
            Finding(
                Severity.WARNING,
                "WIKI_PAGE_EMPTY_CONTENT",
                f"Wiki page {page.id!r} ({page.title}) has no content. An empty page "
                "in the canonical index is indistinguishable from a page that was "
                "never actually written.",
                "v2 §38",
            )
        )

    def _check_id_syntax(ids: list[str], kind: str) -> None:
        for ref_id in ids:
            try:
                validate_generic_id(ref_id)
            except InvalidArenaId as exc:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "WIKI_REFERENCE_MALFORMED_ID",
                        f"Wiki page {page.id!r} references {kind} {ref_id!r}, which is not "
                        f"a syntactically valid Arena ID ({exc}).",
                        "v2 §8/§38",
                    )
                )

    _check_id_syntax(page.knowledge_unit_ids, "Knowledge Unit")
    _check_id_syntax(page.decision_ids, "Decision Record")
    _check_id_syntax(page.audit_ids, "Repo Audit")
    _check_id_syntax(page.work_item_ids, "Work Item")

    for dep in page.dependencies:
        if dep == page.id:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "WIKI_PAGE_SELF_DEPENDENCY",
                    f"Wiki page {page.id!r} lists itself as one of its own dependencies.",
                    "v2 §38",
                )
            )
            continue
        try:
            validate_generic_id(dep)
        except InvalidArenaId as exc:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "WIKI_DEPENDENCY_MALFORMED_ID",
                    f"Wiki page {page.id!r} depends on {dep!r}, which is not a "
                    f"syntactically valid Arena ID ({exc}).",
                    "v2 §8/§38",
                )
            )

    if not page.last_updated.strip():
        findings.append(
            Finding(
                Severity.WARNING,
                "WIKI_PAGE_MISSING_TIMESTAMP",
                f"Wiki page {page.id!r} has no last_updated timestamp.",
                "v2 §38",
            )
        )
    for entry in page.change_history:
        if not entry.timestamp.strip():
            findings.append(
                Finding(
                    Severity.WARNING,
                    "WIKI_CHANGE_HISTORY_MISSING_TIMESTAMP",
                    f"Wiki page {page.id!r} has a change_history entry with no timestamp.",
                    "v2 §38",
                )
            )

    if page_number == WikiPageNumber.IMPLEMENTATION_INVENTORY and not page.knowledge_unit_ids and not page.audit_ids:
        findings.append(
            Finding(
                Severity.WARNING,
                "IMPLEMENTATION_INVENTORY_PAGE_WITHOUT_EVIDENCE",
                f"Wiki page {page.id!r} is the Implementation Inventory page (14) but "
                "references no Knowledge Units or Repo Audits -- it has nothing to "
                "derive its claimed-vs-observed matrix from.",
                "v2 §38",
            )
        )

    if page_number == WikiPageNumber.DECISIONS and not page.decision_ids:
        findings.append(
            Finding(
                Severity.WARNING,
                "DECISIONS_PAGE_WITHOUT_DECISIONS",
                f"Wiki page {page.id!r} is the Decisions page (15) but references no "
                "Decision Records.",
                "v2 §38",
            )
        )

    if not page.change_history:
        findings.append(
            Finding(
                Severity.INFO,
                "WIKI_PAGE_NO_CHANGE_HISTORY",
                f"Wiki page {page.id!r} has no change_history entries yet.",
                "v2 §38",
            )
        )

    return findings


def validate_wiki_references(
    page: WikiPage,
    knowledge_units: Optional[dict[str, KnowledgeUnit]] = None,
    decisions: Optional[dict[str, DecisionRecord]] = None,
    audits: Optional[dict[str, RepoAudit]] = None,
    work_items: Optional[dict[str, WorkItem]] = None,
) -> list[Finding]:
    """
    Layer 2: cross-record validation.

    Checks whether a WikiPage's references actually resolve against other
    records -- this is the only layer that receives other records, and it
    never writes back to them. The ``knowledge_units``/``decisions``/
    ``audits``/``work_items`` parameters are dicts of ``{id: record}`` for
    records the caller has already loaded; this function never touches
    storage itself.

    When a mapping is omitted (None), its corresponding references are not
    checked for existence (nothing can be concluded about resolution
    without the records); when a mapping is provided but a referenced ID
    is absent from it, that is a dangling reference
    (``WIKI_REFERENCE_NOT_FOUND``).

    ID *syntax* is layer-1's job (``validate_wiki_page``); this function
    only checks resolution, so callers normally run both layers together.
    """
    findings: list[Finding] = []

    def _check_refs(ids: list[str], mapping: Optional[dict[str, Any]], kind: str) -> None:
        if mapping is None:
            return
        for ref_id in ids:
            if ref_id not in mapping:
                findings.append(
                    Finding(
                        Severity.ERROR,
                        "WIKI_REFERENCE_NOT_FOUND",
                        f"Wiki page {page.id!r} references {kind} {ref_id!r}, which does "
                        "not exist (or was not supplied for verification). A page must "
                        "not point at a record that isn't there.",
                        "v2 §38",
                    )
                )

    _check_refs(page.knowledge_unit_ids, knowledge_units, "Knowledge Unit")
    _check_refs(page.decision_ids, decisions, "Decision Record")
    _check_refs(page.audit_ids, audits, "Repo Audit")
    _check_refs(page.work_item_ids, work_items, "Work Item")

    return findings



# ---------------------------------------------------------------------------
# Aggregate helper
# ---------------------------------------------------------------------------


def has_errors(findings: Iterable[Finding]) -> bool:
    return any(f.severity == Severity.ERROR for f in findings)
