"""
Tests for validate_execution_transition (v2 §15, conformance audit
Recommendation R10, row 2.2).

Scope, locked with the user before any implementation existed (mirrors the
same investigate -> reconcile -> test-first -> implement discipline used for
R14 / check_claim_expiry):

  IMPLEMENT (objectively checkable, directly stated by §15's own diagram):
    - ExecutionState transitions follow a closed graph, not a single linear
      happy path: PLANNED -> STARTED -> ISSUED, and ISSUED branches three
      ways -- COMPLETED, FAILED, or INDETERMINATE -> RECONCILED.
    - ISSUED -> RECONCILED directly (skipping INDETERMINATE) is illegal,
      exactly the same "RUN_TASK -> DONE" compound-transition anti-pattern
      already enforced for LifecycleState (§9.3), applied to this axis.
    - This check is a BLOCKING ERROR at the CLI (`work set-execution-state`
      calls validate_execution_transition before mutating, and refuses the
      command on any ERROR finding), mirroring `work set-state`'s existing
      check-then-mutate gate for LifecycleState -- this was an explicit,
      reconciled design decision, not a default.

  DELIBERATELY NOT IMPLEMENTED (disclosed gap, not an oversight):
    - "Stalled ISSUED" staleness detection (an ISSUED item that never
      reaches any terminal/INDETERMINATE follow-up at all). §15 states
      "missing completion evidence does not automatically mean 'not
      executed'" but defines no staleness threshold or policy ("unless the
      governing specification explicitly defines another semantics" -- it
      doesn't). Using lifecycle_state progression (e.g. reaching OBSERVED/
      VERIFIED) as a staleness proxy was explicitly considered and REJECTED
      by the user: it would introduce a new semantic assumption (that those
      lifecycle states necessarily imply sufficient execution evidence)
      that the pack does not itself establish. No timestamp-based expiry
      policy is implemented either, for the same reason R14's claim-expiry
      policy is caller-supplied rather than fixed by this pack -- except
      here, unlike R14, no caller-supplied-policy mechanism is built at
      all, since no test in this file establishes what such a policy's
      call site or shape should be. This is a genuinely open, disclosed
      gap: this module CAN detect illegal transitions, but it CANNOT
      determine that an ISSUED state has gone stale without a governing
      policy the pack does not define.
"""

from __future__ import annotations

import ast
import inspect

from arena_agent.validation import has_errors, validate_execution_transition
from arena_agent.vocab import ExecutionState


def _get_function_body_source_excluding_docstring(module, func_name: str) -> str:
    """AST helper (mirrors tests/test_claim_expiry.py's precedent): returns
    a function's body source with its own docstring stripped, so a guard
    checks actual executable code, not prose that legitimately explains a
    deliberate scope boundary."""
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
# Legal transitions
# ---------------------------------------------------------------------------


def test_no_op_transition_is_always_legal():
    for state in ExecutionState:
        findings = validate_execution_transition(state, state)
        assert not has_errors(findings)


def test_planned_to_started_is_legal():
    findings = validate_execution_transition(ExecutionState.PLANNED, ExecutionState.STARTED)
    assert not has_errors(findings)


def test_started_to_issued_is_legal():
    findings = validate_execution_transition(ExecutionState.STARTED, ExecutionState.ISSUED)
    assert not has_errors(findings)


def test_issued_to_completed_is_legal():
    findings = validate_execution_transition(ExecutionState.ISSUED, ExecutionState.COMPLETED)
    assert not has_errors(findings)


def test_issued_to_failed_is_legal():
    findings = validate_execution_transition(ExecutionState.ISSUED, ExecutionState.FAILED)
    assert not has_errors(findings)


def test_issued_to_indeterminate_is_legal():
    findings = validate_execution_transition(ExecutionState.ISSUED, ExecutionState.INDETERMINATE)
    assert not has_errors(findings)


def test_indeterminate_to_reconciled_is_legal():
    findings = validate_execution_transition(ExecutionState.INDETERMINATE, ExecutionState.RECONCILED)
    assert not has_errors(findings)


# ---------------------------------------------------------------------------
# Illegal transitions -- the core §15 rule under test
# ---------------------------------------------------------------------------


def test_issued_to_reconciled_directly_is_illegal_skips_indeterminate():
    """The central §15 rule: INDETERMINATE MUST be passed through explicitly."""
    findings = validate_execution_transition(ExecutionState.ISSUED, ExecutionState.RECONCILED)
    assert has_errors(findings)
    assert any(f.code == "EXECUTION_STATE_SKIPPED_INDETERMINATE" for f in findings)


def test_planned_to_issued_directly_is_illegal_skips_started():
    findings = validate_execution_transition(ExecutionState.PLANNED, ExecutionState.ISSUED)
    assert has_errors(findings)
    assert any(f.code == "EXECUTION_STATE_ILLEGAL_TRANSITION" for f in findings)


def test_planned_to_completed_directly_is_illegal():
    findings = validate_execution_transition(ExecutionState.PLANNED, ExecutionState.COMPLETED)
    assert has_errors(findings)


def test_completed_to_anything_else_is_illegal_terminal_state():
    findings = validate_execution_transition(ExecutionState.COMPLETED, ExecutionState.RECONCILED)
    assert has_errors(findings)


def test_failed_to_anything_else_is_illegal_terminal_state():
    findings = validate_execution_transition(ExecutionState.FAILED, ExecutionState.COMPLETED)
    assert has_errors(findings)


def test_reconciled_to_anything_else_is_illegal_terminal_state():
    findings = validate_execution_transition(ExecutionState.RECONCILED, ExecutionState.ISSUED)
    assert has_errors(findings)


def test_backward_transition_is_illegal():
    findings = validate_execution_transition(ExecutionState.ISSUED, ExecutionState.STARTED)
    assert has_errors(findings)


def test_indeterminate_back_to_issued_is_illegal():
    """INDETERMINATE's only legal successor is RECONCILED, never back to ISSUED."""
    findings = validate_execution_transition(ExecutionState.INDETERMINATE, ExecutionState.ISSUED)
    assert has_errors(findings)


def test_completed_to_failed_is_illegal_both_are_terminal():
    findings = validate_execution_transition(ExecutionState.COMPLETED, ExecutionState.FAILED)
    assert has_errors(findings)


# ---------------------------------------------------------------------------
# Disclosed scope boundary: no staleness inference, no lifecycle_state
# coupling -- confirmed by construction, not just by docstring claim.
# ---------------------------------------------------------------------------


def test_validate_execution_transition_never_reads_lifecycle_state_as_code():
    """Confirms the rejected OBSERVED/VERIFIED-as-staleness-proxy design is
    not present as actual code -- this function checks transition legality
    only, never reads/compares lifecycle_state. Inspects the AST for real
    attribute access / enum references, not string literals: the function's
    own explanatory messages legitimately mention "lifecycle_state" in
    prose (cross-referencing the analogous §9.3 rule for LifecycleState),
    which is not the same as this function actually depending on it."""
    from arena_agent import validation

    source = inspect.getsource(validation)
    tree = ast.parse(source)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "validate_execution_transition":
            target = node
            break
    assert target is not None

    for node in ast.walk(target):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            continue  # string literals (messages) are not code dependencies
        if isinstance(node, ast.Attribute) and node.attr == "lifecycle_state":
            raise AssertionError("validate_execution_transition reads .lifecycle_state")
        if isinstance(node, ast.Name) and node.id == "LifecycleState":
            raise AssertionError("validate_execution_transition references LifecycleState")


def test_validate_execution_transition_never_references_time_or_datetime():
    """Confirms no timestamp-based staleness/expiry policy was smuggled in
    -- the disclosed gap (stalled-ISSUED detection) requires a policy this
    pack does not define, and none is invented here."""
    from arena_agent import validation

    body_source = _get_function_body_source_excluding_docstring(validation, "validate_execution_transition")
    assert "datetime" not in body_source
    assert "timedelta" not in body_source
    assert "now" not in body_source


def test_validate_execution_transition_is_a_pure_function_returning_findings_only():
    """Matches every other check_*/validate_* function in this module: it
    returns list[Finding] and (by construction, since it takes only
    ExecutionState values, not a WorkItem) cannot mutate anything."""
    sig = inspect.signature(validate_execution_transition)
    params = list(sig.parameters.values())
    assert len(params) == 2
    assert all(p.annotation == "ExecutionState" for p in params)
