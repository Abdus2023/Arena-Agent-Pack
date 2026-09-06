"""
Conformance audit Recommendation R18 (Phase 5C, row 3.6): v2 §27's Work
Item template has a "### Persistence" narrative section with four
sub-fields -- Durable state, Journal, Recovery behavior, and
Indeterminate states and reconciliation path -- with no field-level
equivalent anywhere on `WorkItem` before this change.

Scope discipline (explicit, binding for this recommendation): these are
additive, free-text narrative fields only, following the exact precedent
already set by `required_authority`/`forbidden_authority`/
`resource_budget` (also free-text §27 template sections with no
completeness validation). R18 must NOT:
  - reference `ExecutionState.INDETERMINATE`/`RECONCILED` from any new
    validation check (that reconciliation *logic* is Recommendation R10's
    territory, Phase 6, deliberately untouched here);
  - add journal mutation/append-only machinery (the template's Journal
    sub-field is one narrative line, not a structured log -- unlike
    `lifecycle_log`, which is a genuinely different, pre-existing,
    already-append-only concept);
  - add any new completeness/validation check at all.
A field describing the journal/recovery situation is not itself a journal
or recovery *implementation* -- these tests exist to keep that boundary
enforced going forward, not to grow it.
"""

import dataclasses

from arena_agent.models import WorkItem, to_dict
from arena_agent.storage import Workspace
from arena_agent.vocab import ExecutionState


def test_work_item_has_all_four_persistence_narrative_fields():
    """§27's Persistence section has exactly four sub-fields; all four
    must exist on WorkItem as plain strings, defaulting to empty like
    every other free-text §27 section (required_authority, etc.)."""
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    for name in (
        "durable_state",
        "journal",
        "recovery_behavior",
        "indeterminate_states_reconciliation_path",
    ):
        assert hasattr(item, name), f"WorkItem is missing the {name!r} field (v2 §27 Persistence)"
        assert getattr(item, name) == "", f"{name!r} should default to '' like other free-text §27 fields"
        assert isinstance(getattr(item, name), str)


def test_persistence_fields_are_plain_strings_not_a_new_abstraction():
    """These are narrative fields, not a new Journal/Recovery object --
    confirms the dataclass field type is exactly `str`, matching the
    Authority/Resources precedent exactly (no dedicated dataclass, no
    list, no dict)."""
    for f in dataclasses.fields(WorkItem):
        if f.name in (
            "durable_state",
            "journal",
            "recovery_behavior",
            "indeterminate_states_reconciliation_path",
        ):
            assert f.type in ("str", str), f"{f.name!r} must be a plain str field, got {f.type!r}"


def test_persistence_fields_round_trip_through_workspace_storage(tmp_path):
    """A populated Persistence narrative must survive a save/load cycle
    through the real JSON file store, not just exist in memory."""
    ws = Workspace(str(tmp_path))
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        durable_state="Recorded in the JSON workspace store once saved.",
        journal="No separate write-ahead journal; each save is a full-file overwrite.",
        recovery_behavior="On restart, the last successfully saved JSON file is authoritative.",
        indeterminate_states_reconciliation_path=(
            "See ExecutionState.INDETERMINATE -> RECONCILED (v2 §14/§15); "
            "this field only documents the path, it does not implement it."
        ),
    )
    ws.save_work_item(item)
    loaded = ws.load_work_item("ARENA-WORK-1")
    assert loaded.durable_state == item.durable_state
    assert loaded.journal == item.journal
    assert loaded.recovery_behavior == item.recovery_behavior
    assert (
        loaded.indeterminate_states_reconciliation_path
        == item.indeterminate_states_reconciliation_path
    )


def test_to_dict_serializes_persistence_fields():
    """The generic to_dict() projection (used by JSON storage and --json
    CLI output) must include the four new fields like every other field --
    proves this is a plain additive dataclass field, not something
    special-cased out of serialization."""
    item = WorkItem(
        id="ARENA-WORK-1",
        title="t",
        responsibility="r",
        journal="some journal note",
    )
    d = to_dict(item)
    assert d["journal"] == "some journal note"
    assert "durable_state" in d
    assert "recovery_behavior" in d
    assert "indeterminate_states_reconciliation_path" in d


def test_r18_does_not_add_any_new_validation_check():
    """Explicit negative-path guard against scope creep: populating (or
    leaving empty) the four Persistence narrative fields must never by
    itself produce a new Finding -- there is deliberately no
    completeness/consistency check for this template section, matching
    the pre-existing Authority/Resources precedent exactly."""
    from arena_agent.validation import validate_work_item

    empty_item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    findings_before = {f.code for f in validate_work_item(empty_item)}

    filled_item = WorkItem(
        id="ARENA-WORK-2",
        title="t",
        responsibility="r",
        durable_state="x",
        journal="y",
        recovery_behavior="z",
        indeterminate_states_reconciliation_path="w",
    )
    findings_after = {f.code for f in validate_work_item(filled_item)}

    persistence_related_codes = {
        c for c in findings_before | findings_after if "PERSISTENCE" in c or "JOURNAL" in c or "RECOVERY" in c
    }
    assert persistence_related_codes == set(), (
        "R18 must not introduce any new Persistence/Journal/Recovery validation "
        f"check; found: {persistence_related_codes}"
    )


def test_r18_does_not_reference_execution_state_reconciliation_values():
    """Explicit boundary check: R18 is data-shape only. No validation
    logic anywhere should branch on ExecutionState.INDETERMINATE or
    ExecutionState.RECONCILED as a result of adding these fields -- that
    reconciliation *behavior* is Recommendation R10's scope (Phase 6),
    not R18's. This is a static source-level guard, not a behavioral one,
    since the enum values are legitimately used elsewhere (their
    definition in vocab.py, unrelated to WorkItem's new fields)."""
    import ast
    import inspect

    from arena_agent import validation

    source = inspect.getsource(validation)
    tree = ast.parse(source)

    # Find validate_work_item specifically and confirm it contains no
    # reference to INDETERMINATE/RECONCILED anywhere in its body.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "validate_work_item":
            func_source = ast.get_source_segment(source, node) or ""
            assert "INDETERMINATE" not in func_source
            assert "RECONCILED" not in func_source
            return
    raise AssertionError("validate_work_item not found in validation.py")
