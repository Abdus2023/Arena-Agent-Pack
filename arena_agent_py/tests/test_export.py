"""
Phase 3: workspace export (`arena_agent.export`, `arena export`/`export
validate` CLI).

Guiding rule under test throughout: export is an artifact assembly
operation, not a second source of truth. Concretely:

  - it must call the *same* validate_*/render_* functions every other
    command uses (no export-only rule reimplementation);
  - a missing canonical Wiki page must be reported as missing, never
    synthesized as a placeholder file;
  - a WikiPage's rendered header must always reflect the *current* state
    of the records it references, never a value computed once and reused.
"""

import json
import os

from click.testing import CliRunner

from arena_agent.cli import cli
from arena_agent.export import EXPORT_SUBDIRS, build_export_plan, write_export_plan
from arena_agent.models import DecisionRecord, KnowledgeUnit, WikiPage
from arena_agent.storage import Workspace
from arena_agent.vocab import Confidence, EvidenceClass, PresenceClass, WikiPageNumber


def _run(runner, ws, *args):
    return runner.invoke(cli, ["--workspace", str(ws), *args])


def _run_json(runner, ws, *args):
    result = runner.invoke(cli, ["--workspace", str(ws), "--json", *args])
    assert result.exit_code in (0, 1), result.output
    return result, json.loads(result.output)


# ---------------------------------------------------------------------------
# build_export_plan / write_export_plan (library level)
# ---------------------------------------------------------------------------


def test_build_export_plan_on_empty_workspace_lists_all_pages_missing(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    wiki_items = [i for i in plan.items if i.kind == "wiki_page"]
    assert len(wiki_items) == 18
    assert all(i.missing for i in wiki_items)
    assert all(i.relative_path is None for i in wiki_items)
    assert all(i.markdown is None for i in wiki_items)
    assert not plan.has_errors()


def test_write_export_plan_never_writes_a_file_for_a_missing_page(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    out_dir = tmp_path / "export"
    write_export_plan(plan, out_dir)
    wiki_dir = out_dir / "wiki"
    # No page was ever created, so nothing should exist under wiki/ at all.
    assert not any(wiki_dir.glob("*.md"))


def test_write_export_plan_creates_all_declared_subdirs(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    out_dir = tmp_path / "export"
    write_export_plan(plan, out_dir)
    for sub in EXPORT_SUBDIRS:
        assert (out_dir / sub).exists()
    assert (out_dir / "index.md").exists()


def test_export_plan_renders_existing_wiki_page(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    page = WikiPage(
        id=Workspace.wiki_page_id(WikiPageNumber.STATUS),
        page_number=WikiPageNumber.STATUS,
        content="Status narrative.",
    )
    ws.save_wiki_page(page)
    plan = build_export_plan(ws)
    item = next(i for i in plan.items if i.record_id == page.id)
    assert not item.missing
    assert item.relative_path == "wiki/00-status.md"
    assert "Status narrative." in item.markdown
    assert item.markdown.startswith("# 00 Status")


def test_export_plan_header_is_derived_live_not_cached(tmp_path):
    """
    The exact regression this phase exists to prevent: a WikiPage
    referencing a Knowledge Unit whose implementation_status has since
    changed must reflect the *current* value when exported, not a value
    computed at some earlier point.
    """
    ws = Workspace(tmp_path / "ws")
    ws.init()
    unit = KnowledgeUnit(
        id="ARENA-U-1",
        meaning="x",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.HIGH,
        implementation_status=PresenceClass.PLANNED,
    )
    ws.save_knowledge_unit(unit)
    page = WikiPage(
        id=Workspace.wiki_page_id(WikiPageNumber.IMPLEMENTATION_INVENTORY),
        page_number=WikiPageNumber.IMPLEMENTATION_INVENTORY,
        content="inventory",
        knowledge_unit_ids=["ARENA-U-1"],
    )
    ws.save_wiki_page(page)

    plan_before = build_export_plan(ws)
    item_before = next(i for i in plan_before.items if i.record_id == page.id)
    assert "PLANNED" in item_before.markdown

    unit.implementation_status = PresenceClass.PRESENT
    ws.save_knowledge_unit(unit)

    plan_after = build_export_plan(ws)
    item_after = next(i for i in plan_after.items if i.record_id == page.id)
    assert "PRESENT" in item_after.markdown
    assert "PLANNED" not in item_after.markdown.split("## Content")[0]  # header cell specifically


def test_export_plan_missing_page_finding_is_info_not_error(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    missing_findings = [f for f in plan.all_findings() if f.code == "WIKI_PAGE_MISSING"]
    assert len(missing_findings) == 18
    assert all(f.severity.value == "INFO" for f in missing_findings)
    assert not plan.has_errors()


def test_export_plan_includes_every_record_kind(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_knowledge_unit(
        KnowledgeUnit(id="ARENA-U-1", meaning="m", evidence_class=EvidenceClass.OBSERVED, confidence=Confidence.HIGH)
    )
    ws.save_decision(DecisionRecord(id="ARENA-DECISION-1", question="q"))
    plan = build_export_plan(ws)
    kinds = {i.kind for i in plan.items}
    assert "knowledge_unit" in kinds
    assert "decision" in kinds
    assert "wiki_page" in kinds


def test_export_index_lists_missing_pages_distinctly_from_rendered_ones(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.STATUS), page_number=WikiPageNumber.STATUS, content="x")
    )
    plan = build_export_plan(ws)
    assert "00 [Status]" in plan.index_markdown
    assert "01 Source Corpus -- _missing" in plan.index_markdown


# ---------------------------------------------------------------------------
# ExportPlan as a self-describing artifact manifest
# ---------------------------------------------------------------------------


def test_export_plan_carries_manifest_metadata(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    assert plan.generated_at  # non-empty ISO timestamp
    assert plan.workspace_root == str((tmp_path / "ws"))
    assert plan.pack_version  # e.g. "2.0.0"


def test_export_plan_generated_at_is_iso_parseable(tmp_path):
    import datetime as dt

    ws = Workspace(tmp_path / "ws")
    ws.init()
    plan = build_export_plan(ws)
    dt.datetime.fromisoformat(plan.generated_at)  # raises if malformed


def test_export_plan_missing_items_helper(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.STATUS), page_number=WikiPageNumber.STATUS, content="x")
    )
    plan = build_export_plan(ws)
    missing = plan.missing_items()
    assert len(missing) == 17  # all but page 00
    assert all(i.missing for i in missing)
    assert all(i.kind == "wiki_page" for i in missing)


def test_export_item_and_plan_carry_no_semantic_authority_in_write_step(tmp_path):
    """
    write_export_plan must not alter, recompute, or filter findings/content
    -- it is purely a filesystem materialization of what build_export_plan
    already decided. Verify by mutating a plan's markdown directly and
    confirming the write step reproduces exactly that content, with no
    re-derivation.
    """
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.STATUS), page_number=WikiPageNumber.STATUS, content="x")
    )
    plan = build_export_plan(ws)
    item = next(i for i in plan.items if i.kind == "wiki_page" and not i.missing)
    item.markdown = "COMPLETELY REPLACED CONTENT, NOT RE-RENDERED"
    out_dir = tmp_path / "export"
    write_export_plan(plan, out_dir)
    written = (out_dir / item.relative_path).read_text()
    assert written == "COMPLETELY REPLACED CONTENT, NOT RE-RENDERED"


# ---------------------------------------------------------------------------
# index.md must make ERROR findings conspicuous, not just persist them
# ---------------------------------------------------------------------------


def test_export_index_has_no_error_banner_when_clean(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(id=Workspace.wiki_page_id(WikiPageNumber.STATUS), page_number=WikiPageNumber.STATUS, content="x")
    )
    plan = build_export_plan(ws)
    assert not plan.has_errors()
    assert "ERROR-severity validation findings" not in plan.index_markdown


def test_export_index_shows_conspicuous_error_banner_near_the_top(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(
            id=Workspace.wiki_page_id(WikiPageNumber.SOURCE_CORPUS),
            page_number=WikiPageNumber.SOURCE_CORPUS,
            content="x",
            knowledge_unit_ids=["ARENA-UNIT-GHOST"],
        )
    )
    plan = build_export_plan(ws)
    assert plan.has_errors()
    assert "ERROR-severity validation findings" in plan.index_markdown
    assert "⚠ has ERROR findings" in plan.index_markdown
    # The banner must appear before the per-record listing sections, not
    # buried only in the tail-end summary.
    banner_pos = plan.index_markdown.index("ERROR-severity validation findings")
    knowledge_units_heading_pos = plan.index_markdown.index("## Knowledge Units")
    assert banner_pos < knowledge_units_heading_pos


def test_export_index_error_marker_appears_on_the_offending_item_line(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    ws.save_wiki_page(
        WikiPage(
            id=Workspace.wiki_page_id(WikiPageNumber.SOURCE_CORPUS),
            page_number=WikiPageNumber.SOURCE_CORPUS,
            content="x",
            knowledge_unit_ids=["ARENA-UNIT-GHOST"],
        )
    )
    plan = build_export_plan(ws)
    lines = plan.index_markdown.splitlines()
    matching = [l for l in lines if "01" in l and "Source Corpus" in l]
    assert matching
    assert "⚠ has ERROR findings" in matching[0]


# ---------------------------------------------------------------------------
# CLI: `arena export` / `arena export validate`
# ---------------------------------------------------------------------------


def test_cli_export_validate_on_empty_workspace_exits_zero_and_writes_nothing(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    result = _run(runner, ws, "export", "validate")
    assert result.exit_code == 0
    assert not (tmp_path / "export").exists()


def test_cli_export_writes_index_and_subdirs(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    export_dir = tmp_path / "myexport"
    _run(runner, ws, "init")
    result = _run(runner, ws, "export", "--to", str(export_dir))
    assert result.exit_code == 0
    assert (export_dir / "index.md").exists()
    for sub in EXPORT_SUBDIRS:
        assert (export_dir / sub).exists()


def test_cli_export_default_directory_is_export(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["--workspace", str(ws), "export"])
        assert result.exit_code == 0
        assert os.path.exists("export/index.md")


def test_cli_export_never_synthesizes_missing_wiki_pages(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    export_dir = tmp_path / "export"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "00", "--content", "only this one")
    _run(runner, ws, "export", "--to", str(export_dir))
    wiki_files = sorted(p.name for p in (export_dir / "wiki").glob("*.md"))
    assert wiki_files == ["00-status.md"]  # not 18 files


def test_cli_export_json_mode_reports_missing_pages_and_counts(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "00", "--content", "x")
    _, data = _run_json(runner, ws, "export", "--to", str(tmp_path / "export"))
    assert data["record_count"] == 18
    assert len(data["missing_wiki_pages"]) == 17
    assert "ARENA-WIKI-00" not in data["missing_wiki_pages"]


def test_cli_export_validate_exits_nonzero_on_dangling_wiki_reference(tmp_path):
    runner = CliRunner()
    ws = tmp_path / "ws"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "01", "--knowledge-unit", "ARENA-UNIT-GHOST")
    result = _run(runner, ws, "export", "validate")
    assert result.exit_code == 1
    assert "WIKI_REFERENCE_NOT_FOUND" in result.output


def test_cli_export_still_writes_despite_errors(tmp_path):
    """`arena export` always writes, mirroring create/finalize semantics --
    it reports findings (including ERROR) without refusing the write."""
    runner = CliRunner()
    ws = tmp_path / "ws"
    export_dir = tmp_path / "export"
    _run(runner, ws, "init")
    _run(runner, ws, "wiki", "create", "--page", "01", "--knowledge-unit", "ARENA-UNIT-GHOST")
    result = _run(runner, ws, "export", "--to", str(export_dir))
    assert result.exit_code == 0  # export itself doesn't gate on findings
    assert (export_dir / "wiki" / "01-source-corpus.md").exists()
    content = (export_dir / "wiki" / "01-source-corpus.md").read_text()
    assert "WIKI_REFERENCE_NOT_FOUND" in content


def test_cli_export_reflects_live_knowledge_unit_state(tmp_path):
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
        "--implementation-status",
        "PLANNED",
    )
    _, units = _run_json(runner, ws, "unit", "list")
    unit_id = units[0]["id"]
    _run(runner, ws, "wiki", "create", "--page", "14", "--content", "inv", "--knowledge-unit", unit_id)

    export_dir1 = tmp_path / "exp1"
    _run(runner, ws, "export", "--to", str(export_dir1))
    text1 = (export_dir1 / "wiki" / "14-implementation-inventory.md").read_text()
    assert "PLANNED" in text1

    # Load the unit, flip its status directly through the storage layer
    # (simulating time passing / other work advancing it), and re-export.
    w = Workspace(ws)
    u = w.load_knowledge_unit(unit_id)
    u.implementation_status = PresenceClass.PRESENT
    w.save_knowledge_unit(u)

    export_dir2 = tmp_path / "exp2"
    _run(runner, ws, "export", "--to", str(export_dir2))
    text2 = (export_dir2 / "wiki" / "14-implementation-inventory.md").read_text()
    header2 = text2.split("## Content")[0]
    assert "PRESENT" in header2
    assert "PLANNED" not in header2
