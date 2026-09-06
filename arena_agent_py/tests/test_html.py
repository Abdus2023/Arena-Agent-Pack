"""
Phase 4: HTML presentation (`arena_agent.html`).

Guiding rule under test throughout: HTML rendering is a *projection* of an
already-built ``ExportPlan`` -- never a second export pipeline. Concretely:

  - it must not touch ``Workspace``, JSON, ``validate_*``, or ``derive_*``;
  - it must reflect whatever is on the ``ExportPlan``/``ExportItem`` at the
    moment of rendering, including if that plan was mutated by hand after
    being built -- it must never "go back" and recompute a fresher answer;
  - navigation must come from ``ExportPlan`` fields only, never a
    filesystem walk.
"""

import ast
import inspect
import json
from pathlib import Path

from click.testing import CliRunner

import arena_agent.html as html_mod
from arena_agent.cli import cli
from arena_agent.export import ExportItem, ExportPlan
from arena_agent.html import render_html_document, render_html_index, write_html_export
from arena_agent.validation import Finding, Severity


def _run(runner, ws, *args):
    return runner.invoke(cli, ["--workspace", str(ws), *args])


def _plan(items, **kwargs):
    defaults = dict(
        generated_at="2026-01-01T00:00:00+00:00",
        workspace_root="/tmp/example-ws",
        pack_version="2.0.0",
    )
    defaults.update(kwargs)
    return ExportPlan(items=items, **defaults)


def _item(**kwargs):
    defaults = dict(
        kind="knowledge_unit",
        record_id="ARENA-U-1",
        relative_path="knowledge-units/ARENA-U-1.md",
        findings=[],
        missing=False,
        markdown="# ARENA-U-1\n\nSome **content** with a [link](other.md).\n",
    )
    defaults.update(kwargs)
    return ExportItem(**defaults)


# ---------------------------------------------------------------------------
# Static/module-boundary checks: html.py must not even *reference* the
# forbidden modules/functions, regardless of what any particular test plan
# happens to exercise at runtime.
# ---------------------------------------------------------------------------


def test_html_module_does_not_import_storage_or_validate_or_derive():
    source = Path(html_mod.__file__).read_text()
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_names.add(module.split(".")[0] if module else "")
            for alias in node.names:
                imported_names.add(alias.name)

    assert "storage" not in imported_names
    assert "Workspace" not in imported_names
    for forbidden_prefix in ("validate_", "derive_"):
        assert not any(name.startswith(forbidden_prefix) for name in imported_names), (
            f"html.py must not import any {forbidden_prefix}* function"
        )


def test_html_module_public_api_is_exactly_the_three_contracted_functions():
    public = {
        name
        for name, obj in vars(html_mod).items()
        if inspect.isfunction(obj) and obj.__module__ == html_mod.__name__ and not name.startswith("_")
    }
    assert public == {"render_html_document", "render_html_index", "write_html_export"}


# ---------------------------------------------------------------------------
# HTML rendering does not access Workspace / invoke validation / invoke
# derivation -- demonstrated behaviorally: a plan built entirely by hand,
# with no Workspace object ever constructed or imported in this test file's
# call graph, renders successfully.
# ---------------------------------------------------------------------------


def test_render_html_document_works_with_no_workspace_involved(tmp_path):
    item = _item()
    out = render_html_document(item)
    assert "<html" in out
    assert "ARENA-U-1" in out
    assert "<strong>content</strong>" in out  # markdown -> HTML transform happened
    assert "<a href=" in out  # link from the markdown body survived the transform


def test_render_html_index_works_with_no_workspace_involved():
    plan = _plan([_item()])
    out = render_html_index(plan)
    assert "<html" in out
    assert "Arena Workspace Export" in out


def test_write_html_export_works_with_no_workspace_involved(tmp_path):
    plan = _plan([_item()])
    written = write_html_export(plan, tmp_path / "html_out")
    assert len(written) == 2  # index + the one item
    assert (tmp_path / "html_out" / "index.html").exists()
    assert (tmp_path / "html_out" / "knowledge-units" / "ARENA-U-1.html").exists()


# ---------------------------------------------------------------------------
# HTML rendering reflects mutated ExportItem.markdown / findings / missing.
# ---------------------------------------------------------------------------


def test_html_rendering_reflects_mutated_export_item_markdown():
    item = _item(markdown="# Original\n")
    assert "Original" in render_html_document(item)
    item.markdown = "# Mutated Afterwards\n"
    out = render_html_document(item)
    assert "Mutated Afterwards" in out
    assert "Original" not in out


def test_html_rendering_reflects_export_item_findings():
    item = _item(findings=[])
    out_clean = render_html_document(item)
    assert 'class="error-banner"' not in out_clean

    item.findings = [Finding(severity=Severity.ERROR, code="E1", message="boom", ref="v2 \u00a71")]
    out_error = render_html_document(item)
    assert 'class="error-banner"' in out_error
    assert "boom" in out_error
    assert "E1" in out_error


def test_html_rendering_reflects_missing_true():
    item = _item(missing=True, relative_path=None, markdown=None, findings=[])
    out = render_html_document(item)
    assert "missing" in out.lower()
    # Must not have attempted to markdown-transform None into a body.
    assert "None" not in out


def test_html_rendering_does_not_call_markdown_markdown_on_none(monkeypatch):
    calls = []
    original = html_mod._markdown_lib.markdown

    def spy(text, **kwargs):
        calls.append(text)
        return original(text, **kwargs)

    monkeypatch.setattr(html_mod._markdown_lib, "markdown", spy)
    item = _item(missing=True, relative_path=None, markdown=None, findings=[])
    render_html_document(item)
    assert None not in calls


# ---------------------------------------------------------------------------
# HTML index reflects ExportPlan metadata / exposes ERROR-bearing items.
# ---------------------------------------------------------------------------


def test_html_index_reflects_export_plan_metadata():
    plan = _plan(
        [_item()],
        generated_at="2030-05-04T12:00:00+00:00",
        workspace_root="/some/specific/workspace",
        pack_version="9.9.9",
    )
    out = render_html_index(plan)
    assert "2030-05-04T12:00:00+00:00" in out
    assert "/some/specific/workspace" in out
    assert "9.9.9" in out


def test_html_index_exposes_error_bearing_items():
    clean_item = _item(record_id="ARENA-U-1", relative_path="knowledge-units/ARENA-U-1.md")
    error_item = _item(
        record_id="ARENA-U-2",
        relative_path="knowledge-units/ARENA-U-2.md",
        findings=[Finding(severity=Severity.ERROR, code="E1", message="bad", ref="")],
    )
    plan = _plan([clean_item, error_item])
    out = render_html_index(plan)
    assert "has ERROR findings" in out
    # The error flag should be associated with the offending item's link,
    # not just present anywhere on the page.
    assert out.index("ARENA-U-2") < out.index("has ERROR findings")


# ---------------------------------------------------------------------------
# HTML links correspond to ExportPlan.relative_path (.md -> .html swap).
# ---------------------------------------------------------------------------


def test_html_links_correspond_to_export_plan_relative_path():
    item = _item(record_id="ARENA-U-7", relative_path="knowledge-units/ARENA-U-7.md")
    plan = _plan([item])
    out = render_html_index(plan)
    assert 'href="knowledge-units/ARENA-U-7.html"' in out


def test_write_html_export_paths_mirror_relative_path_with_html_suffix(tmp_path):
    item = _item(record_id="ARENA-U-8", relative_path="knowledge-units/ARENA-U-8.md")
    plan = _plan([item])
    written = write_html_export(plan, tmp_path / "out")
    paths = {str(p.relative_to(tmp_path / "out")) for p in written}
    assert "knowledge-units/ARENA-U-8.html" in paths


def test_write_html_export_never_writes_a_file_for_a_missing_item(tmp_path):
    missing_item = ExportItem(
        kind="wiki_page",
        record_id="ARENA-WIKI-05",
        relative_path=None,
        missing=True,
        findings=[],
        markdown=None,
    )
    plan = _plan([missing_item])
    written = write_html_export(plan, tmp_path / "out")
    # Only the index should be written; no per-item file for the missing one.
    assert len(written) == 1
    assert written[0].name == "index.html"


# ---------------------------------------------------------------------------
# The single most important test (user's own emphasis): mutate the
# ExportPlan *after* it is built, and confirm HTML output reflects the
# mutation rather than silently reopening/recomputing anything. This is the
# HTML-layer analogue of Phase 3's write_export_plan no-re-render test.
# ---------------------------------------------------------------------------


def test_html_reflects_plan_mutated_after_being_built_not_a_fresh_recompute(tmp_path):
    item = _item(record_id="ARENA-U-9", relative_path="knowledge-units/ARENA-U-9.md", markdown="# Before\n")
    plan = _plan([item])

    # Sanity: initial render reflects the plan as originally built.
    written_before = write_html_export(plan, tmp_path / "out1")
    before_html = (tmp_path / "out1" / "knowledge-units" / "ARENA-U-9.html").read_text()
    assert "Before" in before_html

    # Mutate the plan by hand, well after it was "built" -- no Workspace,
    # no re-validation, no re-derivation involved in this mutation at all.
    plan.items[0].markdown = "# After Mutation\n"
    plan.items[0].findings = [Finding(severity=Severity.ERROR, code="E9", message="now broken", ref="")]
    plan.generated_at = "2099-01-01T00:00:00+00:00"
    plan.workspace_root = "/mutated/workspace"

    written_after = write_html_export(plan, tmp_path / "out2")
    after_html = (tmp_path / "out2" / "knowledge-units" / "ARENA-U-9.html").read_text()
    after_index = (tmp_path / "out2" / "index.html").read_text()

    assert "After Mutation" in after_html
    assert "Before" not in after_html
    assert "now broken" in after_html
    assert "error-banner" in after_html
    assert "2099-01-01T00:00:00+00:00" in after_index
    assert "/mutated/workspace" in after_index
    assert len(written_before) == len(written_after) == 2


# ---------------------------------------------------------------------------
# Basic correctness sanity checks beyond the anti-regression list.
# ---------------------------------------------------------------------------


def test_render_html_document_includes_kind_and_record_id():
    item = _item(kind="decision", record_id="ARENA-DECISION-1", relative_path="decisions/ARENA-DECISION-1.md")
    out = render_html_document(item)
    assert "ARENA-DECISION-1" in out
    assert "decision" in out


def test_render_html_index_lists_wiki_pages_including_missing_ones():
    plan = _plan([])  # no wiki items at all -> every canonical page is missing
    out = render_html_index(plan)
    assert out.count("missing") >= 18


# ---------------------------------------------------------------------------
# CLI wiring: `arena html` mirrors `arena export`'s always-write pattern
# and uses the same build_export_plan the Markdown export CLI command uses.
# ---------------------------------------------------------------------------


def test_cli_html_command_writes_index_and_item_files(tmp_path):
    ws = tmp_path / "ws"
    html_dir = tmp_path / "out"
    runner = CliRunner()
    _run(runner, ws, "init")
    result = _run(runner, ws, "html", "--to", str(html_dir))
    assert result.exit_code == 0, result.output
    assert (html_dir / "index.html").exists()


def test_cli_html_json_summary_matches_export_json_summary_fields(tmp_path):
    ws = tmp_path / "ws"
    runner = CliRunner()
    _run(runner, ws, "init")

    export_result = runner.invoke(
        cli, ["--workspace", str(ws), "--json", "export", "validate"]
    )
    html_result = runner.invoke(
        cli, ["--workspace", str(ws), "--json", "html", "--to", str(tmp_path / "html_out")]
    )
    assert export_result.exit_code in (0, 1)
    assert html_result.exit_code == 0
    export_summary = json.loads(export_result.output)
    html_summary = json.loads(html_result.output)
    for key in ("generated_at", "workspace_root", "pack_version", "record_count", "missing_wiki_pages"):
        assert key in html_summary
    # Same underlying plan-building call, so the manifest-shape fields line
    # up (timestamps will differ slightly between the two separate calls,
    # but the record/missing-page counts must not).
    assert html_summary["record_count"] == export_summary["record_count"]
    assert html_summary["missing_wiki_pages"] == export_summary["missing_wiki_pages"]


def test_no_placeholder_tests_present():
    """Guard against an accidental no-op test slipping in (bit us once in
    test_export.py); every test function in this module must have a body
    beyond a bare `pass`."""
    source = Path(__file__).read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            assert not (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)), node.name
