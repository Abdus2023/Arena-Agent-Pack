"""
Conformance audit Recommendation R14 (Phase 6, row 2.16): v2 §24.1's
Ownership/Claiming contract states "Claims expire per the governing
operational policy (not fixed by this pack); an expired claim reverts the
item to `PLANNED` and MUST record the original agent's partial evidence
rather than discarding it." Before this change, `ClaimStatus.EXPIRED`
existed as a vocabulary value but nothing in this codebase ever set it,
checked for it, or exposed any mechanism for a caller to supply an expiry
policy at all.

Scope discipline (explicit, binding for this recommendation, reconciled
with the user before any code was written -- see the conformance
matrix's row 2.16 investigation note):

  - §24.1 mandates reverting an expired claim's item to `PLANNED`, but
    `validate_lifecycle_transition` already treats `EXECUTING -> PLANNED`
    as an ERROR-severity `LIFECYCLE_BACKWARD_TRANSITION` (§9.1's own
    canonical model) -- `PLANNED` is not `EXECUTING`'s defined failure
    branch (`CRASHED` is). The pack itself never reconciles this. This
    implementation does NOT silently resolve that contradiction by
    treating either section as overriding the other.
  - `check_claim_expiry` is a PURE detection hook, matching this
    codebase's established `check_*`/`validate_*` pattern
    (`validate_lifecycle_transition`, `validate_work_item`, etc. all
    return `list[Finding]` and never mutate). It must NEVER mutate
    `Ownership` or `lifecycle_state`, and must NEVER call or bypass
    `validate_lifecycle_transition`.
  - The expiry *policy* is caller-supplied (`max_age: timedelta`), per
    the pack's own "not fixed by this pack" language. `now` is
    evaluation-time context, not policy, and is a separate, optional,
    injectable parameter for deterministic testing.
  - Applying the actual consequence (setting `ClaimStatus.EXPIRED`, and
    whatever lifecycle transition the caller's own governing operational
    policy actually requires) remains a distinct, explicit,
    caller-controlled operation -- this recommendation's scope is
    detection only.
  - R14 is exclusively about claim expiry. It must not implement or
    reference `ExecutionState.INDETERMINATE`/`RECONCILED` reconciliation
    logic, which remains Recommendation R10's separate, untouched
    territory (Phase 6, next item).
"""

import ast
import copy
import dataclasses
import inspect
from datetime import datetime, timedelta, timezone

from arena_agent.models import Ownership, WorkItem, to_dict
from arena_agent.vocab import ClaimStatus, LifecycleState


def _item_with_claim(status: ClaimStatus, claimed_at, owner="agent-1"):
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.lifecycle_state = LifecycleState.EXECUTING
    item.ownership = Ownership(owner=owner, claimed_at=claimed_at, status=status)
    return item


def _get_function_body_source_excluding_docstring(module, func_name: str) -> str:
    """AST helper: returns a function's body source with its own
    docstring (if any) stripped, so guards below check actual executable
    code, not prose that legitimately explains/cross-references adjacent
    concepts (e.g. why this function deliberately does NOT touch them)."""
    source = inspect.getsource(module)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant
            ):
                body = body[1:]  # drop the docstring statement
            return "\n".join(ast.get_source_segment(source, n) or "" for n in body)
    raise AssertionError(f"{func_name} not found in {module.__name__}")


# ---------------------------------------------------------------------------
# Core detection behavior (to hold once check_claim_expiry exists)
# ---------------------------------------------------------------------------


def test_active_unexpired_claim_produces_no_finding():
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=1)).isoformat()
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert findings == []


def test_active_expired_claim_produces_a_finding():
    from arena_agent.validation import check_claim_expiry, Severity

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=48)).isoformat()
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert len(findings) == 1
    assert findings[0].code == "CLAIM_EXPIRED"
    assert findings[0].severity == Severity.WARNING
    assert "v2 §24.1" in findings[0].ref


def test_claim_exactly_at_max_age_boundary_is_not_expired():
    """age <= max_age -> not expired; age > max_age -> expired (explicit
    boundary semantics, not left ambiguous)."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=24)).isoformat()  # exactly max_age
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert findings == []


def test_claim_one_second_past_max_age_boundary_is_expired():
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=24, seconds=1)).isoformat()
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert len(findings) == 1
    assert findings[0].code == "CLAIM_EXPIRED"


def test_released_claim_is_never_flagged_as_expired():
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(days=999)).isoformat()  # ancient, but released
    item = _item_with_claim(ClaimStatus.RELEASED, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert findings == []


def test_already_expired_claim_produces_no_duplicate_finding():
    """A claim already marked EXPIRED is not re-flagged -- CLAIM_EXPIRED
    only fires for a still-ACTIVE claim that has exceeded the policy."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=48)).isoformat()
    item = _item_with_claim(ClaimStatus.EXPIRED, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert findings == []


def test_unclaimed_item_produces_no_finding():
    """An item that was never claimed (default Ownership) has nothing to
    expire."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    assert findings == []


def test_missing_claimed_at_on_active_claim_is_a_distinct_finding_not_an_invented_expiry():
    """An ACTIVE claim with no claimed_at timestamp is malformed data --
    this must be reported as its own distinct problem, never silently
    treated as "expired" (that would be inventing an expiry decision the
    policy was never actually asked to make) and never silently treated
    as "not expired" (that would hide a real data problem)."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at=None)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    codes = [f.code for f in findings]
    assert "CLAIM_EXPIRED" not in codes
    assert "CLAIM_ACTIVE_WITHOUT_TIMESTAMP" in codes


def test_malformed_claimed_at_on_active_claim_is_a_distinct_finding():
    """Same principle for an unparsable timestamp string, as distinct
    from a missing one -- both are malformed-data findings, never a
    manufactured expiry decision."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at="not-a-timestamp")

    findings = check_claim_expiry(item, max_age=timedelta(hours=24), now=now)
    codes = [f.code for f in findings]
    assert "CLAIM_EXPIRED" not in codes
    assert "CLAIM_TIMESTAMP_UNPARSEABLE" in codes


def test_now_defaults_to_current_time_when_omitted():
    """now is optional -- when omitted, the hook must use the real
    current time (evaluation-time context), not silently skip the check
    or require every caller to supply it."""
    from arena_agent.validation import check_claim_expiry

    claimed_at = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)

    findings = check_claim_expiry(item, max_age=timedelta(hours=24))
    assert any(f.code == "CLAIM_EXPIRED" for f in findings)


# ---------------------------------------------------------------------------
# Purity / non-mutation guarantees (the central architectural boundary)
# ---------------------------------------------------------------------------


def test_check_claim_expiry_never_mutates_the_work_item():
    """Calling the hook -- regardless of outcome -- must leave the
    WorkItem byte-for-byte unchanged. This is the central purity
    guarantee distinguishing R14's hook from R10's future territory."""
    from arena_agent.validation import check_claim_expiry

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    claimed_at = (now - timedelta(hours=48)).isoformat()
    item = _item_with_claim(ClaimStatus.ACTIVE, claimed_at)
    before = copy.deepcopy(to_dict(item))

    check_claim_expiry(item, max_age=timedelta(hours=24), now=now)

    after = to_dict(item)
    assert after == before
    assert item.ownership.status == ClaimStatus.ACTIVE  # unchanged, still ACTIVE
    assert item.lifecycle_state == LifecycleState.EXECUTING  # unchanged


def test_check_claim_expiry_never_invokes_validate_lifecycle_transition():
    """Static source guard: check_claim_expiry's own function BODY (not
    its docstring, which legitimately explains the deliberate boundary in
    prose) must never call validate_lifecycle_transition -- the pure
    detection hook must not call into (or attempt to bypass) the
    lifecycle-transition validator to manufacture its own transition
    decision."""
    from arena_agent import validation

    body_source = _get_function_body_source_excluding_docstring(validation, "check_claim_expiry")
    assert "validate_lifecycle_transition" not in body_source


def test_no_execution_to_planned_exception_introduced_into_lifecycle_transition():
    """Guard against silently resolving the §9.1<->§24.1 tension inside
    application code: EXECUTING -> PLANNED must remain an ERROR after
    R14, exactly as it was before. R14 detects expiry; it does not grant
    itself (or any caller) a special-cased lifecycle exception."""
    from arena_agent.validation import validate_lifecycle_transition, has_errors

    findings = validate_lifecycle_transition(LifecycleState.EXECUTING, LifecycleState.PLANNED)
    assert has_errors(findings)
    assert any(f.code == "LIFECYCLE_BACKWARD_TRANSITION" for f in findings)


def test_check_claim_expiry_does_not_reference_execution_state_reconciliation_values():
    """Explicit boundary check mirroring R18's precedent: no reference to
    ExecutionState.INDETERMINATE/RECONCILED anywhere in check_claim_expiry's
    executable BODY (the docstring's cross-reference explaining the
    boundary in prose is not itself a code reference) -- that
    reconciliation behavior is Recommendation R10's scope, not R14's."""
    from arena_agent import validation

    body_source = _get_function_body_source_excluding_docstring(validation, "check_claim_expiry")
    assert "INDETERMINATE" not in body_source
    assert "RECONCILED" not in body_source


def test_check_claim_expiry_has_no_mutating_side_effect_signature():
    """check_claim_expiry must return list[Finding] (matching every other
    check_*/validate_* function in this module) -- confirms it follows
    the pure-function pattern by construction, not just by convention."""
    from arena_agent.validation import check_claim_expiry

    sig = inspect.signature(check_claim_expiry)
    assert "item" in sig.parameters
    assert "max_age" in sig.parameters
    assert "now" in sig.parameters
    assert sig.parameters["now"].default is None
