"""
Conformance audit Recommendation R14 (Phase 6, row 2.16), CLI mutation
half: v2 §24.1 requires an expired claim to revert the item to `PLANNED`
and MUST record the original agent's partial evidence rather than
discarding it.

Scope discipline (explicit, binding for this recommendation -- see
`tests/test_claim_expiry.py`'s module docstring and the conformance
matrix's row 2.16 investigation note for the full normative reasoning):

  - `check_claim_expiry` (already implemented, `validation.py`) is a pure
    detection hook -- it never mutates anything.
  - `work expire-claim` (this CLI command) is the explicit,
    caller-controlled mutation operation. Per the user's explicit,
    binding decision: it mutates `Ownership` ONLY --
    `ClaimStatus.ACTIVE -> EXPIRED`, preserving `owner`/`claimed_at` as
    historical evidence (never wiped, since that provenance is exactly
    what §24.1's "MUST record the original agent's partial evidence"
    requires) -- and logs the expiry as a new lifecycle-log entry.
  - It does NOT touch `lifecycle_state` at all. §24.1's "reverts the item
    to PLANNED" is a *separate*, already-disclosed, unresolved tension
    against §9.1's `LIFECYCLE_BACKWARD_TRANSITION` rule (row 2.16): if a
    caller wants to also move `lifecycle_state`, they must do so via the
    existing `work set-state` command, which will visibly reject
    `EXECUTING -> PLANNED` today rather than silently succeeding or being
    silently bypassed by this command.
  - It must never expire a claim that isn't actually expired under the
    caller-supplied policy (no forcing/expiring on demand regardless of
    age) -- it must re-run `check_claim_expiry` itself, not trust the
    caller's assertion that a claim is expired.
"""

import json

from click.testing import CliRunner

from arena_agent.cli import cli
from arena_agent.storage import Workspace
from arena_agent.vocab import ClaimStatus, LifecycleState


def _run(runner, ws, *args):
    return runner.invoke(cli, ["--workspace", str(ws), *args])


def _run_json(runner, ws, *args):
    result = runner.invoke(cli, ["--workspace", str(ws), "--json", *args])
    return result, (json.loads(result.output) if result.output else None)


def _claim(runner, ws, work_id="ARENA-WORK-1", owner="agent-1"):
    _run(runner, ws, "work", "create", "--id", work_id, "--title", "t", "--responsibility", "r")
    _run(runner, ws, "work", "claim", work_id, "--owner", owner)


def test_expire_claim_command_is_registered():
    """work expire-claim exists as a real subcommand (post-implementation
    replacement for the pre-implementation existence-gap proof)."""
    runner = CliRunner()
    result = runner.invoke(cli, ["work", "--help"])
    assert "expire-claim" in result.output


def test_expire_claim_rejects_a_claim_that_is_not_actually_expired(tmp_path):
    """work expire-claim must re-check expiry itself against the supplied
    policy, not trust the caller's assertion -- an ACTIVE claim younger
    than max_age must be rejected, not force-expired."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    result = _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "9999")
    assert result.exit_code != 0

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    assert item.ownership.status == ClaimStatus.ACTIVE  # unchanged


def test_expire_claim_succeeds_on_an_actually_expired_claim(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    # Backdate the claim directly through storage so the CLI test doesn't
    # depend on real wall-clock sleeping.
    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    from datetime import datetime, timedelta, timezone

    item.ownership.claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    workspace.save_work_item(item)

    result = _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")
    assert result.exit_code == 0, result.output

    loaded = workspace.load_work_item("ARENA-WORK-1")
    assert loaded.ownership.status == ClaimStatus.EXPIRED


def test_expire_claim_preserves_owner_and_claimed_at_as_historical_evidence(tmp_path):
    """§24.1: an expired claim MUST record the original agent's partial
    evidence rather than discarding it -- owner/claimed_at must survive
    the expiry, not be wiped."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws, owner="agent-1")

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    from datetime import datetime, timedelta, timezone

    original_claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    item.ownership.claimed_at = original_claimed_at
    workspace.save_work_item(item)

    _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")

    loaded = workspace.load_work_item("ARENA-WORK-1")
    assert loaded.ownership.owner == "agent-1"
    assert loaded.ownership.claimed_at == original_claimed_at


def test_expire_claim_never_touches_lifecycle_state(tmp_path):
    """Central architectural boundary (explicit, user-locked decision):
    work expire-claim mutates Ownership only. lifecycle_state (EXECUTING
    in this test, matching the real §24.1 scenario) must remain
    completely untouched -- reverting to PLANNED, if ever done, is a
    separate operation via work set-state, not this command."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    item.lifecycle_state = LifecycleState.EXECUTING
    from datetime import datetime, timedelta, timezone

    item.ownership.claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    workspace.save_work_item(item)

    _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")

    loaded = workspace.load_work_item("ARENA-WORK-1")
    assert loaded.lifecycle_state == LifecycleState.EXECUTING  # unchanged


def test_expire_claim_records_a_new_lifecycle_log_entry(tmp_path):
    """The expiry must be auditable -- recorded as a new, appended
    lifecycle-log entry, never silently applied with no trace."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    entries_before = len(item.lifecycle_log)
    from datetime import datetime, timedelta, timezone

    item.ownership.claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    workspace.save_work_item(item)

    _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")

    loaded = workspace.load_work_item("ARENA-WORK-1")
    assert len(loaded.lifecycle_log) == entries_before + 1
    new_entry = loaded.lifecycle_log[-1]
    assert "expir" in str(new_entry.details).lower() or "expir" in str(new_entry.stage).lower()


def test_expire_claim_on_unclaimed_item_fails_cleanly(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "work", "create", "--id", "ARENA-WORK-1", "--title", "t", "--responsibility", "r")

    result = _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")
    assert result.exit_code != 0


def test_expire_claim_on_already_expired_claim_is_a_no_op_failure_not_a_double_expiry(tmp_path):
    """An already-EXPIRED claim has nothing left to expire -- must fail
    cleanly (there's no ACTIVE claim to act on), not silently succeed
    with a duplicate/no-op mutation."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    from datetime import datetime, timedelta, timezone

    item.ownership.claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    item.ownership.status = ClaimStatus.EXPIRED
    workspace.save_work_item(item)

    result = _run(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")
    assert result.exit_code != 0

    loaded = workspace.load_work_item("ARENA-WORK-1")
    assert len(loaded.lifecycle_log) == len(item.lifecycle_log)  # no new entry added


def test_expire_claim_json_mode_reports_the_transition(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _claim(runner, ws)

    workspace = Workspace(str(ws))
    item = workspace.load_work_item("ARENA-WORK-1")
    from datetime import datetime, timedelta, timezone

    item.ownership.claimed_at = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    workspace.save_work_item(item)

    result, data = _run_json(runner, ws, "work", "expire-claim", "ARENA-WORK-1", "--max-age-hours", "24")
    assert result.exit_code == 0
    assert data["status"] == "ok"
