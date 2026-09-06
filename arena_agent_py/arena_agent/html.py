"""
HTML presentation layer: a projection of an already-built ``ExportPlan``.

The guiding rule (explicit user instruction): **HTML must be a projection
of ExportPlan, not another export pipeline.** Concretely, no function in
this module may:

  - load JSON;
  - access ``Workspace``;
  - call any ``validate_*`` function;
  - call ``derive_wiki_header`` or any other ``derive_*`` function;
  - resolve a record ID against another record;
  - determine COMPLETE/BLOCKED/INCOMPLETE or any other status;
  - recompute a Wiki header;
  - decide whether something is missing;
  - invent content absent from the ``ExportPlan`` it was given.

Everything this module needs -- rendered Markdown, findings, missing-page
bookkeeping, generated-at/workspace/pack-version metadata, and the
relative path each artifact was (or would be) written to -- already lives
on ``ExportPlan``/``ExportItem`` (see ``arena_agent.export``). This module
converts that data to HTML and lays it out with navigation; it derives no
new facts.

Dependency direction, deliberately one level of pure conversion:

    ExportPlan
        |
        +-- item.markdown  -> markdown.markdown(...) -> HTML document body
        +-- item.findings  -> HTML status/findings block
        +-- item.missing   -> missing-page HTML representation
        +-- plan metadata  -> HTML manifest/index

Markdown -> HTML conversion is delegated to the ``markdown`` library
(already-rendered Markdown text in, HTML text out) rather than a
hand-rolled parser -- this module adds presentation (a document shell,
metadata header, findings block, navigation) around that conversion, it
does not reimplement Markdown semantics.
"""

from __future__ import annotations

from pathlib import Path

import markdown as _markdown_lib

from .export import EXPORT_SUBDIRS, KIND_TITLES, ExportItem, ExportPlan
from .validation import Finding, Severity, has_errors
from .vocab import WIKI_PAGE_TITLES, WikiPageNumber

_MARKDOWN_EXTENSIONS = ["tables", "fenced_code", "sane_lists"]

_HTML_ESCAPE = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
}


def _escape(text: str) -> str:
    out = text
    for raw, esc in _HTML_ESCAPE.items():
        out = out.replace(raw, esc)
    return out


def _markdown_to_html(markdown_text: str) -> str:
    """The one and only place Markdown text becomes an HTML fragment --
    a thin call into the ``markdown`` library, no custom parsing."""
    return _markdown_lib.markdown(markdown_text, extensions=_MARKDOWN_EXTENSIONS)


def _relative_path_for(item: ExportItem) -> str:
    """
    The HTML artifact's own path, mirroring the Markdown one 1:1 (same
    directory, ``.html`` instead of ``.md``) so the two trees stay
    trivially comparable. Never invoked for a missing item -- callers
    check ``item.missing``/``item.relative_path is None`` first.
    """
    assert item.relative_path is not None
    return item.relative_path[: -len(".md")] + ".html" if item.relative_path.endswith(".md") else item.relative_path + ".html"


def _findings_html(findings: list[Finding]) -> str:
    if not findings:
        return '<p class="findings-none">No findings.</p>'
    rows = []
    for f in findings:
        css = f"finding-{f.severity.value.lower()}"
        rows.append(
            f'<tr class="{css}"><td>{_escape(f.severity.value)}</td>'
            f"<td><code>{_escape(f.code)}</code></td>"
            f"<td>{_escape(f.message)}</td>"
            f"<td>{_escape(f.ref)}</td></tr>"
        )
    return (
        '<table class="findings">'
        "<thead><tr><th>Severity</th><th>Code</th><th>Message</th><th>Ref</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


_CSS = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
header.artifact-meta, header.plan-meta { background: #f4f4f4; border: 1px solid #ddd; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.5rem; font-size: 0.9rem; }
header.artifact-meta dl, header.plan-meta dl { display: grid; grid-template-columns: max-content 1fr; gap: 0.15rem 0.75rem; margin: 0; }
header.artifact-meta dt, header.plan-meta dt { font-weight: 600; color: #555; }
.error-banner { background: #fdecea; border: 1px solid #f5c2c0; color: #7a1f1a; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.5rem; }
.missing-banner { background: #f0f0f0; border: 1px dashed #aaa; color: #555; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.5rem; }
table { border-collapse: collapse; width: 100%; margin: 0.75rem 0; }
th, td { border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.92rem; }
th { background: #fafafa; }
table.findings tr.finding-error td { background: #fdecea; }
table.findings tr.finding-warning td { background: #fff8e1; }
table.findings tr.finding-info td { background: #eef6ff; }
.kind-badge { display: inline-block; background: #e8eef7; color: #2a4d8f; border-radius: 4px; padding: 0.1rem 0.5rem; font-size: 0.8rem; margin-left: 0.5rem; }
.error-flag { color: #b3261e; font-weight: 600; }
nav.index-nav a { display: block; padding: 0.15rem 0; }
nav.index-nav .missing { color: #888; }
a { color: #1a56db; }
"""


def _html_shell(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        f"<title>{_escape(title)}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def render_html_document(item: ExportItem) -> str:
    """
    Render one ``ExportItem`` as a standalone HTML document.

    For a missing item (``item.missing``), this renders a small
    "missing" notice using only ``item.record_id``/``item.findings`` --
    it does not invent placeholder content, it presents the fact that the
    plan already recorded: this canonical slot has no record.

    For a present item, the body is exactly ``item.markdown`` converted to
    HTML (via the ``markdown`` library), wrapped in a metadata header
    (kind, record id) and a findings block built from ``item.findings`` --
    no field on the item is read except the ones already listed in the
    module docstring's dependency diagram.
    """
    if item.missing:
        title = f"{item.record_id} (missing)"
        body = (
            f'<header class="artifact-meta"><dl>'
            f"<dt>Record</dt><dd>{_escape(item.record_id)}</dd>"
            f"<dt>Kind</dt><dd>{_escape(item.kind)}</dd>"
            f"<dt>Status</dt><dd>missing</dd>"
            "</dl></header>"
            '<div class="missing-banner">This canonical slot has no record. '
            "It is reported as missing, not rendered as a placeholder.</div>"
            f"{_findings_html(item.findings)}"
        )
        return _html_shell(title, body)

    title = item.record_id
    banner = ""
    if has_errors(item.findings):
        banner = (
            '<div class="error-banner">&#9888; This artifact has ERROR-severity '
            "validation findings -- see below.</div>"
        )
    body = (
        f'<header class="artifact-meta"><dl>'
        f"<dt>Record</dt><dd>{_escape(item.record_id)}</dd>"
        f"<dt>Kind</dt><dd>{_escape(item.kind)}</dd>"
        f"<dt>Path</dt><dd>{_escape(item.relative_path or '')}</dd>"
        "</dl></header>"
        f"{banner}"
        f"{_markdown_to_html(item.markdown or '')}"
        '<hr><h2 class="findings-heading">Findings (from ExportPlan)</h2>'
        "<p><em>Presented independently of the rendered artifact above, straight "
        "from <code>ExportItem.findings</code> -- this section does not "
        "recompute anything even if the artifact's own Markdown already "
        "includes a findings section of its own.</em></p>"
        f"{_findings_html(item.findings)}"
    )
    return _html_shell(title, body)


def render_html_index(plan: ExportPlan) -> str:
    """
    Render the HTML export index/navigation page from ``ExportPlan``
    metadata alone: ``plan.generated_at``/``plan.workspace_root``/
    ``plan.pack_version``, ``plan.items``, ``plan.missing_items()``, and
    ``plan.all_findings()``. Never touches the filesystem or the
    workspace -- every link it emits points at a path already recorded on
    an ``ExportItem`` (derived deterministically from that item's own
    ``relative_path``, never independently invented).
    """
    all_findings = plan.all_findings()
    error_count = sum(1 for f in all_findings if f.severity == Severity.ERROR)
    warning_count = sum(1 for f in all_findings if f.severity == Severity.WARNING)

    meta = (
        '<header class="plan-meta"><dl>'
        f"<dt>Generated at</dt><dd>{_escape(plan.generated_at)}</dd>"
        f"<dt>Workspace</dt><dd><code>{_escape(plan.workspace_root)}</code></dd>"
        f"<dt>Pack version</dt><dd>{_escape(plan.pack_version)}</dd>"
        f"<dt>Records</dt><dd>{len(plan.items)}</dd>"
        f"<dt>Findings</dt><dd>{error_count} ERROR, {warning_count} WARNING</dd>"
        "</dl></header>"
    )

    banner = ""
    if error_count:
        banner = (
            '<div class="error-banner">&#9888; '
            f"{error_count} record(s) in this export have ERROR-severity validation "
            "findings. Look for the highlighted entries below.</div>"
        )

    by_kind: dict[str, list[ExportItem]] = {}
    for item in plan.items:
        by_kind.setdefault(item.kind, []).append(item)

    sections = ['<nav class="index-nav">']
    for kind, title in KIND_TITLES.items():
        items = by_kind.get(kind, [])
        sections.append(f"<h2>{_escape(title)}</h2>")
        if not items:
            sections.append("<p><em>none</em></p>")
            continue
        for item in sorted(items, key=lambda i: i.record_id):
            flag = ' <span class="error-flag">&#9888; has ERROR findings</span>' if has_errors(item.findings) else ""
            html_path = _relative_path_for(item)
            sections.append(f'<a href="{_escape(html_path)}">{_escape(item.record_id)}</a>{flag}<br>')

    sections.append("<h2>Wiki Pages (canonical 00-17 index)</h2>")
    # Wiki items' own record_id already encodes their canonical page number
    # as its trailing two digits (e.g. "ARENA-WIKI-05") -- that's data the
    # plan already carries, so this is presentational parsing of a field
    # already on the item, not a re-derivation of anything.
    wiki_items_by_number = {i.record_id[-2:]: i for i in by_kind.get("wiki_page", [])}
    for number in WikiPageNumber:
        # This loop is presentational ordering over the fixed enum, not a
        # decision about what's missing -- that determination (item.missing)
        # was already made by build_export_plan and is only read here.
        matching = wiki_items_by_number.get(number.value)
        title = f"{number.value} {WIKI_PAGE_TITLES[number]}"
        if matching is None or matching.missing:
            sections.append(f'<span class="missing">{_escape(title)} -- missing</span><br>')
        else:
            flag = (
                ' <span class="error-flag">&#9888; has ERROR findings</span>'
                if has_errors(matching.findings)
                else ""
            )
            html_path = _relative_path_for(matching)
            sections.append(f'<a href="{_escape(html_path)}">{_escape(title)}</a>{flag}<br>')
    sections.append("</nav>")

    body = (
        "<h1>Arena Workspace Export</h1>"
        "<p>This export is a projection of the workspace's own validated records, "
        "rendered at a specific point in time.</p>"
        f"{meta}{banner}{''.join(sections)}"
    )
    return _html_shell("Arena Workspace Export", body)


def write_html_export(plan: ExportPlan, html_root: Path) -> list[Path]:
    """
    Write the HTML projection of ``plan`` under ``html_root``. Purely a
    filesystem materialization step, mirroring ``export.write_export_plan``
    exactly: it has no semantic authority over what gets written -- every
    item this function writes (or skips, for ``missing``) was already
    decided by whatever built ``plan``. This function never re-derives,
    re-validates, or re-renders anything; it only converts each item's
    already-rendered Markdown to HTML and lays out the same directory
    shape ``export.write_export_plan`` uses (see ``EXPORT_SUBDIRS``).

    A missing ``ExportItem`` never gets an HTML file, for the same reason
    it never gets a Markdown file in ``export.write_export_plan``: writing
    one would fabricate a page nobody authored.
    """
    html_root = Path(html_root)
    html_root.mkdir(parents=True, exist_ok=True)
    for sub in EXPORT_SUBDIRS:
        (html_root / sub).mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    index_path = html_root / "index.html"
    index_path.write_text(render_html_index(plan), encoding="utf-8")
    written.append(index_path)

    for item in plan.items:
        if item.missing or item.relative_path is None:
            continue
        path = html_root / _relative_path_for(item)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_html_document(item), encoding="utf-8")
        written.append(path)

    return written
