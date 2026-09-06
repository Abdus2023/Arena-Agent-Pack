"""
CLI-level tests for `work set-execution-state`'s transition-legality gate
(v2 §15, conformance audit Recommendation R10, row 2.2).

See `tests/test_execution_transition.py`'s module docstring for the full
scope discipline (what's implemented vs. the disclosed staleness gap).
This file specifically covers the CLI wiring: `work set-execution-state`
must call `validate_execution_transition` BEFORE mutating and refuse the
command (non-zero exit, unchanged on-disk state) on any illegal
transition -- mirroring `work set-state`'s existing check-then-mutate gate
for lifecycle_state. This was an explicit, reconciled design decision
(blocking ERROR at the CLI, not a warning-only advisory via `work
validate`), confirmed with the user before implementation.
"""

import json

from click.testing import CliRunner

from arena_agent.cli import cli
from arena_agent.storage import Workspace
from arena_agent.vocab import ExecutionState


def _run(runner, ws, *args):
    return runner.invoke(cli, ["--workspace", str(ws), *args])


def _run_json(runner, ws, *args):
    result = runner.invoke(cli, ["--workspace", str(ws), "--json", *args])
    return result, (json.loads(result.output) if result.output else None)


def _create(runner, ws, work_id="ARENA-WORK-1"):
    return _run(runner, ws, "work", "create", "--id", work_id, "--title", "t", "--responsibility", "r")


def test_illegal_jump_from_default_planned_to_completed_is_rejected(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", "COMPLETED")
    assert result.exit_code == 1
    assert "EXECUTION_STATE_ILLEGAL_TRANSITION" in result.output


def test_rejected_transition_does_not_mutate_stored_state(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", "COMPLETED")

    store = Workspace(ws)
    item = store.load_work_item("ARENA-WORK-1")
    assert item.execution_state == ExecutionState.PLANNED  # untouched, still the default


def test_issued_to_reconciled_directly_is_rejected_skips_indeterminate(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    for state in ["STARTED", "ISSUED"]:
        result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", state)
        assert result.exit_code == 0, result.output

    result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", "RECONCILED")
    assert result.exit_code == 1
    assert "EXECUTION_STATE_SKIPPED_INDETERMINATE" in result.output

    store = Workspace(ws)
    item = store.load_work_item("ARENA-WORK-1")
    assert item.execution_state == ExecutionState.ISSUED  # unchanged, rejection was not persisted


def test_legal_full_path_through_indeterminate_to_reconciled_succeeds(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    for state in ["STARTED", "ISSUED", "INDETERMINATE", "RECONCILED"]:
        result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", state)
        assert result.exit_code == 0, result.output

    store = Workspace(ws)
    item = store.load_work_item("ARENA-WORK-1")
    assert item.execution_state == ExecutionState.RECONCILED


def test_legal_path_to_failed_succeeds(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    for state in ["STARTED", "ISSUED", "FAILED"]:
        result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", state)
        assert result.exit_code == 0, result.output


def test_transition_out_of_terminal_completed_state_is_rejected(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    for state in ["STARTED", "ISSUED", "COMPLETED"]:
        result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", state)
        assert result.exit_code == 0, result.output

    result = _run(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", "RECONCILED")
    assert result.exit_code == 1
    assert "EXECUTION_STATE_ILLEGAL_TRANSITION" in result.output


def test_json_mode_reports_rejection_with_findings(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _create(runner, ws)

    result, data = _run_json(runner, ws, "work", "set-execution-state", "ARENA-WORK-1", "--state", "COMPLETED")
    assert result.exit_code == 1
    assert isinstance(data, (list, dict))
    payload_text = json.dumps(data)
    assert "EXECUTION_STATE_ILLEGAL_TRANSITION" in payload_text
