"""
Phase 2: Wiki Page (v2 §19/§38, arena-wiki-page-template.md).

Covers WikiPageNumber/WIKI_PAGE_TITLES (vocab), WikiPage/WikiChangeHistoryEntry
(models), storage round-trip, derive_wiki_header/validate_wiki_page
(validation), render_wiki_page (reporting), and the `wiki` CLI command group.
Deliberately does not touch anything in Phase 1's frozen status/BLOCKED
machinery.
"""

import json

import pytest
from click.testing import CliRunner

from arena_agent.cli import cli
from arena_agent.models import DecisionRecord, KnowledgeUnit, WikiChangeHistoryEntry, WikiPage
from arena_agent.reporting import render_wiki_page
from arena_agent.storage import RecordNotFound, Workspace
from arena_agent.validation import (
    Severity,
    derive_wiki_header,
    has_errors,
    validate_wiki_page,
    validate_wiki_references,
)
from arena_agent.vocab import (
    Confidence,
    DecisionStatus,
    EvidenceClass,
    EvidenceState,
    PresenceClass,
    WIKI_PAGE_TITLES,
    WikiPageNumber,
)


# ---------------------------------------------------------------------------
# vocab
# ---------------------------------------------------------------------------


def test_wiki_page_number_is_closed_18_member_set():
    values = [p.value for p in WikiPageNumber]
    assert values == [f"{i:02d}" for i in range(18)]


def test_wiki_page_titles_cover_every_page_number():
    assert set(WIKI_PAGE_TITLES.keys()) == set(WikiPageNumber)
    assert WIKI_PAGE_TITLES[WikiPageNumber.STATUS] == "Status"
    assert WIKI_PAGE_TITLES[WikiPageNumber.RUNBOOKS] == "Runbooks"
    assert WIKI_PAGE_TITLES[WikiPageNumber.IMPLEMENTATION_INVENTORY] == "Implementation Inventory"
    assert WIKI_PAGE_TITLES[WikiPageNumber.DECISIONS] == "Decisions"


def test_wiki_page_number_rejects_out_of_range_value():
    with pytest.raises(ValueError):
        WikiPageNumber("18")
    with pytest.raises(ValueError):
        WikiPageNumber("Status")


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------


def test_wiki_page_title_is_derived_not_stored():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS)
    assert page.title == "Status"
    # title is a read-only property -- there is no way to set it independently
    with pytest.raises(AttributeError):
        page.title = "Something Else"


def test_wiki_page_coerces_string_page_number_in_post_init():
    page = WikiPage(id="ARENA-WIKI-05", page_number="05")
    assert page.page_number is WikiPageNumber.INVARIANTS
    assert page.title == "Invariants"


def test_wiki_page_has_no_header_metadata_fields():
    """
    The header block (classification/implementation-status/evidence-status/
    open-decisions) must never be an independently stored WikiPage field --
    only derivable via validation.derive_wiki_header at render time.
    """
    field_names = {f.name for f in __import__("dataclasses").fields(WikiPage)}
    for forbidden in ("classification", "implementation_status", "evidence_status", "open_decisions"):
        assert forbidden not in field_names


def test_wiki_page_default_fields():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS)
    assert page.content == ""
    assert page.knowledge_unit_ids == []
    assert page.decision_ids == []
    assert page.audit_ids == []
    assert page.work_item_ids == []
    assert page.dependencies == []
    assert page.change_history == []


def test_wiki_change_history_entry_defaults():
    entry = WikiChangeHistoryEntry()
    assert entry.change == ""
    assert entry.is_semantic_change is False
    assert entry.related_decision_id is None
    assert entry.referenced_records_added == []
    assert entry.referenced_records_removed == []


# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------


def test_wiki_page_id_is_stable_per_page_number():
    assert Workspace.wiki_page_id(WikiPageNumber.STATUS) == "ARENA-WIKI-00"
    assert Workspace.wiki_page_id("14") == "ARENA-WIKI-14"


def test_wiki_page_roundtrip(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    page = WikiPage(
        id=Workspace.wiki_page_id(WikiPageNumber.DECISIONS),
        page_number=WikiPageNumber.DECISIONS,
        content="Decisions narrative.",
        scope="repo-wide",
        source="manual",
        repository_revision="abc123",
        decision_ids=["ARENA-DECISION-1"],
        dependencies=["ARENA-WIKI-00"],
        updated_by="alice",
        change_history=[
            WikiChangeHistoryEntry(
                timestamp="2026-01-01T00:00:00+00:00",
                updated_by="alice",
                change="initial draft",
                is_semantic_change=True,
                related_decision_id="ARENA-DECISION-1",
                referenced_records_added=["ARENA-DECISION-1"],
            )
        ],
    )
    ws.save_wiki_page(page)
    loaded = ws.load_wiki_page(page.id)
    assert loaded.id == page.id
    assert loaded.page_number is WikiPageNumber.DECISIONS
    assert loaded.title == "Decisions"
    assert loaded.content == "Decisions narrative."
    assert loaded.decision_ids == ["ARENA-DECISION-1"]
    assert loaded.dependencies == ["ARENA-WIKI-00"]
    assert len(loaded.change_history) == 1
    entry = loaded.change_history[0]
    assert isinstance(entry, WikiChangeHistoryEntry)
    assert entry.is_semantic_change is True
    assert entry.related_decision_id == "ARENA-DECISION-1"
    assert entry.referenced_records_added == ["ARENA-DECISION-1"]


def test_wiki_page_missing_raises(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    with pytest.raises(RecordNotFound):
        ws.load_wiki_page("ARENA-WIKI-16")


def test_list_wiki_pages(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.STATUS), page_number=WikiPageNumber.STATUS))
    ws.save_wiki_page(WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.RUNBOOKS), page_number=WikiPageNumber.RUNBOOKS))
    pages = ws.list_wiki_pages()
    assert {p.id for p in pages} == {"ARENA-WIKI-00", "ARENA-WIKI-17"}


def test_wiki_pages_subdir_registered(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    assert (tmp_path / "ws" / "wiki_pages").exists()


# ---------------------------------------------------------------------------
# validation: derive_wiki_header
# ---------------------------------------------------------------------------


def _unit(evidence_class, impl_status, evidence_state, uid="ARENA-U-1"):
    return KnowledgeUnit(
        id=uid,
        meaning="x",
        evidence_class=evidence_class,
        confidence=Confidence.HIGH,
        implementation_status=impl_status,
        evidence_state=evidence_state,
    )


def test_derive_wiki_header_empty_page_has_empty_rollups():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS)
    header = derive_wiki_header(page)
    assert header.classifications == []
    assert header.implementation_statuses == []
    assert header.evidence_statuses == []
    assert header.open_decision_ids == []
    assert header.dependencies == []


def test_derive_wiki_header_rolls_up_referenced_units_sorted_distinct():
    page = WikiPage(
        id="ARENA-WIKI-14",
        page_number=WikiPageNumber.IMPLEMENTATION_INVENTORY,
        knowledge_unit_ids=["u1", "u2", "u3"],
    )
    units = [
        _unit(EvidenceClass.OBSERVED, PresenceClass.PRESENT, EvidenceState.VALIDATED, "u1"),
        _unit(EvidenceClass.ARCHITECTURAL_PROPOSAL, PresenceClass.PLANNED, EvidenceState.PARTIAL, "u2"),
        _unit(EvidenceClass.OBSERVED, PresenceClass.PRESENT, EvidenceState.VALIDATED, "u3"),
    ]
    header = derive_wiki_header(page, knowledge_units=units)
    assert header.classifications == sorted({"OBSERVED", "ARCHITECTURAL-PROPOSAL"})
    assert header.implementation_statuses == sorted({"PRESENT", "PLANNED"})
    assert header.evidence_statuses == sorted({"VALIDATED", "PARTIAL"})


def test_derive_wiki_header_only_open_decisions_counted():
    page = WikiPage(id="ARENA-WIKI-15", page_number=WikiPageNumber.DECISIONS, decision_ids=["d1", "d2"])
    d1 = DecisionRecord(id="d1", question="q1", status=DecisionStatus.OPEN)
    d2 = DecisionRecord(id="d2", question="q2", status=DecisionStatus.RESOLVED)
    header = derive_wiki_header(page, decisions=[d1, d2])
    assert header.open_decision_ids == ["d1"]


def test_derive_wiki_header_never_persisted_on_page():
    """derive_wiki_header returns a fresh value; WikiPage itself has nowhere to store it."""
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS)
    derive_wiki_header(page, knowledge_units=[_unit(EvidenceClass.OBSERVED, PresenceClass.PRESENT, EvidenceState.VALIDATED)])
    assert not hasattr(page, "classifications")
    assert not hasattr(page, "implementation_status")


# ---------------------------------------------------------------------------
# validation: validate_wiki_page
# ---------------------------------------------------------------------------


def test_validate_wiki_page_empty_content_warns():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="   ")
    findings = validate_wiki_page(page)
    codes = {f.code for f in findings}
    assert "WIKI_PAGE_EMPTY_CONTENT" in codes
    assert not has_errors(findings)


def test_validate_wiki_page_dangling_reference_is_error_when_mapping_supplied():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", knowledge_unit_ids=["ARENA-U-GHOST"])
    findings = validate_wiki_references(page, knowledge_units={})
    assert has_errors(findings)
    assert any(f.code == "WIKI_REFERENCE_NOT_FOUND" and f.severity == Severity.ERROR for f in findings)


def test_validate_wiki_references_not_checked_when_mapping_omitted():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", knowledge_unit_ids=["ARENA-U-GHOST"])
    findings = validate_wiki_references(page)  # knowledge_units=None -> skip existence check
    assert not any(f.code == "WIKI_REFERENCE_NOT_FOUND" for f in findings)


def test_validate_wiki_page_resolved_reference_is_not_flagged():
    unit = _unit(EvidenceClass.OBSERVED, PresenceClass.PRESENT, EvidenceState.VALIDATED, "ARENA-U-1")
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", knowledge_unit_ids=["ARENA-U-1"])
    findings = validate_wiki_references(page, knowledge_units={"ARENA-U-1": unit})
    assert not any(f.code == "WIKI_REFERENCE_NOT_FOUND" for f in findings)


def test_validate_wiki_page_is_local_only_and_never_touches_other_records():
    """
    validate_wiki_page (layer 1) takes only the page itself -- there is no
    parameter through which another record could be passed in, so it is
    architecturally impossible for this layer to do cross-record checks.
    """
    import inspect

    sig = inspect.signature(validate_wiki_page)
    assert list(sig.parameters) == ["page"]


def test_validate_wiki_page_rejects_malformed_referenced_id_syntax():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", knowledge_unit_ids=["not-an-id"])
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_REFERENCE_MALFORMED_ID" and f.severity == Severity.ERROR for f in findings)


def test_validate_wiki_page_accepts_well_formed_referenced_id_syntax():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", knowledge_unit_ids=["ARENA-AUTH-LOGIN-FLOW"])
    findings = validate_wiki_page(page)
    assert not any(f.code == "WIKI_REFERENCE_MALFORMED_ID" for f in findings)


def test_validate_wiki_page_rejects_self_dependency():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", dependencies=["ARENA-WIKI-00"])
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_PAGE_SELF_DEPENDENCY" and f.severity == Severity.ERROR for f in findings)


def test_validate_wiki_page_rejects_malformed_dependency_id():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", dependencies=["not-a-wiki-id"])
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_DEPENDENCY_MALFORMED_ID" and f.severity == Severity.ERROR for f in findings)


def test_validate_wiki_page_accepts_valid_dependency_on_another_page():
    page = WikiPage(id="ARENA-WIKI-01", page_number=WikiPageNumber.SOURCE_CORPUS, content="x", dependencies=["ARENA-WIKI-00"])
    findings = validate_wiki_page(page)
    assert not any(f.code in ("WIKI_DEPENDENCY_MALFORMED_ID", "WIKI_PAGE_SELF_DEPENDENCY") for f in findings)


def test_validate_wiki_page_missing_last_updated_warns():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x", last_updated="")
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_PAGE_MISSING_TIMESTAMP" and f.severity == Severity.WARNING for f in findings)


def test_validate_wiki_page_change_history_entry_missing_timestamp_warns():
    page = WikiPage(
        id="ARENA-WIKI-00",
        page_number=WikiPageNumber.STATUS,
        content="x",
        change_history=[WikiChangeHistoryEntry(timestamp="", change="edited")],
    )
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_CHANGE_HISTORY_MISSING_TIMESTAMP" and f.severity == Severity.WARNING for f in findings)


def test_validate_wiki_page_rejects_invalid_page_number_on_hand_crafted_data():
    """
    A page number outside 00-17 should never reach here via normal
    construction (WikiPage.__post_init__ raises first), but a
    hand-edited/corrupted record loaded via a permissive path must still
    be caught by validation, not silently accepted -- mirrors the Phase 1
    invariant that the validator remains authoritative regardless of how
    the record was produced.
    """
    page = WikiPage.__new__(WikiPage)
    page.id = "ARENA-WIKI-99"
    page.page_number = "99"
    page.content = "x"
    page.scope = ""
    page.source = ""
    page.repository_revision = ""
    page.knowledge_unit_ids = []
    page.decision_ids = []
    page.audit_ids = []
    page.work_item_ids = []
    page.dependencies = []
    page.last_updated = "2026-01-01T00:00:00+00:00"
    page.updated_by = ""
    page.change_history = []
    page.pack_version = "2.0.0"
    findings = validate_wiki_page(page)
    assert any(f.code == "WIKI_PAGE_INVALID_PAGE_NUMBER" and f.severity == Severity.ERROR for f in findings)




def test_validate_wiki_page_implementation_inventory_without_evidence_warns():
    page = WikiPage(id="ARENA-WIKI-14", page_number=WikiPageNumber.IMPLEMENTATION_INVENTORY, content="x")
    findings = validate_wiki_page(page)
    assert any(f.code == "IMPLEMENTATION_INVENTORY_PAGE_WITHOUT_EVIDENCE" for f in findings)


def test_validate_wiki_page_implementation_inventory_with_audit_does_not_warn():
    page = WikiPage(
        id="ARENA-WIKI-14",
        page_number=WikiPageNumber.IMPLEMENTATION_INVENTORY,
        content="x",
        audit_ids=["a1"],
    )
    findings = validate_wiki_page(page)
    assert not any(f.code == "IMPLEMENTATION_INVENTORY_PAGE_WITHOUT_EVIDENCE" for f in findings)


def test_validate_wiki_page_decisions_page_without_decisions_warns():
    page = WikiPage(id="ARENA-WIKI-15", page_number=WikiPageNumber.DECISIONS, content="x")
    findings = validate_wiki_page(page)
    assert any(f.code == "DECISIONS_PAGE_WITHOUT_DECISIONS" for f in findings)


def test_validate_wiki_page_no_change_history_is_info_only():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x")
    findings = validate_wiki_page(page)
    matches = [f for f in findings if f.code == "WIKI_PAGE_NO_CHANGE_HISTORY"]
    assert len(matches) == 1
    assert matches[0].severity == Severity.INFO
    assert not has_errors(findings)


def test_validate_wiki_page_with_change_history_no_info_finding():
    page = WikiPage(
        id="ARENA-WIKI-00",
        page_number=WikiPageNumber.STATUS,
        content="x",
        change_history=[WikiChangeHistoryEntry(change="edited")],
    )
    findings = validate_wiki_page(page)
    assert not any(f.code == "WIKI_PAGE_NO_CHANGE_HISTORY" for f in findings)


# ---------------------------------------------------------------------------
# reporting: render_wiki_page
# ---------------------------------------------------------------------------


def test_render_wiki_page_includes_heading_and_title():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="hello")
    md = render_wiki_page(page)
    assert md.startswith("# 00 Status")
    assert "hello" in md
    assert "## Required Header Block" in md
    assert "## Content" in md
    assert "## Knowledge Units Referenced" in md
    assert "## Change History" in md


def test_render_wiki_page_without_header_shows_not_computed():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="hello")
    md = render_wiki_page(page, header=None)
    assert "_not computed_" in md


def test_render_wiki_page_with_header_shows_rollups():
    page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="hello", knowledge_unit_ids=["u1"])
    header = derive_wiki_header(page, knowledge_units=[_unit(EvidenceClass.OBSERVED, PresenceClass.PRESENT, EvidenceState.VALIDATED, "u1")])
    md = render_wiki_page(page, header=header)
    assert "OBSERVED" in md
    assert "PRESENT" in md
    assert "VALIDATED" in md


def test_render_wiki_page_implementation_inventory_section_only_on_page_14():
    inv_page = WikiPage(id="ARENA-WIKI-14", page_number=WikiPageNumber.IMPLEMENTATION_INVENTORY, content="x")
    other_page = WikiPage(id="ARENA-WIKI-00", page_number=WikiPageNumber.STATUS, content="x")
    assert "## Implementation Inventory" in render_wiki_page(inv_page)
    assert "## Implementation Inventory" not in render_wiki_page(other_page)


def test_render_wiki_page_change_history_rows():
    page = WikiPage(
        id="ARENA-WIKI-00",
        page_number=WikiPageNumber.STATUS,
        content="x",
        change_history=[
            WikiChangeHistoryEntry(timestamp="T1", updated_by="alice", change="did a thing", is_semantic_change=True, related_decision_id="ARENA-DECISION-1"),
        ],
    )
    md = render_wiki_page(page)
    assert "did a thing" in md
    assert "alice" in md
    assert "ARENA-DECISION-1" in md


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run(runner, ws, *args):
    return runner.invoke(cli, ["--workspace", str(ws), *args])


def _run_json(runner, ws, *args):
    result = runner.invoke(cli, ["--workspace", str(ws), "--json", *args])
    assert result.exit_code in (0, 1), result.output
    return result, json.loads(result.output)


def test_wiki_create_persists_and_derives_title(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    result = _run(runner, ws, "wiki", "create", "--page", "00", "--content", "status page content")
    assert result.exit_code == 0
    _, data = _run_json(runner, ws, "wiki", "show", "ARENA-WIKI-00")
    assert data["title"] == "Status"
    assert data["wiki_page"]["content"] == "status page content"


def test_wiki_create_rejects_invalid_page_number_before_persisting(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    result = _run(runner, ws, "wiki", "create", "--page", "99", "--content", "x")
    assert result.exit_code != 0
    assert not (ws / "wiki_pages").exists() or list((ws / "wiki_pages").iterdir()) == []


def test_wiki_create_always_persists_even_with_dangling_reference(tmp_path):
    """
    Mirrors decision/report `create`: findings (including ERROR severity)
    are surfaced, but `create` never itself gates the exit code -- only
    dedicated `validate`/lifecycle commands do that.
    """
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    result = _run(runner, ws, "wiki", "create", "--page", "01", "--knowledge-unit", "ARENA-GHOST-UNIT")
    assert result.exit_code == 0, result.output
    assert "WIKI_REFERENCE_NOT_FOUND" in result.output
    _, data = _run_json(runner, ws, "wiki", "show", "ARENA-WIKI-01")
    assert data["wiki_page"]["knowledge_unit_ids"] == ["ARENA-GHOST-UNIT"]  # still persisted


def test_wiki_list_shows_all_created_pages(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "00", "--content", "a")
    _run(runner, ws, "wiki", "create", "--page", "17", "--content", "b")
    _, data = _run_json(runner, ws, "wiki", "list")
    ids = {row["id"] for row in data}
    assert ids == {"ARENA-WIKI-00", "ARENA-WIKI-17"}


def test_wiki_update_appends_change_history_and_adds_reference(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(
        runner,
        ws,
        "unit",
        "create",
        "--domain",
        "auth",
        "--subject",
        "login",
        "--property",
        "flow",
        "--meaning",
        "m",
        "--evidence-class",
        "OBSERVED",
        "--confidence",
        "HIGH",
    )
    _, units = _run_json(runner, ws, "unit", "list")
    unit_id = units[0]["id"]

    _run(runner, ws, "wiki", "create", "--page", "14", "--content", "inventory")
    result = _run(
        runner,
        ws,
        "wiki",
        "update",
        "ARENA-WIKI-14",
        "--add-knowledge-unit",
        unit_id,
        "--change",
        "linked unit",
        "--updated-by",
        "bob",
    )
    assert result.exit_code == 0
    _, data = _run_json(runner, ws, "wiki", "show", "ARENA-WIKI-14")
    assert data["wiki_page"]["knowledge_unit_ids"] == [unit_id]
    assert len(data["wiki_page"]["change_history"]) == 1
    assert data["wiki_page"]["change_history"][0]["change"] == "linked unit"
    assert data["wiki_page"]["change_history"][0]["updated_by"] == "bob"
    # header now reflects the linked unit live
    assert data["header"]["implementation_statuses"] == ["UNKNOWN"]


def test_wiki_validate_exit_code_reflects_errors(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "00", "--content", "fine")
    ok = _run(runner, ws, "wiki", "validate", "ARENA-WIKI-00")
    assert ok.exit_code == 0

    _run(runner, ws, "wiki", "create", "--page", "01", "--knowledge-unit", "ARENA-GHOST-UNIT")
    bad = _run(runner, ws, "wiki", "validate", "ARENA-WIKI-01")
    assert bad.exit_code == 1


def test_wiki_render_writes_file(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "00", "--content", "rendered content")
    out_file = tmp_path / "out.md"
    result = _run(runner, ws, "wiki", "render", "ARENA-WIKI-00", "--to", str(out_file))
    assert result.exit_code == 0
    text = out_file.read_text(encoding="utf-8")
    assert "# 00 Status" in text
    assert "rendered content" in text


def test_wiki_show_missing_page_raises(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    result = _run(runner, ws, "wiki", "show", "ARENA-WIKI-16")
    assert result.exit_code != 0
