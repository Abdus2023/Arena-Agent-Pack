"""
Workspace export: assemble the existing per-record Markdown renderers into
a directory tree, without introducing a second interpretation of the pack.

The guiding rule (explicit user instruction): **export must be an artifact
assembly operation, not a second source of truth.** Concretely that means:

  - This module contains no new validation *rules* -- it calls the same
    ``validate_*``/``derive_wiki_header`` functions every CLI command
    already uses, and the same ``render_*`` functions every ``show``/
    ``render`` command already uses. If a rule needs to change, it changes
    in ``validation.py``/``reporting.py`` and export picks it up for free.
  - Export never manufactures a record merely to make the directory tree
    look complete. A canonical Wiki page (00-17) that was never created is
    reported as *missing*, not synthesized -- missing/invalid/blocked/not
    applicable are kept as distinct outcomes, never collapsed into a
    single "absent" bucket that would hide which one actually applies.
  - A WikiPage's header is always recomputed live from currently loaded
    records at export time (via ``derive_wiki_header``), exactly like
    ``wiki render`` -- export never serializes a stale cached header.

Pipeline (``build_export_plan`` implements this in order):

    load -> validate records -> resolve references -> validate
    cross-record invariants -> derive projections -> render -> write

``arena export validate`` runs everything through "derive projections" and
reports findings without writing anything; ``arena export`` runs the same
pipeline and then writes the artifact tree. This gives the guarantee: an
exported workspace is a projection of validated source records at a
specific point in time -- never a place where new facts get decided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import __pack_version__
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
from .reporting import (
    render_change_impact,
    render_counterexample,
    render_decision_record,
    render_final_report,
    render_knowledge_graph,
    render_knowledge_unit,
    render_repo_audit,
    render_wiki_page,
    render_work_item,
)
from .storage import RecordCorrupted, RecordNotFound, Workspace
from .validation import (
    Finding,
    Severity,
    derive_wiki_header,
    has_errors,
    validate_change_impact_analysis,
    validate_counterexample_record,
    validate_decision_record,
    validate_final_report,
    validate_knowledge_graph,
    validate_knowledge_unit,
    validate_repo_audit,
    validate_wiki_page,
    validate_wiki_references,
    validate_work_item,
)
from .vocab import WikiPageNumber

#: Export subdirectory layout. Kept as an explicit tuple (rather than
#: derived from Workspace.SUBDIRS) because the export tree's naming/shape
#: is a presentation concern, distinct from the storage layer's naming.
EXPORT_SUBDIRS = (
    "audits",
    "knowledge-units",
    "work-items",
    "decisions",
    "counterexamples",
    "impacts",
    "reports",
    "wiki",
    "graph",
)

#: Human-facing section titles per ``ExportItem.kind``, in display order.
#: Shared by the Markdown index and (deliberately re-imported, not
#: reimplemented) the HTML index in ``arena_agent.html`` -- this is naming
#: metadata, not a rule, so reusing it across presentation layers doesn't
#: violate the "HTML derives nothing" boundary.
KIND_TITLES = {
    "knowledge_unit": "Knowledge Units",
    "work_item": "Work Items",
    "decision": "Decision Records",
    "counterexample": "Counterexamples",
    "repo_audit": "Repo Audits",
    "change_impact": "Change-Impact Analyses",
    "final_report": "Final Reports",
    "graph": "Knowledge Graphs",
}


@dataclass
class ExportItem:
    """
    One artifact the export plan will (or, for `missing`, will not) write.
    This is the manifest's per-record unit -- it carries everything a
    presentation layer (Markdown writer, future HTML renderer) needs
    without ever touching the workspace itself:

      - record identity (``kind``, ``record_id``)
      - artifact type/location (``relative_path``, ``None`` if unwritable)
      - the already-rendered artifact (``markdown``, ``None`` if unwritable)
      - the findings already computed for it (never recomputed downstream)
      - ``missing``, distinct from an ERROR finding -- see ExportPlan.
    """

    kind: str  # e.g. "knowledge_unit", "wiki_page"
    record_id: str
    relative_path: Optional[str]  # None if this item cannot be rendered/written
    findings: list[Finding] = field(default_factory=list)
    missing: bool = False  # True only for a canonical slot with no record at all
    markdown: Optional[str] = None


@dataclass
class ExportPlan:
    """
    The full result of running the load -> validate -> derive -> render
    pipeline, before anything is written to disk. ``arena export validate``
    stops here; ``arena export`` additionally calls ``write_export_plan``.

    This is the artifact manifest for one export operation -- a complete,
    self-describing snapshot that a presentation layer can consume without
    re-touching the workspace, re-validating anything, or re-deriving any
    projection. In particular this is the intended contract for a future
    HTML exporter: it should take an ``ExportPlan`` (already-rendered
    Markdown + findings + missing-page bookkeeping) and produce HTML files
    from it, never re-open the workspace or re-run validation itself --
    doing so would make HTML a second implementation of the pack's
    semantics instead of a second *presentation* of the same one.

    ``generated_at``/``workspace_root``/``pack_version`` exist so the
    manifest can answer "when was this snapshot taken, from where, against
    which pack version" on its own, without a caller having to separately
    track that alongside it.
    """

    items: list[ExportItem] = field(default_factory=list)
    index_markdown: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    workspace_root: str = ""
    pack_version: str = __pack_version__

    def all_findings(self) -> list[Finding]:
        out: list[Finding] = []
        for item in self.items:
            out.extend(item.findings)
        return out

    def has_errors(self) -> bool:
        return has_errors(self.all_findings())

    def missing_items(self) -> list[ExportItem]:
        return [i for i in self.items if i.missing]


def _load_map(ids: list[str], loader) -> dict[str, object]:
    """Best-effort load of a set of IDs into a ``{id: record}`` dict, silently
    omitting any that fail to load -- the omission is itself surfaced later
    as a validation finding (e.g. WIKI_REFERENCE_NOT_FOUND), not swallowed."""
    out: dict[str, object] = {}
    for rid in ids:
        try:
            out[rid] = loader(rid)
        except (RecordNotFound, RecordCorrupted):
            pass
    return out


def build_export_plan(ws: Workspace) -> ExportPlan:
    """
    Run every record currently in ``ws`` through: load -> validate ->
    resolve references -> validate cross-record invariants -> derive
    projections -> render. Returns a plan describing what would be written
    and every finding surfaced along the way; nothing is written to disk
    by this function.

    The returned ``ExportPlan`` records ``workspace_root``/``generated_at``
    at the moment this function is called, so the manifest can always
    answer "when/where was this snapshot taken" on its own.
    """
    plan = ExportPlan(workspace_root=str(ws.root))

    # -- Knowledge Units ------------------------------------------------
    for uid in ws.list_ids("knowledge_units"):
        unit = ws.load_knowledge_unit(uid)
        findings = validate_knowledge_unit(unit)
        plan.items.append(
            ExportItem(
                kind="knowledge_unit",
                record_id=uid,
                relative_path=f"knowledge-units/{uid}.md",
                findings=findings,
                markdown=render_knowledge_unit(unit, findings),
            )
        )

    # -- Work Items -------------------------------------------------------
    for wid in ws.list_ids("work_items"):
        item = ws.load_work_item(wid)
        findings = validate_work_item(item)
        plan.items.append(
            ExportItem(
                kind="work_item",
                record_id=wid,
                relative_path=f"work-items/{wid}.md",
                findings=findings,
                markdown=render_work_item(item, findings),
            )
        )

    # -- Decision Records ---------------------------------------------------
    for did in ws.list_ids("decisions"):
        decision = ws.load_decision(did)
        findings = validate_decision_record(decision)
        plan.items.append(
            ExportItem(
                kind="decision",
                record_id=did,
                relative_path=f"decisions/{did}.md",
                findings=findings,
                markdown=render_decision_record(decision, findings),
            )
        )

    # -- Counterexamples ------------------------------------------------
    for cid in ws.list_ids("counterexamples"):
        ce = ws.load_counterexample(cid)
        findings = validate_counterexample_record(ce)
        plan.items.append(
            ExportItem(
                kind="counterexample",
                record_id=cid,
                relative_path=f"counterexamples/{cid}.md",
                findings=findings,
                markdown=render_counterexample(ce, findings),
            )
        )

    # -- Repo Audits ------------------------------------------------------
    for aid in ws.list_ids("repo_audits"):
        audit = ws.load_repo_audit(aid)
        findings = validate_repo_audit(audit)
        plan.items.append(
            ExportItem(
                kind="repo_audit",
                record_id=aid,
                relative_path=f"audits/{aid}.md",
                findings=findings,
                markdown=render_repo_audit(audit, findings),
            )
        )

    # -- Change-Impact Analyses -------------------------------------------
    for iid in ws.list_ids("change_impact"):
        analysis = ws.load_change_impact(iid)
        findings = validate_change_impact_analysis(analysis)
        plan.items.append(
            ExportItem(
                kind="change_impact",
                record_id=iid,
                relative_path=f"impacts/{iid}.md",
                findings=findings,
                markdown=render_change_impact(analysis, findings),
            )
        )

    # -- Final Reports ------------------------------------------------------
    for rid in ws.list_ids("final_reports"):
        report = ws.load_final_report(rid)
        blocking_decision = None
        if report.blocking_decision_id:
            try:
                blocking_decision = ws.load_decision(report.blocking_decision_id)
            except (RecordNotFound, RecordCorrupted):
                blocking_decision = None
        findings = validate_final_report(report, blocking_decision=blocking_decision)
        plan.items.append(
            ExportItem(
                kind="final_report",
                record_id=rid,
                relative_path=f"reports/{rid}.md",
                findings=findings,
                markdown=render_final_report(report, findings),
            )
        )

    # -- Knowledge Graphs ---------------------------------------------------
    for gid in ws.list_ids("graphs"):
        graph = ws.load_graph(gid)
        findings = validate_knowledge_graph(graph)
        plan.items.append(
            ExportItem(
                kind="graph",
                record_id=gid,
                relative_path=f"graph/{gid}.md",
                findings=findings,
                markdown=render_knowledge_graph(graph, findings),
            )
        )

    # -- Wiki Pages: closed 18-slot index, missing != invalid ---------------
    existing_pages: dict[WikiPageNumber, WikiPage] = {}
    for pid in ws.list_ids("wiki_pages"):
        page = ws.load_wiki_page(pid)
        existing_pages[page.page_number] = page

    for number in WikiPageNumber:
        page = existing_pages.get(number)
        slug = f"{number.value}-{_slugify(_title_for(number))}"
        if page is None:
            # No record exists for this canonical slot at all. This is
            # reported as MISSING, not rendered as a fake/empty page --
            # export must never manufacture a record just to make the
            # directory tree look complete.
            plan.items.append(
                ExportItem(
                    kind="wiki_page",
                    record_id=Workspace.wiki_page_id(number),
                    relative_path=None,
                    missing=True,
                    findings=[
                        Finding(
                            Severity.INFO,
                            "WIKI_PAGE_MISSING",
                            f"Canonical Wiki page {number.value} ({_title_for(number)}) has "
                            "not been created yet. This is a missing page, not an error and "
                            "not a stand-in for one -- export does not synthesize a "
                            "placeholder page to fill the slot.",
                            "v2 §38",
                        )
                    ],
                )
            )
            continue

        units = _load_map(page.knowledge_unit_ids, ws.load_knowledge_unit)
        decisions = _load_map(page.decision_ids, ws.load_decision)
        audits = _load_map(page.audit_ids, ws.load_repo_audit)
        work_items = _load_map(page.work_item_ids, ws.load_work_item)

        findings = validate_wiki_page(page) + validate_wiki_references(
            page, units, decisions, audits, work_items
        )
        # Header is always recomputed live from currently loaded records --
        # never read off a stored field, exactly like `wiki render`. This is
        # the specific mechanism that prevents a page from exporting a
        # classification/implementation-status that has since drifted from
        # the underlying Knowledge Units.
        header = derive_wiki_header(page, units.values(), decisions.values())
        plan.items.append(
            ExportItem(
                kind="wiki_page",
                record_id=page.id,
                relative_path=f"wiki/{slug}.md",
                findings=findings,
                markdown=render_wiki_page(page, header, findings=findings),
            )
        )

    plan.index_markdown = _render_index(plan, existing_pages)
    return plan


def _title_for(number: WikiPageNumber) -> str:
    from .vocab import WIKI_PAGE_TITLES

    return WIKI_PAGE_TITLES[number]


def _slugify(title: str) -> str:
    return title.lower().replace(" ", "-")


def _render_index(plan: ExportPlan, existing_pages: dict[WikiPageNumber, WikiPage]) -> str:
    lines = ["# Arena Workspace Export", ""]
    lines.append(
        "This export is a projection of the workspace's own validated records, "
        "rendered at a specific point in time -- it introduces no new facts and "
        "records no state that the source records don't already hold."
    )
    lines.append("")
    lines.append(f"- Generated at: {plan.generated_at}")
    lines.append(f"- Workspace: `{plan.workspace_root}`")
    lines.append(f"- Pack version: {plan.pack_version}")
    lines.append("")

    all_findings_early = plan.all_findings()
    error_count_early = sum(1 for f in all_findings_early if f.severity == Severity.ERROR)
    if error_count_early:
        # Deliberately conspicuous, at the very top of the file, not just a
        # per-item suffix or a tally buried at the bottom -- an exported
        # artifact containing ERROR-severity findings must not read the
        # same as a clean one at a glance. Export can (and does) still
        # write these records; it must not make them look fine.
        lines.append(
            f"> **⚠ {error_count_early} record(s) in this export have ERROR-severity "
            "validation findings.** Look for \"⚠ has ERROR findings\" below, or read "
            "each artifact's own \"Validation Findings\" section for details. This "
            "export was still written in full -- persistence and validation are "
            "separate concerns here -- but these records are not currently valid."
        )
        lines.append("")

    by_kind: dict[str, list[ExportItem]] = {}
    for item in plan.items:
        by_kind.setdefault(item.kind, []).append(item)

    for kind, title in KIND_TITLES.items():
        items = by_kind.get(kind, [])
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("_none_")
        else:
            for item in sorted(items, key=lambda i: i.record_id):
                error_flag = " **⚠ has ERROR findings**" if has_errors(item.findings) else ""
                lines.append(f"- [{item.record_id}]({item.relative_path}){error_flag}")
        lines.append("")

    lines.append("## Wiki Pages (canonical 00-17 index)")
    lines.append("")
    wiki_items = {i.record_id: i for i in by_kind.get("wiki_page", [])}
    for number in WikiPageNumber:
        page = existing_pages.get(number)
        expected_id = Workspace.wiki_page_id(number)
        item = wiki_items.get(expected_id)
        title = _title_for(number)
        if page is None or item is None or item.missing:
            lines.append(f"- {number.value} {title} -- _missing (no canonical page created)_")
        else:
            error_flag = " **⚠ has ERROR findings**" if has_errors(item.findings) else ""
            lines.append(f"- {number.value} [{title}]({item.relative_path}){error_flag}")
    lines.append("")

    all_findings = plan.all_findings()
    error_count = sum(1 for f in all_findings if f.severity == Severity.ERROR)
    warning_count = sum(1 for f in all_findings if f.severity == Severity.WARNING)
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- {len(plan.items)} record(s) considered")
    lines.append(f"- {error_count} ERROR finding(s), {warning_count} WARNING finding(s)")
    lines.append("")

    return "\n".join(lines)


def write_export_plan(plan: ExportPlan, export_root: Path) -> list[Path]:
    """
    Write an already-built ``ExportPlan`` to disk under ``export_root``.
    Only ``build_export_plan`` decides *what* gets written and with what
    content; this function performs no validation or rendering of its own
    -- it is purely the "write export" step of the pipeline.

    Missing canonical Wiki pages are, by construction, never written (an
    ``ExportItem`` with ``missing=True`` has ``relative_path=None`` and
    ``markdown=None``), so the export tree never contains a synthesized
    stand-in for a page nobody wrote.
    """
    export_root = Path(export_root)
    export_root.mkdir(parents=True, exist_ok=True)
    for sub in EXPORT_SUBDIRS:
        (export_root / sub).mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    index_path = export_root / "index.md"
    index_path.write_text(plan.index_markdown, encoding="utf-8")
    written.append(index_path)

    for item in plan.items:
        if item.missing or item.relative_path is None or item.markdown is None:
            continue
        path = export_root / item.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.markdown, encoding="utf-8")
        written.append(path)

    return written
