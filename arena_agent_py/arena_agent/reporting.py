"""
Markdown rendering, mirroring the companion template pack
(templates/*.md). These functions take a validated record and render it as
the same document shape a human would fill in by hand, so the two paths
(hand-authored template, programmatically-generated record) stay
interchangeable and comparable.
"""

from __future__ import annotations

from .graph import KnowledgeGraph
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
from .validation import Finding, Severity, WikiHeader
from .vocab import to_pack_overall_status_label


def _bullet_list(items: list[str], empty: str = "_none_") -> str:
    if not items:
        return empty
    return "\n".join(f"- {i}" for i in items)


def _findings_section(findings: list[Finding]) -> str:
    if not findings:
        return "_No findings — passes all checked rules._"
    lines = ["| Severity | Code | Message | Ref |", "|---|---|---|---|"]
    for f in findings:
        msg = f.message.replace("|", "\\|")
        lines.append(f"| {f.severity.value} | {f.code} | {msg} | {f.ref} |")
    return "\n".join(lines)


def render_knowledge_unit(unit: KnowledgeUnit, findings: list[Finding] | None = None) -> str:
    lines = [
        f"### {unit.id}",
        "",
        f"- Meaning: {unit.meaning}",
        f"- Source location: {unit.source_location}",
        f"- Extraction classification: "
        f"{unit.extraction_class.value if unit.extraction_class else '_unset_'}",
        f"- Evidence classification: {unit.evidence_class.value}",
        f"- Confidence: {unit.confidence.value}",
        f"- Scope: {unit.scope}",
        f"- Inputs: {', '.join(unit.inputs) or '_none_'}",
        f"- Outputs: {', '.join(unit.outputs) or '_none_'}",
        f"- Affected components: {', '.join(unit.affected_components) or '_none_'}",
        f"- Dependencies: {', '.join(unit.dependencies) or '_none_'}",
        f"- Forbidden dependencies: {', '.join(unit.forbidden_dependencies) or '_none_'}",
        f"- Trust level: {unit.trust_level}",
        f"- Authority implications: {unit.authority_implications}",
        f"- Resource implications: {unit.resource_implications}",
        f"- Lifecycle state: {unit.lifecycle_state.value}",
        f"- Invariants: {', '.join(unit.invariants) or '_none_'}",
        f"- Positive cases: {', '.join(unit.positive_cases) or '_none_'}",
        f"- Negative cases: {', '.join(unit.negative_cases) or '_none_'}",
        f"- Failure modes: {', '.join(unit.failure_modes) or '_none_'}",
        f"- Verification obligation: {unit.verification_obligation}",
        f"- Implementation status: {unit.implementation_status.value}",
        f"- Evidence state: {unit.evidence_state.value}",
        f"- Open ambiguity / decision link: {', '.join(unit.open_decision_ids) or 'none'}",
        f"- Related items: {', '.join(unit.related_items) or '_none_'}",
        f"- Pack version: {unit.pack_version}",
        "",
    ]
    if findings is not None:
        lines += ["#### Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_work_item(item: WorkItem, findings: list[Finding] | None = None) -> str:
    lines = [
        f"## {item.id} — {item.title}",
        "",
        "### Responsibility",
        item.responsibility,
        "",
        "### Evidence Classification",
        f"- Classification: {item.evidence_class.value}",
        f"- Confidence: {item.confidence.value}",
        f"- Source knowledge units: {', '.join(item.source_unit_ids) or '_none_'}",
        f"- Pack version: {item.pack_version}",
        "",
        "### Inputs / Outputs",
        f"- Inputs: {', '.join(item.inputs) or '_none_'}",
        f"- Outputs: {', '.join(item.outputs) or '_none_'}",
        "",
        "### Authority",
        f"- Required authority: {item.required_authority}",
        f"- Forbidden authority: {item.forbidden_authority}",
        "",
        "### Dependencies",
        f"- Upstream: {', '.join(item.upstream) or '_none_'}",
        f"- Downstream: {', '.join(item.downstream) or '_none_'}",
        f"- Forbidden: {', '.join(item.forbidden_dependencies) or '_none_'}",
        "",
        "### State",
        f"- Lifecycle state: {item.lifecycle_state.value}",
        f"- Execution state: {item.execution_state.value}",
        f"- Authorization state: {item.authorization_state.value}",
        f"- Evidence state: {item.evidence_state.value}",
        "",
        "### Ownership",
        f"- Owner: {item.ownership.owner or '_unclaimed_'}",
        f"- Claimed at: {item.ownership.claimed_at or '_n/a_'}",
        f"- Claim status: {item.ownership.status.value}",
        "",
        "### Preconditions",
        _bullet_list(item.preconditions),
        "",
        "### Postconditions",
        _bullet_list(item.postconditions),
        "",
        "### Invariants",
        _bullet_list(item.invariants),
        "",
        "### Persistence",
        f"- Durable state: {item.durable_state or '_none_'}",
        f"- Journal: {item.journal or '_none_'}",
        f"- Recovery behavior: {item.recovery_behavior or '_none_'}",
        f"- Indeterminate states and reconciliation path: {item.indeterminate_states_reconciliation_path or '_none_'}",
        "",
        "### Verification Gates",
        "",
        "| Gate | Method | Result | Evidence |",
        "|---|---|---|---|",
    ]
    for g in item.gates:
        lines.append(
            f"| {g.gate.value} | {g.method.value if g.method else '_none_'} | "
            f"{g.result.value} | {g.evidence or '_none_'} |"
        )
    lines += [
        "",
        "### Lifecycle Log",
        "",
        "| Stage | Timestamp | Actor |",
        "|---|---|---|",
    ]
    for entry in item.lifecycle_log:
        lines.append(f"| {entry.stage} | {entry.timestamp} | {entry.actor} |")
    lines += [
        "",
        "### Open Decisions",
        _bullet_list(item.open_decision_ids, empty="none"),
        "",
    ]
    if findings is not None:
        lines += ["### Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_decision_record(decision: DecisionRecord, findings: list[Finding] | None = None) -> str:
    lines = [
        f"## {decision.id}",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Status | {decision.status.value} |",
        f"| Raised by | {decision.raised_by} |",
        f"| Raised at | {decision.raised_at} |",
        f"| Overrides Stop Condition | {decision.overrides_stop_condition or '_n/a_'} |",
        "",
        "### Question",
        decision.question,
        "",
        "### Conflicting Statements",
    ]
    if decision.conflicting_statements:
        lines += ["", "| # | Statement | Source | Classification |", "|---|---|---|---|"]
        for i, s in enumerate(decision.conflicting_statements, 1):
            lines.append(
                f"| {i} | {s.get('statement', '')} | {s.get('source', '')} | "
                f"{s.get('classification', '')} |"
            )
    else:
        lines.append("_none recorded_")

    lines += [
        "",
        "### Sources",
        _bullet_list(decision.sources),
        "",
        "### Affected Components",
        _bullet_list(decision.affected_components),
        "",
        "### Related Knowledge Unit(s)",
        _bullet_list(decision.related_unit_ids),
        "",
        "### Related Work Item(s)",
        _bullet_list(decision.related_work_item_ids),
        "",
        "### Possible Interpretations",
    ]
    if decision.options:
        lines += ["", "| Option | Description | Consequences |", "|---|---|---|"]
        for o in decision.options:
            marker = " **(chosen)**" if o.option_id == decision.chosen_option_id else ""
            lines.append(f"| {o.option_id}{marker} | {o.description} | {o.consequences} |")
    else:
        lines.append("_none recorded_")

    lines += [
        "",
        "### Current Decision",
        f"- Decision: {decision.chosen_option_id or 'UNRESOLVED'}",
        f"- Decided by: {decision.decided_by or '_n/a_'}",
        f"- Decided at: {decision.decided_at or '_n/a_'}",
        f"- Rationale: {decision.rationale}",
        "",
        "### Decision Provenance",
        decision.decision_provenance or "_none recorded_",
        "",
    ]
    if decision.overrides_stop_condition is not None:
        lines += [
            "### Override Detail",
            f"- Stop Condition overridden: #{decision.overrides_stop_condition}",
            f"- Scope: {decision.override_scope}",
            f"- Residual risk accepted: {decision.override_residual_risk}",
            "",
        ]
    if findings is not None:
        lines += ["### Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_counterexample(record: CounterexampleRecord, findings: list[Finding] | None = None) -> str:
    lines = [
        f"## {record.id}",
        "",
        f"**Stage: {record.stage.value}**",
        "",
        "### Section 1 — Observed Failure",
        f"- Source revision: {record.source_revision}",
        f"- Environment: {record.environment}",
        f"- Expected behavior: {record.expected_behavior}",
        f"- Actual behavior: {record.actual_behavior}",
        f"- First divergence: {record.first_divergence}",
        "",
        "### Section 2 — Reproducible Defect",
        f"- Seed: {record.seed}",
        f"- Generator version: {record.generator_version}",
        f"- Reproduction command: `{record.reproduction_command or ''}`",
        f"- Confirmed: {record.confirmed}",
        f"- Divergence classification: "
        f"{record.divergence_classification.value if record.divergence_classification else '_unset_'}",
        "",
    ]
    if record.minimization:
        m = record.minimization
        lines += [
            "### Section 4 — Minimization Record",
            f"- Removed structure: {m.removed_structure}",
            f"- Preserved invariant: {m.preserved_invariant}",
            "",
            "| Checklist item | Preserved? |",
            "|---|---|",
        ]
        for k, v in m.checklist.items():
            lines.append(f"| {k} | {'✅' if v else '❌'} |")
        lines.append("")
    lines += [
        "### Resolution",
        f"- Resolution status: {record.resolution_status.value}",
        f"- Fix reference: {record.fix_reference or '_none_'}",
        "",
    ]
    if findings is not None:
        lines += ["### Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_repo_audit(audit: RepoAudit, findings: list[Finding] | None = None) -> str:
    lines = [
        f"# Repository Reality Audit — {audit.id}",
        "",
        "## Audit Identity",
        f"- Repository: {audit.repository}",
        f"- Branch requested: {audit.branch_requested}",
        f"- Branch inspected: {audit.branch_inspected}",
        f"- Commit: {audit.commit if audit.commit_identity_known else 'UNKNOWN'}",
        f"- Identity failure reason: {audit.identity_failure_reason or '_n/a_'}",
        f"- Auditor: {audit.auditor}",
        f"- Timestamp: {audit.timestamp}",
        "",
        "## Inventory",
        "",
        "| Path | Kind | Classification | Coverage | Evidence |",
        "|---|---|---|---|---|",
    ]
    for item in audit.inventory:
        cov = item.coverage.value
        if item.coverage.value == "SAMPLED" and item.coverage_method:
            cov += f" ({item.coverage_method})"
        lines.append(
            f"| {item.path} | {item.kind} | {item.classification.value} | {cov} | "
            f"{item.evidence or '_none_'} |"
        )
    lines += [
        "",
        "## Claimed Architecture vs. Observed Implementation",
        "",
        "| Claimed | Source | Observed status | Evidence | Classification |",
        "|---|---|---|---|---|",
    ]
    for row in audit.claimed_vs_observed:
        lines.append(
            f"| {row.get('claim', '')} | {row.get('source', '')} | "
            f"{row.get('observed', '')} | {row.get('evidence', '')} | "
            f"{row.get('classification', '')} |"
        )
    lines += ["", "## Evidence Gaps", ""]
    for gap in audit.evidence_gaps:
        lines.append(f"- **{gap.get('id', '')}**: {gap.get('description', '')}")
    lines += ["", "## Contradictions", ""]
    for c in audit.contradictions:
        lines.append(f"- **{c.get('id', '')}**: {c.get('a', '')} vs {c.get('b', '')}")
    lines += ["", "## Recommended Next Inspection", "", audit.recommended_next_inspection, ""]
    if findings is not None:
        lines += ["## Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_change_impact(analysis: ChangeImpactAnalysis, findings: list[Finding] | None = None) -> str:
    lines = [
        f"# Change-Impact Analysis — {analysis.id}",
        "",
        f"- Target unit: {analysis.target_unit_id}",
        f"- Change description: {analysis.change_description}",
        f"- Proposed by: {analysis.proposed_by}",
        f"- Timestamp: {analysis.timestamp}",
        "",
        "## Impact Categories",
        "",
        "| Category | Classification | Details | Evidence |",
        "|---|---|---|---|",
    ]
    for cat, result in analysis.categories.items():
        lines.append(
            f"| {cat} | {result.classification.value} | {result.details or '_none_'} | "
            f"{result.evidence or '_none_'} |"
        )
    lines += [
        "",
        "## Approval Gate",
        f"- Approved: {analysis.approved}",
        f"- Conditions: {analysis.approval_conditions or '_none_'}",
        f"- Approved by: {analysis.approved_by or '_n/a_'}",
        "",
    ]
    if findings is not None:
        lines += ["## Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_final_report(report: FinalReport, findings: list[Finding] | None = None) -> str:
    """
    Render a Final Report as Markdown conformant with
    arena-final-report-template.md (v2 §40).

    ``Overall status`` is emitted twice, deliberately: once using this
    implementation's richer 4-value OverallStatus (COMPLETE /
    COMPLETE-WITH-WARNINGS / BLOCKED / INCOMPLETE), and once collapsed to
    the exact 3-value spelling (COMPLETE / PARTIAL / BLOCKED) the pack's
    own §40 template literally shows, via
    ``vocab.to_pack_overall_status_label``. This keeps the artifact
    strictly conformant to the template's own vocabulary while not losing
    the finer-grained distinction internally.
    """
    checklist_lines = [
        f"- [{'x' if v else ' '}] {k.replace('_', ' ')}"
        for k, v in report.completion_checklist.items()
    ]
    core_principle_lines = [
        f"- [{'x' if v else ' '}] {k.replace('_', ' ')}"
        for k, v in report.core_principle_checklist.items()
    ]
    pack_status = to_pack_overall_status_label(report.overall_status)
    lines = [
        "# Arena Result",
        "",
        "## Completion Contract Check",
        "",
        *checklist_lines,
        "",
        f"Overall status: **{report.overall_status.value}**"
        + (f" (§40 template spelling: `{pack_status}`)" if pack_status != report.overall_status.value else ""),
        "",
        "## Identity",
        f"- Repository: {report.repository}",
        f"- Branch: {report.branch}",
        f"- Commit: {report.commit}",
        f"- Source: {report.source}",
        f"- Related Repo-Audit ID(s): {', '.join(report.related_audit_ids) or '_none_'}",
        f"- Related Work Item ID(s): {', '.join(report.related_work_item_ids) or '_none_'}",
        f"- Related Decision ID(s): {', '.join(report.related_decision_ids) or '_none_'}",
        f"- Pack version: {report.pack_version}",
        "",
        "## Scope",
        report.scope or "_not stated_",
        "",
        "## Objective",
        report.objective,
        "",
        "## What Was Actually Observed",
        report.observed,
        "",
        "## What Was Inferred",
        report.inferred,
        "",
        "## What Was Changed",
        report.changed,
        "",
        "## What Was Not Changed",
        report.not_changed,
        "",
    ]
    if report.knowledge_units:
        lines += ["## Knowledge Units", "", "| ID | Status | Evidence |", "|---|---|---|"]
        for ku in report.knowledge_units:
            lines.append(f"| {ku.get('id', '')} | {ku.get('status', '')} | {ku.get('evidence', '')} |")
        lines.append("")
    if report.invariants:
        lines += ["## Invariants", "", "| ID | Result | Evidence |", "|---|---|---|"]
        for inv in report.invariants:
            lines.append(f"| {inv.get('id', '')} | {inv.get('result', '')} | {inv.get('evidence', '')} |")
        lines.append("")
    if report.execution:
        lines += ["## Execution", "", "| Action | Result | Evidence |", "|---|---|---|"]
        for ex in report.execution:
            lines.append(f"| {ex.get('action', '')} | {ex.get('result', '')} | {ex.get('evidence', '')} |")
        lines.append("")
    lines += [
        "## Verification",
        report.verification_summary or "_not stated_",
        "",
        "## Failures",
        _bullet_list(report.failures, empty="_none_"),
        "",
        "## Stop Conditions Triggered / Overridden",
    ]
    if report.stop_conditions_triggered:
        lines += ["", "| Condition # | Overridden? | Decision ID |", "|---|---|---|"]
        for s in report.stop_conditions_triggered:
            lines.append(
                f"| {s.get('condition')} | {s.get('overridden', False)} | "
                f"{s.get('decision_id', '')} |"
            )
    else:
        lines.append("_none triggered_")
    lines += [
        "",
        "## Open Decisions",
        _bullet_list(report.open_decision_ids, empty="_none_"),
        "",
        "## Evidence Gaps",
        _bullet_list(report.evidence_gaps, empty="_none_"),
        "",
        "## Known Limitations / Unresolved Gaps",
        _bullet_list(report.known_limitations, empty="_none_"),
        "",
    ]
    lines += [
        "## Content Scan Anomalies",
        "",
        "_Evidence about the source, not license to act on it (v2 §4.1) --"
        " not a verification conclusion or a confirmed defect._",
        "",
    ]
    if report.content_scan_anomalies:
        lines += ["| Kind | Matched Text | Context |", "|---|---|---|"]
        for a in report.content_scan_anomalies:
            context = " ".join(a.get("context", "").split())
            lines.append(f"| {a.get('kind', '')} | {a.get('matched_text', '')} | {context} |")
        lines.append("")
    else:
        lines += ["_none flagged_", ""]
    lines += [
        "## Recommended Next Action",
        report.recommended_next_action,
        "",
    ]
    if report.overall_status.value == "BLOCKED":
        lines += [
            "## Blocking Detail",
            f"- Blocking decision: {report.blocking_decision_id or '_none referenced_'}",
            f"- Blocking reason: {report.blocking_reason or '_none stated_'}",
            "",
        ]
    lines += [
        "## Core Arena Principle Self-Check (pack §43, non-normative)",
        "",
        *core_principle_lines,
        "",
    ]
    if findings is not None:
        lines += ["## Completion Contract Validation Findings", "", _findings_section(findings), ""]
    return "\n".join(lines)


def render_knowledge_graph(graph: KnowledgeGraph, findings: list[Finding] | None = None) -> str:
    """
    Render a Knowledge Graph as Markdown: node/edge tables split by
    planned-vs-observed (v2 §34's mandated subgraph separation), plus
    contradictions and divergences called out explicitly rather than
    buried in the raw edge list.
    """
    lines = ["# Knowledge Graph", ""]

    planned_nodes = [n for n in graph.nodes.values() if n.planned]
    observed_nodes = [n for n in graph.nodes.values() if not n.planned]

    def _node_table(nodes) -> str:
        if not nodes:
            return "_none_"
        rows = ["| ID | Type | Label | Provenance |", "|---|---|---|---|"]
        for n in sorted(nodes, key=lambda n: n.id):
            rows.append(f"| {n.id} | {n.node_type.value} | {n.label} | {n.provenance} |")
        return "\n".join(rows)

    lines += ["## Planned Nodes", "", _node_table(planned_nodes), ""]
    lines += ["## Observed Nodes", "", _node_table(observed_nodes), ""]

    lines += ["## Edges", ""]
    if graph.edges:
        rows = ["| ID | From | Type | To | Derived | Provenance |", "|---|---|---|---|---|---|"]
        for e in sorted(graph.edges.values(), key=lambda e: e.id):
            rows.append(
                f"| {e.id} | {e.from_id} | {e.edge_type.value} | {e.to_id} | "
                f"{e.derived} | {e.provenance} |"
            )
        lines.append("\n".join(rows))
    else:
        lines.append("_none_")
    lines.append("")

    contradictions = graph.contradictions()
    lines += ["## Contradictions (never auto-resolved)", ""]
    lines.append(_bullet_list([c.id for c in contradictions], empty="_none_"))
    lines.append("")

    divergences = graph.divergences()
    lines += ["## Planned but Not Observed", ""]
    lines.append(_bullet_list([n.id for n, _ in divergences], empty="_none_"))
    lines.append("")

    if findings is not None:
        lines += ["## Validation Findings", "", _findings_section(findings), ""]

    return "\n".join(lines)


def render_wiki_page(
    page: WikiPage,
    header: WikiHeader | None = None,
    knowledge_unit_relevance: dict[str, str] | None = None,
    inventory_rows: list[dict[str, str]] | None = None,
    findings: list[Finding] | None = None,
) -> str:
    """
    Render a WikiPage as Markdown conformant with arena-wiki-page-template.md
    (v2 §19/§38).

    ``header``: the live-derived WikiHeader (validation.derive_wiki_header),
    computed by the caller from the page's currently-referenced records.
    If omitted, the header table's classification/implementation-status/
    evidence-status/open-decisions cells render as "_not computed_" rather
    than silently showing nothing or (worse) a stale cached value -- this
    function has no way to compute it itself without touching storage.

    ``knowledge_unit_relevance``: optional ``{unit_id: relevance note}`` for
    the "Knowledge Units Referenced" table's Relevance column.

    ``inventory_rows``: optional rows for the "Implementation Inventory"
    section (only meaningful/rendered for the page 14 / Implementation
    Inventory page) -- each a dict with component/status/evidence/
    repo_audit_reference.
    """
    knowledge_unit_relevance = knowledge_unit_relevance or {}
    lines = [
        f"# {page.page_number.value} {page.title}",
        "",
        "## Required Header Block",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Scope | {page.scope or '_not stated_'} |",
        f"| Source | {page.source or '_not stated_'} |",
        f"| Repository revision (commit) | {page.repository_revision or '_not stated_'} |",
        f"| Classification (pack §4) | {', '.join(header.classifications) if header else '_not computed_'} |",
        f"| Implementation status | {', '.join(header.implementation_statuses) if header else '_not computed_'} |",
        f"| Evidence status | {', '.join(header.evidence_statuses) if header else '_not computed_'} |",
        f"| Dependencies | {', '.join(page.dependencies) or 'none'} |",
        f"| Open decisions | {', '.join(header.open_decision_ids) if header and header.open_decision_ids else 'none'} |",
        f"| Last updated | {page.last_updated} |",
        f"| Updated by | {page.updated_by or '_not stated_'} |",
        f"| Pack version | {page.pack_version} |",
        "",
        "## Content",
        "",
        page.content or "_no content authored yet_",
        "",
        "## Knowledge Units Referenced",
        "",
        "| ID | Relevance |",
        "|---|---|",
    ]
    if page.knowledge_unit_ids:
        for uid in page.knowledge_unit_ids:
            lines.append(f"| {uid} | {knowledge_unit_relevance.get(uid, '')} |")
    else:
        lines.append("| _none_ | |")
    lines.append("")

    if page.page_number.value == "14":  # Implementation Inventory
        lines += [
            "## Implementation Inventory",
            "",
            "| Component | Status | Evidence | Repo-Audit Reference |",
            "|---|---|---|---|",
        ]
        if inventory_rows:
            for row in inventory_rows:
                lines.append(
                    f"| {row.get('component', '')} | {row.get('status', '')} | "
                    f"{row.get('evidence', '')} | {row.get('repo_audit_reference', '')} |"
                )
        else:
            lines.append("| _none_ | | | |")
        lines.append("")

    lines += [
        "## Open Ambiguities",
        "",
        "| Decision ID | Question | Status |",
        "|---|---|---|",
    ]
    if page.decision_ids:
        for did in page.decision_ids:
            lines.append(f"| {did} | | |")
    else:
        lines.append("| _none_ | | |")
    lines.append("")

    lines += [
        "## Change History",
        "",
        "| Date | Change | Author | Reason | Semantic change? |",
        "|---|---|---|---|---|",
    ]
    if page.change_history:
        for entry in page.change_history:
            semantic = f"Y — {entry.related_decision_id}" if entry.is_semantic_change and entry.related_decision_id else ("Y" if entry.is_semantic_change else "N")
            lines.append(f"| {entry.timestamp} | {entry.change} | {entry.updated_by} | | {semantic} |")
    else:
        lines.append("| _none recorded_ | | | | |")
    lines.append("")

    if findings is not None:
        lines += ["## Validation Findings", "", _findings_section(findings), ""]

    return "\n".join(lines)
