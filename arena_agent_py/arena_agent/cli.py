"""
Command-line interface for the Arena Agent Python implementation.

Subcommands mirror the templates/prompts in the pack:

    arena init <workspace>
    arena unit create / list / show / validate / set-state
    arena work create / claim / log / gate / list / show / validate / set-state
    arena decision create / resolve / add-option / list / show / validate
    arena ce create / promote / list / show
    arena audit create / add-item / scan-fs / list / show / validate
    arena impact create / set / approve / list / show / validate
    arena report create / check / finalize / show / validate
    arena graph create / add-node / add-edge / dependents / contradictions / divergences
    arena scan-content <path>

Output modes
------------
Every command accepts the global ``--json`` flag (before or after the
subcommand, e.g. ``arena --json unit list`` or ``arena unit list --json``
both work since it's defined on the top-level group and inherited via the
Click context). In JSON mode, each command prints exactly one JSON document
to stdout -- no color, no decorative text -- so it composes safely with
``jq`` and other scripting tools. In text mode (default), output goes
through Rich: colored tables for lists and validation findings, panels for
single-record views.

Exit codes are identical in both modes: any command whose validation
produces an ERROR-severity finding, or that fails outright, exits non-zero.
Only the *representation* of the result changes with ``--json``, never
whether the command succeeded.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Any, Optional

import click
from rich.console import Console
from rich.markdown import Markdown

from . import __pack_version__
from .content_scan import scan_text
from .graph import GraphEdge, GraphNode, KnowledgeGraph
from .ids import new_generic_id
from .models import (
    ChangeImpactAnalysis,
    CounterexampleRecord,
    DecisionRecord,
    FinalReport,
    GateResult,
    ImpactCategoryResult,
    InterpretationOption,
    InventoryItem,
    KnowledgeUnit,
    Ownership,
    RepoAudit,
    WikiChangeHistoryEntry,
    WikiPage,
    WorkItem,
    to_dict,
)
from .output import Output, OutputFormat
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
from .export import build_export_plan, write_export_plan
from .html import write_html_export
from .storage import RecordCorrupted, RecordNotFound, Workspace
from .validation import (
    Finding,
    Severity,
    check_claim_expiry,
    derive_wiki_header,
    validate_wiki_references,
    has_errors,
    validate_change_impact_analysis,
    validate_counterexample_promotion,
    validate_counterexample_record,
    validate_decision_record,
    validate_execution_transition,
    validate_final_report,
    validate_knowledge_graph,
    validate_knowledge_unit,
    validate_lifecycle_transition,
    validate_repo_audit,
    validate_wiki_page,
    validate_work_item,
)
from .vocab import (
    AuthorizationState,
    ClaimStatus,
    Confidence,
    Coverage,
    CounterexampleStage,
    DecisionStatus,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    ExtractionClass,
    GraphEdgeType,
    GraphNodeType,
    ImpactClass,
    LifecycleState,
    OverallStatus,
    PresenceClass,
    ResolutionStatus,
    TrustTier,
    VerificationGate,
    VerificationMethod,
    VerificationResult,
    WikiPageNumber,
    WorkItemStage,
    to_pack_overall_status_label,
)


# ---------------------------------------------------------------------------
# Context plumbing
# ---------------------------------------------------------------------------


class ArenaCliGroup(click.Group):
    """
    Top-level Click group that centralizes error handling for the storage
    exceptions every subcommand can raise (``RecordNotFound``,
    ``RecordCorrupted``). Individual commands used to catch these
    ad hoc -- in practice only one (``unit show``) actually did, so a
    missing or corrupted record file anywhere else produced a raw Python
    traceback instead of a clean error, including in ``--json`` mode where
    that traceback also violates the documented "exactly one JSON document
    on stdout" contract. Catching once here, at the point every subcommand
    funnels through, means new commands get this for free instead of
    depending on each author remembering to add a try/except.
    """

    def invoke(self, ctx: click.Context):
        try:
            return super().invoke(ctx)
        except click.exceptions.Exit:
            raise
        except click.ClickException:
            raise
        except (RecordNotFound, RecordCorrupted) as exc:
            out = ctx.obj.get("out") if ctx.obj else None
            message = str(exc).strip('"')
            if out is not None:
                out.error(message)
            else:  # pragma: no cover - defensive fallback if ctx.obj was never set
                click.echo(f"Error: {message}", err=True)
            ctx.exit(1)


@click.group(cls=ArenaCliGroup)
@click.option(
    "--workspace",
    "-w",
    default=".arena",
    show_default=True,
    help="Path to the Arena JSON workspace directory.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Emit machine-readable JSON instead of Rich-formatted text. "
    "Exactly one JSON document per command, safe to pipe into jq.",
)
@click.option(
    "--no-color",
    is_flag=True,
    default=False,
    help="Disable ANSI color in text mode (ignored in --json mode).",
)
@click.pass_context
def cli(ctx: click.Context, workspace: str, json_output: bool, no_color: bool) -> None:
    """Arena Agent — Python CLI implementing the Arena Agent Instructions Pack (v2)."""
    ctx.ensure_object(dict)
    ctx.obj["ws"] = Workspace(workspace)
    fmt = OutputFormat.JSON if json_output else OutputFormat.TEXT
    console = Console(no_color=no_color, highlight=False) if not json_output else None
    ctx.obj["out"] = Output(fmt=fmt, console=console) if console else Output(fmt=fmt)


def _out(ctx: click.Context) -> Output:
    return ctx.obj["out"]


def _ws(ctx: click.Context) -> Workspace:
    return ctx.obj["ws"]


def _exit_if_errors(out: Output, findings: list[Finding]) -> None:
    if has_errors(findings):
        sys.exit(1)


def _fail(out: Output, message: str, **data: Any) -> "click.exceptions.Exit":
    out.error(message, **data)
    sys.exit(1)


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize a new Arena workspace directory."""
    ws, out = _ws(ctx), _out(ctx)
    ws.init()
    out.success(f"Initialized Arena workspace at {ws.root}", workspace=str(ws.root), pack_version=__pack_version__)


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Print the pack/implementation version."""
    out = _out(ctx)
    if out.is_json:
        out.json({"pack_version": __pack_version__})
    else:
        out.console.print(__pack_version__)


# ---------------------------------------------------------------------------
# Knowledge Units
# ---------------------------------------------------------------------------


@cli.group()
def unit() -> None:
    """Manage Knowledge Units."""


@unit.command("create")
@click.option("--domain", required=True)
@click.option("--subject", required=True)
@click.option("--property", "prop", required=True)
@click.option("--meaning", required=True)
@click.option("--evidence-class", type=click.Choice([e.value for e in EvidenceClass]), required=True)
@click.option("--confidence", type=click.Choice([c.value for c in Confidence]), required=True)
@click.option("--source-location", default="")
@click.option(
    "--implementation-status",
    type=click.Choice([p.value for p in PresenceClass]),
    default=PresenceClass.UNKNOWN.value,
)
@click.option(
    "--extraction-class",
    type=click.Choice([e.value for e in ExtractionClass]),
    default=None,
    help="Wiki extraction category (v2 §19). Optional at create time, but recommended.",
)
@click.pass_context
def unit_create(
    ctx: click.Context,
    domain: str,
    subject: str,
    prop: str,
    meaning: str,
    evidence_class: str,
    confidence: str,
    source_location: str,
    implementation_status: str,
    extraction_class: Optional[str],
) -> None:
    """Create a new Knowledge Unit."""
    ws, out = _ws(ctx), _out(ctx)
    unit_id = new_generic_id(domain, subject, prop)
    u = KnowledgeUnit(
        id=unit_id,
        meaning=meaning,
        evidence_class=EvidenceClass(evidence_class),
        confidence=Confidence(confidence),
        source_location=source_location,
        implementation_status=PresenceClass(implementation_status),
        extraction_class=ExtractionClass(extraction_class) if extraction_class else None,
    )
    findings = validate_knowledge_unit(u)
    ws.save_knowledge_unit(u)
    out.findings(findings, title=f"Created {unit_id}", record_id=unit_id, also={"id": unit_id, "created": True})


@unit.command("list")
@click.pass_context
def unit_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for uid in ws.list_ids("knowledge_units"):
        u = ws.load_knowledge_unit(uid)
        rows.append(
            {
                "id": uid,
                "evidence_class": u.evidence_class.value,
                "confidence": u.confidence.value,
                "lifecycle_state": u.lifecycle_state.value,
                "implementation_status": u.implementation_status.value,
            }
        )
    out.table(
        rows,
        title="Knowledge Units",
        column_styles={"evidence_class": {"CONFLICTING": "bold red", "VERIFIED": "bold green"}},
    )


@unit.command("show")
@click.argument("unit_id")
@click.pass_context
def unit_show(ctx: click.Context, unit_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    u = ws.load_knowledge_unit(unit_id)  # RecordNotFound/RecordCorrupted handled by ArenaCliGroup
    findings = validate_knowledge_unit(u)
    if out.is_json:
        out.json({"unit": to_dict(u), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_knowledge_unit(u, findings)))


@unit.command("validate")
@click.argument("unit_id")
@click.pass_context
def unit_validate(ctx: click.Context, unit_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    u = ws.load_knowledge_unit(unit_id)
    findings = validate_knowledge_unit(u)
    out.findings(findings, title=f"Validation: {unit_id}", record_id=unit_id)
    _exit_if_errors(out, findings)


@unit.command("set-state")
@click.argument("unit_id")
@click.argument("new_state", type=click.Choice([s.value for s in LifecycleState]))
@click.pass_context
def unit_set_state(ctx: click.Context, unit_id: str, new_state: str) -> None:
    """Transition a Knowledge Unit's lifecycle_state, validating legality first."""
    ws, out = _ws(ctx), _out(ctx)
    u = ws.load_knowledge_unit(unit_id)
    target = LifecycleState(new_state)
    findings = validate_lifecycle_transition(u.lifecycle_state, target)
    if has_errors(findings):
        out.findings(findings, title=f"{unit_id}: transition rejected", record_id=unit_id)
        sys.exit(1)
    u.lifecycle_state = target
    ws.save_knowledge_unit(u)
    out.findings(findings, title=f"{unit_id}: lifecycle_state -> {target.value}", record_id=unit_id, also={"new_state": target.value})


# ---------------------------------------------------------------------------
# Work Items
# ---------------------------------------------------------------------------


@cli.group()
def work() -> None:
    """Manage Work Items."""


@work.command("create")
@click.option("--id", "work_id", required=True)
@click.option("--title", required=True)
@click.option("--responsibility", required=True)
@click.option("--source-unit", "source_units", multiple=True)
@click.pass_context
def work_create(
    ctx: click.Context, work_id: str, title: str, responsibility: str, source_units: tuple[str, ...]
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    item = WorkItem(id=work_id, title=title, responsibility=responsibility, source_unit_ids=list(source_units))
    item.log(WorkItemStage.PLAN, actor="cli")
    ws.save_work_item(item)
    out.success(f"Created work item {work_id}", id=work_id)


@work.command("claim")
@click.argument("work_id")
@click.option("--owner", required=True)
@click.pass_context
def work_claim(ctx: click.Context, work_id: str, owner: str) -> None:
    """Claim ownership of a work item before executing it (v2 §24.1)."""
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    if item.ownership.status == ClaimStatus.ACTIVE and item.ownership.owner != owner:
        _fail(
            out,
            f"Work item {work_id!r} is already actively claimed by {item.ownership.owner!r} (v2 §24.1).",
            id=work_id,
            current_owner=item.ownership.owner,
        )
        return
    from datetime import datetime, timezone

    item.ownership = Ownership(
        owner=owner,
        claimed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        status=ClaimStatus.ACTIVE,
    )
    item.log(WorkItemStage.AUTHORIZATION, actor=owner, note="claimed")
    ws.save_work_item(item)
    out.success(f"{work_id} claimed by {owner}", id=work_id, owner=owner)


@work.command("expire-claim")
@click.argument("work_id")
@click.option(
    "--max-age-hours",
    "max_age_hours",
    type=float,
    required=True,
    help=(
        "Caller-supplied expiry policy (v2 §24.1: 'per the governing "
        "operational policy, not fixed by this pack') -- an ACTIVE claim "
        "older than this many hours is treated as expired."
    ),
)
@click.pass_context
def work_expire_claim(ctx: click.Context, work_id: str, max_age_hours: float) -> None:
    """
    Apply the §24.1 claim-expiry consequence to an ACTIVE claim that has
    exceeded the supplied policy.

    This command re-checks expiry itself via ``check_claim_expiry`` (a
    pure hook) rather than trusting the caller's assertion -- it fails if
    the claim is not actually expired under ``--max-age-hours``.

    Scope boundary (conformance audit Recommendation R14, row 2.16,
    explicit user decision -- see the conformance matrix's row 2.16
    investigation note): this command mutates ``Ownership`` ONLY --
    ``ClaimStatus.ACTIVE`` -> ``EXPIRED``, preserving ``owner`` and
    ``claimed_at`` as historical evidence (§24.1: "MUST record the
    original agent's partial evidence rather than discarding it"). It
    does NOT touch ``lifecycle_state``. §24.1 also says an expired claim
    "reverts the item to `PLANNED`," but that transition is already an
    ERROR under ``validate_lifecycle_transition`` (§9.1's own canonical
    model treats `EXECUTING -> PLANNED` as `LIFECYCLE_BACKWARD_TRANSITION`,
    since `PLANNED` is not `EXECUTING`'s defined failure branch). This
    implementation does not silently resolve that pack-level tension: if
    a caller wants to also move ``lifecycle_state``, that remains a
    separate, explicit ``work set-state`` call, which will visibly
    enforce (or reject) the transition exactly as it does today -- this
    command never bypasses or special-cases it.
    """
    from datetime import timedelta

    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)

    if item.ownership.status != ClaimStatus.ACTIVE:
        _fail(
            out,
            f"Work item {work_id!r} has no ACTIVE claim to expire "
            f"(current claim status: {item.ownership.status.value}).",
            id=work_id,
            claim_status=item.ownership.status.value,
        )
        return

    expiry_findings = check_claim_expiry(item, max_age=timedelta(hours=max_age_hours))
    if not any(f.code == "CLAIM_EXPIRED" for f in expiry_findings):
        out.findings(
            expiry_findings,
            title=(
                f"{work_id}: claim by {item.ownership.owner!r} has not exceeded the "
                f"supplied policy of {max_age_hours} hour(s) -- refusing to force-expire"
            ),
            record_id=work_id,
        )
        sys.exit(1)

    original_owner = item.ownership.owner
    original_claimed_at = item.ownership.claimed_at
    item.ownership.status = ClaimStatus.EXPIRED  # owner/claimed_at preserved, never wiped
    item.log(
        WorkItemStage.AUTHORIZATION,
        actor="cli",
        note="claim expired",
        original_owner=original_owner,
        claimed_at=original_claimed_at,
        max_age_hours=max_age_hours,
    )
    ws.save_work_item(item)
    out.success(
        f"{work_id}: claim by {original_owner!r} expired (v2 §24.1)",
        id=work_id,
        owner=original_owner,
        claimed_at=original_claimed_at,
        claim_status=ClaimStatus.EXPIRED.value,
    )


@work.command("authorize")
@click.argument("work_id")
@click.option(
    "--state",
    "auth_state",
    type=click.Choice([s.value for s in AuthorizationState]),
    required=True,
    help="New authorization_state value (v2 §9.1 Appendix A.5). Independent of lifecycle_state.",
)
@click.option("--by", "authorized_by", default="", help="Who granted/denied/revoked authority.")
@click.pass_context
def work_authorize(ctx: click.Context, work_id: str, auth_state: str, authorized_by: str) -> None:
    """
    Set a work item's authorization_state independently of lifecycle_state
    (v2 §9.1: these are separate axes and MUST be recorded independently --
    an item can be lifecycle_state=EXECUTING while authorization_state=
    GRANTED). This is what makes lifecycle_state=AUTHORIZED meaningful:
    'set-state AUTHORIZED' checks that authorization_state is already
    GRANTED (see work_set_state), which requires this command to have been
    run first.
    """
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    item.authorization_state = AuthorizationState(auth_state)
    item.log(WorkItemStage.AUTHORIZATION, actor=authorized_by, note=f"authorization_state -> {auth_state}")
    ws.save_work_item(item)
    out.success(f"{work_id}: authorization_state -> {auth_state}", id=work_id, authorization_state=auth_state)


@work.command("set-execution-state")
@click.argument("work_id")
@click.option(
    "--state",
    "exec_state",
    type=click.Choice([s.value for s in ExecutionState]),
    required=True,
    help="New execution_state value (v2 §14/§15, Appendix A.3). Independent of lifecycle_state.",
)
@click.pass_context
def work_set_execution_state(ctx: click.Context, work_id: str, exec_state: str) -> None:
    """
    Set a work item's execution_state independently of lifecycle_state
    (v2 §9.1).

    v2 §15 / conformance audit Recommendation R10 (row 2.2): checks the
    proposed transition against the closed ExecutionState transition graph
    (``validate_execution_transition``) before mutating, mirroring
    ``work set-state``'s existing check-then-mutate gate for
    lifecycle_state. An illegal transition -- most notably ``ISSUED ->
    RECONCILED`` skipping ``INDETERMINATE`` -- is a blocking ERROR: the
    command exits non-zero and does not persist the change.

    This does NOT detect a *stalled* ISSUED item (no terminal follow-up at
    all); §15 defines no staleness threshold/policy for that, and this
    command does not invent one (disclosed gap, see
    ``validate_execution_transition``'s docstring).
    """
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    target = ExecutionState(exec_state)
    findings = validate_execution_transition(item.execution_state, target)
    if has_errors(findings):
        out.findings(findings, title=f"{work_id}: execution_state transition rejected", record_id=work_id)
        sys.exit(1)
    item.execution_state = target
    ws.save_work_item(item)
    out.success(f"{work_id}: execution_state -> {exec_state}", id=work_id, execution_state=exec_state)


@work.command("set-evidence-state")
@click.argument("work_id")
@click.option(
    "--state",
    "evidence_state",
    type=click.Choice([s.value for s in EvidenceState]),
    required=True,
    help="New evidence_state value (v2 §9.1, Appendix A.4). Independent of lifecycle_state.",
)
@click.pass_context
def work_set_evidence_state(ctx: click.Context, work_id: str, evidence_state: str) -> None:
    """Set a work item's evidence_state independently of lifecycle_state (v2 §9.1)."""
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    item.evidence_state = EvidenceState(evidence_state)
    ws.save_work_item(item)
    out.success(f"{work_id}: evidence_state -> {evidence_state}", id=work_id, evidence_state=evidence_state)


@work.command("set-state")
@click.argument("work_id")
@click.argument("new_state", type=click.Choice([s.value for s in LifecycleState]))
@click.pass_context
def work_set_state(ctx: click.Context, work_id: str, new_state: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    target = LifecycleState(new_state)
    findings = validate_lifecycle_transition(item.lifecycle_state, target)
    if has_errors(findings):
        out.findings(findings, title=f"{work_id}: transition rejected", record_id=work_id)
        sys.exit(1)

    # v2 §9.1: lifecycle_state is one of six independent axes. Reaching
    # AUTHORIZED/VERIFIED must not be possible purely by advancing this one
    # axis while authorization_state/evidence_state are left at their
    # collapsed defaults -- tentatively apply the transition, then run the
    # same axis-collapse checks validate_work_item uses, and reject the
    # transition (without persisting) if they fire as ERRORs. This is the
    # lifecycle-transition hard-block the decision record calls for;
    # unrelated pre-existing findings on the item do not block this specific
    # transition.
    previous_state = item.lifecycle_state
    item.lifecycle_state = target
    axis_findings = [
        f
        for f in validate_work_item(item)
        if f.code in ("AUTHORIZED_WITHOUT_GRANTED_AUTHORIZATION_STATE", "VERIFIED_WITHOUT_SUFFICIENT_EVIDENCE_STATE")
    ]
    if has_errors(axis_findings):
        item.lifecycle_state = previous_state  # reject: do not persist a collapsed-axis transition
        out.findings(axis_findings, title=f"{work_id}: transition to {target.value} rejected", record_id=work_id)
        sys.exit(1)

    stage_map = {
        LifecycleState.EXECUTING: WorkItemStage.EXECUTION,
        LifecycleState.OBSERVED: WorkItemStage.OBSERVATION,
        LifecycleState.VERIFIED: WorkItemStage.VERIFICATION,
    }
    if target in stage_map:
        item.log(stage_map[target], actor="cli")
    ws.save_work_item(item)
    out.findings(
        findings + axis_findings,
        title=f"{work_id}: lifecycle_state -> {target.value}",
        record_id=work_id,
        also={"new_state": target.value},
    )


@work.command("gate")
@click.argument("work_id")
@click.option("--gate", type=click.Choice([g.value for g in VerificationGate]), required=True)
@click.option("--method", type=click.Choice([m.value for m in VerificationMethod]))
@click.option("--result", type=click.Choice([r.value for r in VerificationResult]), required=True)
@click.option("--evidence", default="")
@click.pass_context
def work_gate(
    ctx: click.Context, work_id: str, gate: str, method: Optional[str], result: str, evidence: str
) -> None:
    """Record a verification gate result on a work item (v2 §35)."""
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    gate_enum = VerificationGate(gate)
    item.gates = [g for g in item.gates if g.gate != gate_enum]
    item.gates.append(
        GateResult(
            gate=gate_enum,
            method=VerificationMethod(method) if method else None,
            result=VerificationResult(result),
            evidence=evidence,
        )
    )
    ws.save_work_item(item)
    findings = validate_work_item(item)
    out.findings(
        findings,
        title=f"{work_id}: gate {gate} -> {result}",
        record_id=work_id,
        also={"gate": gate, "result": result},
    )


@work.command("list")
@click.pass_context
def work_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for wid in ws.list_ids("work_items"):
        item = ws.load_work_item(wid)
        rows.append(
            {
                "id": wid,
                "lifecycle_state": item.lifecycle_state.value,
                "execution_state": item.execution_state.value,
                "owner": item.ownership.owner or "-",
            }
        )
    out.table(
        rows,
        title="Work Items",
        column_styles={
            "lifecycle_state": {
                "VERIFIED": "bold green",
                "BLOCKED": "bold red",
                "FAILED": "bold red",
                "CRASHED": "bold red",
                "INVALIDATED": "bold red",
            }
        },
    )


@work.command("show")
@click.argument("work_id")
@click.pass_context
def work_show(ctx: click.Context, work_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    findings = validate_work_item(item)
    if out.is_json:
        out.json({"work_item": to_dict(item), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_work_item(item, findings)))


@work.command("validate")
@click.argument("work_id")
@click.pass_context
def work_validate(ctx: click.Context, work_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    item = ws.load_work_item(work_id)
    findings = validate_work_item(item)
    out.findings(findings, title=f"Validation: {work_id}", record_id=work_id)
    _exit_if_errors(out, findings)


# ---------------------------------------------------------------------------
# Decision Records
# ---------------------------------------------------------------------------


@cli.group()
def decision() -> None:
    """Manage Decision Records (v2 §23/§26.2)."""


def _related_units(ws: Workspace, d: DecisionRecord) -> dict[str, KnowledgeUnit]:
    """
    Best-effort load of the KnowledgeUnits named by a decision's
    related_unit_ids (v2 §26.2; Recommendation R16), as a
    ``{id: KnowledgeUnit}`` mapping -- mirrors ``_related_decisions``'s
    dict-mapping shape exactly (not a bare list), so
    ``validate_decision_record`` can tell "not supplied" apart from
    "supplied but this ID isn't in it" and flag the latter as
    ``RELATED_UNIT_NOT_FOUND``. A dangling or corrupted ID is simply
    omitted from the returned mapping here (a best-effort CLI load, not
    the validator itself) -- the omission is what lets the validator
    detect and flag it.
    """
    units: dict[str, KnowledgeUnit] = {}
    for uid in d.related_unit_ids:
        try:
            units[uid] = ws.load_knowledge_unit(uid)
        except (RecordNotFound, RecordCorrupted):
            continue
    return units


def _related_work_items_for_decision(ws: Workspace, d: DecisionRecord) -> dict[str, WorkItem]:
    """Same pattern as ``_related_units``, for ``related_work_item_ids``."""
    items: dict[str, WorkItem] = {}
    for wid in d.related_work_item_ids:
        try:
            items[wid] = ws.load_work_item(wid)
        except (RecordNotFound, RecordCorrupted):
            continue
    return items


@decision.command("create")
@click.option("--question", required=True)
@click.option("--raised-by", required=True)
@click.option("--override-stop-condition", type=click.IntRange(1, 13), default=None)
@click.option("--related-unit", "related_units", multiple=True, help="Related Knowledge Unit ID(s) (repeatable).")
@click.option("--related-work-item", "related_work_items", multiple=True, help="Related Work Item ID(s) (repeatable).")
@click.pass_context
def decision_create(
    ctx: click.Context,
    question: str,
    raised_by: str,
    override_stop_condition: Optional[int],
    related_units: tuple[str, ...],
    related_work_items: tuple[str, ...],
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    did = ws.next_decision_id()
    d = DecisionRecord(
        id=did,
        question=question,
        raised_by=raised_by,
        overrides_stop_condition=override_stop_condition,
        related_unit_ids=list(related_units),
        related_work_item_ids=list(related_work_items),
    )
    findings = validate_decision_record(d, units=_related_units(ws, d), work_items=_related_work_items_for_decision(ws, d))
    ws.save_decision(d)
    out.findings(findings, title=f"Created {did}", record_id=did, also={"id": did, "created": True})


@decision.command("add-option")
@click.argument("decision_id")
@click.option("--option-id", required=True)
@click.option("--description", required=True)
@click.option("--consequences", default="")
@click.pass_context
def decision_add_option(
    ctx: click.Context, decision_id: str, option_id: str, description: str, consequences: str
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    d = ws.load_decision(decision_id)
    d.options.append(InterpretationOption(option_id=option_id, description=description, consequences=consequences))
    ws.save_decision(d)
    out.success(f"{decision_id}: added option {option_id}", id=decision_id, option_id=option_id)


@decision.command("resolve")
@click.argument("decision_id")
@click.option("--choice", required=True)
@click.option("--decided-by", required=True)
@click.option(
    "--decided-by-trust-tier",
    type=click.Choice([t.value for t in TrustTier]),
    default=None,
    help=(
        "Which v2 §3 Trust Model tier decided_by occupies. Required, and "
        "ARENA-AGENT is rejected, if this decision overrides a Stop "
        "Condition (v2 §26.2: 'authorizing party and their role in the "
        "trust hierarchy'; 'MUST NOT be lifted by the agent's own "
        "initiative')."
    ),
)
@click.option("--rationale", default="")
@click.option("--scope", default="", help="Override scope, required if this decision overrides a Stop Condition (v2 §26.2).")
@click.option("--residual-risk", default="")
@click.pass_context
def decision_resolve(
    ctx: click.Context,
    decision_id: str,
    choice: str,
    decided_by: str,
    decided_by_trust_tier: Optional[str],
    rationale: str,
    scope: str,
    residual_risk: str,
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    d = ws.load_decision(decision_id)
    from datetime import datetime, timezone

    d.status = DecisionStatus.RESOLVED
    d.chosen_option_id = choice
    d.decided_by = decided_by
    if decided_by_trust_tier is not None:
        d.decided_by_trust_tier = TrustTier(decided_by_trust_tier)
    d.decided_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    d.rationale = rationale
    if scope:
        d.override_scope = scope
    if residual_risk:
        d.override_residual_risk = residual_risk
    findings = validate_decision_record(d, units=_related_units(ws, d), work_items=_related_work_items_for_decision(ws, d))
    ws.save_decision(d)
    out.findings(
        findings,
        title=f"{decision_id}: resolved -> {choice}",
        record_id=decision_id,
        also={"resolved_to": choice},
    )


@decision.command("list")
@click.pass_context
def decision_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for did in ws.list_ids("decisions"):
        d = ws.load_decision(did)
        rows.append({"id": did, "status": d.status.value, "question": d.question})
    out.table(
        rows,
        title="Decision Records",
        column_styles={"status": {"OPEN": "yellow", "RESOLVED": "bold green", "SUPERSEDED": "dim"}},
    )


@decision.command("show")
@click.argument("decision_id")
@click.pass_context
def decision_show(ctx: click.Context, decision_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    d = ws.load_decision(decision_id)
    findings = validate_decision_record(d, units=_related_units(ws, d), work_items=_related_work_items_for_decision(ws, d))
    if out.is_json:
        out.json({"decision": to_dict(d), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_decision_record(d, findings)))


@decision.command("validate")
@click.argument("decision_id")
@click.pass_context
def decision_validate(ctx: click.Context, decision_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    d = ws.load_decision(decision_id)
    findings = validate_decision_record(d, units=_related_units(ws, d), work_items=_related_work_items_for_decision(ws, d))
    out.findings(findings, title=f"Validation: {decision_id}", record_id=decision_id)
    _exit_if_errors(out, findings)


# ---------------------------------------------------------------------------
# Counterexamples
# ---------------------------------------------------------------------------


@cli.group()
def ce() -> None:
    """Manage Counterexample / Failure records (v2 §22)."""


@ce.command("create")
@click.option("--first-divergence", required=True)
@click.option("--expected", default="")
@click.option("--actual", default="")
@click.pass_context
def ce_create(ctx: click.Context, first_divergence: str, expected: str, actual: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    ce_id = ws.next_counterexample_id()
    record = CounterexampleRecord(id=ce_id, first_divergence=first_divergence, expected_behavior=expected, actual_behavior=actual)
    ws.save_counterexample(record)
    out.success(f"Created {ce_id} at stage RAW-DIVERGENCE", id=ce_id, stage=record.stage.value)


@ce.command("promote")
@click.argument("ce_id")
@click.argument("target_stage", type=click.Choice([s.value for s in CounterexampleStage]))
@click.option("--reproduction-command", default=None)
@click.option("--confirmed/--not-confirmed", default=None)
@click.pass_context
def ce_promote(
    ctx: click.Context, ce_id: str, target_stage: str, reproduction_command: Optional[str], confirmed: Optional[bool]
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    record = ws.load_counterexample(ce_id)
    if reproduction_command is not None:
        record.reproduction_command = reproduction_command
    if confirmed is not None:
        record.confirmed = confirmed
    target = CounterexampleStage(target_stage)
    findings = validate_counterexample_promotion(record, target)
    if has_errors(findings):
        ws.save_counterexample(record)  # persist any field updates even if promotion blocked
        out.findings(findings, title=f"{ce_id}: promotion to {target.value} rejected", record_id=ce_id)
        sys.exit(1)
    record.stage = target
    ws.save_counterexample(record)
    out.findings(
        findings,
        title=f"{ce_id}: promoted to {target.value}",
        record_id=ce_id,
        also={"stage": target.value},
    )


@ce.command("resolve")
@click.argument("ce_id")
@click.option(
    "--status",
    "resolution_status",
    type=click.Choice([s.value for s in ResolutionStatus]),
    required=True,
)
@click.option("--fix-reference", default="", help="Commit/PR/patch reference for the fix, if any.")
@click.pass_context
def ce_resolve(ctx: click.Context, ce_id: str, resolution_status: str, fix_reference: str) -> None:
    """Set resolution_status/fix_reference on a counterexample record.

    This is a plain field update, not a stage transition: resolution_status
    tracks whether/how the underlying defect was addressed, independently
    of which of the four evidentiary stages (RAW-DIVERGENCE .. MINIMIZED-
    REPRODUCER) the record has reached. Use `ce promote` for stage changes.
    """
    ws, out = _ws(ctx), _out(ctx)
    record = ws.load_counterexample(ce_id)
    record.resolution_status = ResolutionStatus(resolution_status)
    if fix_reference:
        record.fix_reference = fix_reference
    ws.save_counterexample(record)
    out.success(
        f"{ce_id}: resolution_status set to {resolution_status}",
        id=ce_id,
        resolution_status=resolution_status,
        fix_reference=record.fix_reference,
    )


@ce.command("list")
@click.pass_context
def ce_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for cid in ws.list_ids("counterexamples"):
        record = ws.load_counterexample(cid)
        rows.append({"id": cid, "stage": record.stage.value, "first_divergence": record.first_divergence})
    out.table(
        rows,
        title="Counterexamples",
        column_styles={
            "stage": {
                "RAW-DIVERGENCE": "dim",
                "OBSERVED-FAILURE": "yellow",
                "REPRODUCIBLE-DEFECT": "bold red",
                "MINIMIZED-REPRODUCER": "bold green",
            }
        },
    )


@ce.command("show")
@click.argument("ce_id")
@click.pass_context
def ce_show(ctx: click.Context, ce_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    record = ws.load_counterexample(ce_id)
    findings = validate_counterexample_record(record)
    if out.is_json:
        out.json({"counterexample": to_dict(record), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_counterexample(record, findings)))


@ce.command("validate")
@click.argument("ce_id")
@click.pass_context
def ce_validate(ctx: click.Context, ce_id: str) -> None:
    """Check that the record's populated fields satisfy its *current* stage's requirements (v2 §22.1-22.4)."""
    ws, out = _ws(ctx), _out(ctx)
    record = ws.load_counterexample(ce_id)
    findings = validate_counterexample_record(record)
    out.findings(findings, title=f"Validation: {ce_id}", record_id=ce_id)
    _exit_if_errors(out, findings)


# ---------------------------------------------------------------------------
# Repo Audits
# ---------------------------------------------------------------------------


@cli.group()
def audit() -> None:
    """Manage Repository Reality Audits (v2 §6/§28)."""


@audit.command("create")
@click.option("--repository", required=True)
@click.option("--branch", default=None)
@click.option("--commit", default=None)
@click.option("--auditor", default="")
@click.pass_context
def audit_create(ctx: click.Context, repository: str, branch: Optional[str], commit: Optional[str], auditor: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    aid = ws.next_repo_audit_id()
    a = RepoAudit(
        id=aid,
        repository=repository,
        branch_requested=branch,
        branch_inspected=branch,
        commit=commit,
        commit_identity_known=commit is not None,
        identity_failure_reason="" if commit else "commit not provided at creation time",
        auditor=auditor,
    )
    ws.save_repo_audit(a)
    out.success(f"Created {aid}", id=aid)


@audit.command("add-item")
@click.argument("audit_id")
@click.option("--path", required=True)
@click.option("--kind", required=True)
@click.option("--classification", type=click.Choice([p.value for p in PresenceClass]), required=True)
@click.option("--coverage", type=click.Choice([c.value for c in Coverage]), default=Coverage.EXHAUSTIVE.value)
@click.option("--coverage-method", default="")
@click.option("--evidence", default="")
@click.pass_context
def audit_add_item(
    ctx: click.Context,
    audit_id: str,
    path: str,
    kind: str,
    classification: str,
    coverage: str,
    coverage_method: str,
    evidence: str,
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_repo_audit(audit_id)
    a.inventory.append(
        InventoryItem(
            path=path,
            kind=kind,
            classification=PresenceClass(classification),
            coverage=Coverage(coverage),
            coverage_method=coverage_method,
            evidence=evidence,
        )
    )
    findings = validate_repo_audit(a)
    ws.save_repo_audit(a)
    out.findings(findings, title=f"{audit_id}: added inventory item {path}", record_id=audit_id, also={"path": path})


@audit.command("list")
@click.pass_context
def audit_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for aid in ws.list_ids("repo_audits"):
        a = ws.load_repo_audit(aid)
        rows.append({"id": aid, "repository": a.repository, "commit": a.commit or "UNKNOWN"})
    out.table(rows, title="Repository Reality Audits")


@audit.command("show")
@click.argument("audit_id")
@click.pass_context
def audit_show(ctx: click.Context, audit_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_repo_audit(audit_id)
    findings = validate_repo_audit(a)
    if out.is_json:
        out.json({"repo_audit": to_dict(a), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_repo_audit(a, findings)))


@audit.command("validate")
@click.argument("audit_id")
@click.pass_context
def audit_validate(ctx: click.Context, audit_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_repo_audit(audit_id)
    findings = validate_repo_audit(a)
    out.findings(findings, title=f"Validation: {audit_id}", record_id=audit_id)
    _exit_if_errors(out, findings)


@audit.command("scan-fs")
@click.argument("audit_id")
@click.option("--path", "root_path", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("--max-depth", default=2, show_default=True)
@click.pass_context
def audit_scan_fs(ctx: click.Context, audit_id: str, root_path: str, max_depth: int) -> None:
    """
    Populate an audit's inventory from an actual filesystem tree.
    Enumerates exhaustively up to --max-depth (v2 §6.1 scale/sampling
    guidance). Performs a read-only walk and never writes into the
    inspected tree.
    """
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_repo_audit(audit_id)
    root = Path(root_path)

    added = 0
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        depth = len(rel.parts)
        kind = "dir" if p.is_dir() else "file"
        if depth <= max_depth:
            a.inventory.append(
                InventoryItem(
                    path=str(rel),
                    kind=kind,
                    classification=PresenceClass.PRESENT,
                    coverage=Coverage.EXHAUSTIVE,
                    evidence=f"filesystem walk of {root_path}",
                )
            )
            added += 1
    a.repository_modified = False
    findings = validate_repo_audit(a)
    ws.save_repo_audit(a)
    note = "Items deeper than --max-depth were not enumerated. Add them explicitly or re-run with a higher --max-depth; do not assume ABSENT."
    out.findings(
        findings,
        title=f"{audit_id}: added {added} exhaustively-enumerated item(s) (depth<={max_depth})",
        record_id=audit_id,
        also={"added": added, "max_depth": max_depth, "note": note},
    )
    if not out.is_json:
        out.console.print(f"[yellow]{note}[/yellow]")


# ---------------------------------------------------------------------------
# Change-Impact Analysis
# ---------------------------------------------------------------------------


@cli.group()
def impact() -> None:
    """Manage Change-Impact Analyses (v2 §36)."""


def _impact_target_work_item_map(ws: Workspace, analysis: ChangeImpactAnalysis) -> dict[str, WorkItem]:
    """
    Best-effort lookup of ``analysis.target_unit_id`` as a WorkItem, for
    ``validate_change_impact_analysis``'s optional ``work_items`` mapping
    (v2 §36 / §24.1 open-claim conflict check, Recommendation R21). Same
    "load what's referenced, tolerate absence" pattern as
    ``_wiki_referenced_records`` -- a target that isn't a WorkItem (e.g.
    it's a KnowledgeUnit, or doesn't exist) is simply not in the returned
    mapping, so the conflict check is skipped for it rather than treated
    as either a pass or a failure.
    """
    work_items: dict[str, WorkItem] = {}
    try:
        work_items[analysis.target_unit_id] = ws.load_work_item(analysis.target_unit_id)
    except (RecordNotFound, RecordCorrupted):
        pass
    return work_items


@impact.command("create")
@click.option("--target-unit", required=True)
@click.option("--description", default="")
@click.option("--proposed-by", default="")
@click.pass_context
def impact_create(ctx: click.Context, target_unit: str, description: str, proposed_by: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    iid = ws.next_change_impact_id()
    analysis = ChangeImpactAnalysis(id=iid, target_unit_id=target_unit, change_description=description, proposed_by=proposed_by)
    ws.save_change_impact(analysis)
    out.success(f"Created {iid}", id=iid)


@impact.command("set")
@click.argument("impact_id")
@click.option("--category", required=True)
@click.option("--classification", type=click.Choice([c.value for c in ImpactClass]), required=True)
@click.option("--details", default="")
@click.option("--evidence", default="")
@click.pass_context
def impact_set(ctx: click.Context, impact_id: str, category: str, classification: str, details: str, evidence: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    analysis = ws.load_change_impact(impact_id)
    if category not in analysis.categories:
        _fail(out, f"Unknown category {category!r}. Valid: {list(analysis.categories)}")
        return
    analysis.categories[category] = ImpactCategoryResult(
        category=category, classification=ImpactClass(classification), details=details, evidence=evidence
    )
    findings = validate_change_impact_analysis(analysis, work_items=_impact_target_work_item_map(ws, analysis))
    ws.save_change_impact(analysis)
    out.findings(
        findings,
        title=f"{impact_id}: {category} -> {classification}",
        record_id=impact_id,
        also={"category": category, "classification": classification},
    )


@impact.command("approve")
@click.argument("impact_id")
@click.option("--by", "approved_by", required=True)
@click.option("--conditions", default="")
@click.pass_context
def impact_approve(ctx: click.Context, impact_id: str, approved_by: str, conditions: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    analysis = ws.load_change_impact(impact_id)
    analysis.approved = True
    analysis.approved_by = approved_by
    analysis.approval_conditions = conditions
    findings = validate_change_impact_analysis(analysis, work_items=_impact_target_work_item_map(ws, analysis))
    ws.save_change_impact(analysis)
    title = f"{impact_id}: approved" if not has_errors(findings) else f"{impact_id}: approval recorded WITH unresolved errors"
    out.findings(findings, title=title, record_id=impact_id)
    _exit_if_errors(out, findings)


@impact.command("list")
@click.pass_context
def impact_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for iid in ws.list_ids("change_impact"):
        a = ws.load_change_impact(iid)
        rows.append({"id": iid, "target_unit": a.target_unit_id, "approved": str(a.approved)})
    out.table(rows, title="Change-Impact Analyses")


@impact.command("show")
@click.argument("impact_id")
@click.pass_context
def impact_show(ctx: click.Context, impact_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_change_impact(impact_id)
    findings = validate_change_impact_analysis(a, work_items=_impact_target_work_item_map(ws, a))
    if out.is_json:
        out.json({"change_impact": to_dict(a), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_change_impact(a, findings)))


@impact.command("validate")
@click.argument("impact_id")
@click.pass_context
def impact_validate(ctx: click.Context, impact_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    a = ws.load_change_impact(impact_id)
    findings = validate_change_impact_analysis(a, work_items=_impact_target_work_item_map(ws, a))
    out.findings(findings, title=f"Validation: {impact_id}", record_id=impact_id)
    _exit_if_errors(out, findings)


# ---------------------------------------------------------------------------
# Final Report
# ---------------------------------------------------------------------------


def _load_blocking_decision(ws: Workspace, r: FinalReport) -> Optional[DecisionRecord]:
    """
    Best-effort load of the DecisionRecord a report's blocking_decision_id
    points at, so validate_final_report can verify it is actually OPEN
    rather than just present. Returns None (not an error) if there is no
    blocking_decision_id, or if it doesn't resolve -- either case is
    reported by validate_final_report itself (BLOCKING_DECISION_NOT_VERIFIED),
    not raised here, since a dangling reference is a validation finding
    about the report, not a CLI-level failure.
    """
    if not r.blocking_decision_id:
        return None
    try:
        return ws.load_decision(r.blocking_decision_id)
    except RecordNotFound:
        return None


def _related_decisions(ws: Workspace, r: FinalReport) -> dict[str, DecisionRecord]:
    """
    Best-effort load of the DecisionRecords named by a report's
    related_decision_ids (v2 §26.2; Phase 5B Recommendation R17), as a
    ``{id: DecisionRecord}`` mapping -- mirrors _wiki_referenced_records'
    dict-mapping shape exactly (not a bare list), specifically so
    validate_final_report can tell "not supplied" apart from "supplied but
    this ID isn't in it" and flag the latter as RELATED_DECISION_NOT_FOUND.
    A dangling or corrupted ID is simply omitted from the returned mapping
    here (this is a best-effort CLI load, not the validator itself) --
    the omission itself is what lets the validator detect and flag it.
    """
    out: dict[str, DecisionRecord] = {}
    for did in r.related_decision_ids:
        try:
            out[did] = ws.load_decision(did)
        except (RecordNotFound, RecordCorrupted):
            continue
    return out


@cli.group()
def report() -> None:
    """Manage Final Reports (v2 §39/§40)."""


@report.command("create")
@click.option("--id", "report_id", required=True)
@click.option("--repository", default="")
@click.option("--branch", default="")
@click.option("--commit", default="")
@click.option("--source", default="")
@click.option("--scope", default="")
@click.option("--objective", default="")
@click.option("--related-audit", "related_audits", multiple=True, help="Related Repo-Audit ID(s) (repeatable).")
@click.option("--related-work-item", "related_work_items", multiple=True, help="Related Work Item ID(s) (repeatable).")
@click.option(
    "--related-decision",
    "related_decisions",
    multiple=True,
    help="Related Decision Record ID(s) (repeatable) -- v2 §26.2; used to check overrides remain visible (R17).",
)
@click.pass_context
def report_create(
    ctx: click.Context,
    report_id: str,
    repository: str,
    branch: str,
    commit: str,
    source: str,
    scope: str,
    objective: str,
    related_audits: tuple[str, ...],
    related_work_items: tuple[str, ...],
    related_decisions: tuple[str, ...],
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    r = FinalReport(
        id=report_id,
        repository=repository,
        branch=branch,
        commit=commit,
        source=source,
        scope=scope,
        objective=objective,
        related_audit_ids=list(related_audits),
        related_work_item_ids=list(related_work_items),
        related_decision_ids=list(related_decisions),
    )
    ws.save_final_report(r)
    out.success(f"Created {report_id}", id=report_id)


@report.command("list")
@click.pass_context
def report_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for rid in ws.list_ids("final_reports"):
        r = ws.load_final_report(rid)
        rows.append({"id": rid, "overall_status": r.overall_status.value, "repository": r.repository})
    out.table(
        rows,
        title="Final Reports",
        column_styles={
            "overall_status": {
                "COMPLETE": "bold green",
                "COMPLETE-WITH-WARNINGS": "yellow",
                "BLOCKED": "bold red",
                "INCOMPLETE": "dim",
            }
        },
    )


_CHECKLIST_KEYS = list(FinalReport("x").completion_checklist.keys())
_CORE_PRINCIPLE_KEYS = list(FinalReport("x").core_principle_checklist.keys())


@report.command("check")
@click.argument("report_id")
@click.option("--item", "item_key", type=click.Choice(_CHECKLIST_KEYS))
@click.option("--value/--no-value", default=True)
@click.pass_context
def report_check(ctx: click.Context, report_id: str, item_key: str, value: bool) -> None:
    """Set a Completion Contract (v2 §39) checklist item."""
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    r.completion_checklist[item_key] = value
    ws.save_final_report(r)
    out.success(f"{report_id}: {item_key} -> {value}", id=report_id, item=item_key, value=value)


@report.command("check-principle")
@click.argument("report_id")
@click.option("--item", "item_key", type=click.Choice(_CORE_PRINCIPLE_KEYS))
@click.option("--value/--no-value", default=True)
@click.pass_context
def report_check_principle(ctx: click.Context, report_id: str, item_key: str, value: bool) -> None:
    """Set a Core Arena Principle (v2 §43, non-normative) self-check item."""
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    r.core_principle_checklist[item_key] = value
    ws.save_final_report(r)
    out.success(f"{report_id}: {item_key} -> {value}", id=report_id, item=item_key, value=value)


@report.command("set-blocking-reason")
@click.argument("report_id")
@click.option("--reason", default="")
@click.option("--decision-id", default=None, help="ID of the open Decision Record that is blocking progress.")
@click.pass_context
def report_set_blocking_reason(ctx: click.Context, report_id: str, reason: str, decision_id: Optional[str]) -> None:
    """
    Record why a report is (or would be) BLOCKED. This is a plain field
    update; it does not itself set overall_status -- use `report finalize
    --status BLOCKED` for that, which requires one of these to already be
    set (or a triggered, unoverridden Stop Condition) before it will accept
    the transition.
    """
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    if reason:
        r.blocking_reason = reason
    if decision_id:
        r.blocking_decision_id = decision_id
    ws.save_final_report(r)
    out.success(
        f"{report_id}: blocking detail recorded",
        id=report_id,
        blocking_reason=r.blocking_reason,
        blocking_decision_id=r.blocking_decision_id,
    )


@report.command("finalize")
@click.argument("report_id")
@click.option(
    "--status",
    type=click.Choice([s.value for s in OverallStatus] + ["PARTIAL"]),
    required=True,
    help="COMPLETE, COMPLETE-WITH-WARNINGS, BLOCKED, INCOMPLETE (PARTIAL accepted as a legacy alias for INCOMPLETE).",
)
@click.pass_context
def report_finalize(ctx: click.Context, report_id: str, status: str) -> None:
    """
    Set overall_status and validate it against the report's own evidence.

    This does NOT reject on a failing validation the way `work set-state`
    does for lifecycle transitions -- consistent with this project's
    create/finalize-always-persists semantics, the status is written and
    the findings (including STATUS_MASQUERADING / UNJUSTIFIED_BLOCKED_STATUS
    if applicable) are reported alongside it, with a non-zero exit code on
    ERROR so scripts can still gate on it. Persistence answers "what was
    claimed"; validation answers "was that claim demonstrated" -- conflating
    the two by silently downgrading the claim would hide the very
    discrepancy this command exists to surface.
    """
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    r.overall_status = OverallStatus.INCOMPLETE if status == "PARTIAL" else OverallStatus(status)
    findings = validate_final_report(
        r, blocking_decision=_load_blocking_decision(ws, r), decisions=_related_decisions(ws, r)
    )
    ws.save_final_report(r)
    out.findings(
        findings,
        title=f"{report_id}: overall_status -> {r.overall_status.value}",
        record_id=report_id,
        also={"overall_status": r.overall_status.value},
    )
    _exit_if_errors(out, findings)


@report.command("show")
@click.argument("report_id")
@click.pass_context
def report_show(ctx: click.Context, report_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    findings = validate_final_report(
        r, blocking_decision=_load_blocking_decision(ws, r), decisions=_related_decisions(ws, r)
    )
    if out.is_json:
        out.json(
            {
                "final_report": to_dict(r),
                "pack_status_label": to_pack_overall_status_label(r.overall_status),
                "findings": [f.__dict__ for f in _findings_as_plain(findings)],
            }
        )
    else:
        out.console.print(Markdown(render_final_report(r, findings)))


@report.command("validate")
@click.argument("report_id")
@click.pass_context
def report_validate(ctx: click.Context, report_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    r = ws.load_final_report(report_id)
    findings = validate_final_report(
        r, blocking_decision=_load_blocking_decision(ws, r), decisions=_related_decisions(ws, r)
    )
    out.findings(findings, title=f"Validation: {report_id}", record_id=report_id)
    _exit_if_errors(out, findings)


# ---------------------------------------------------------------------------
# Knowledge Graph
# ---------------------------------------------------------------------------


@cli.group()
def graph() -> None:
    """Manage the Knowledge Graph (v2 §34)."""


@graph.command("create")
@click.pass_context
def graph_create(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    gid = ws.next_graph_id()
    g = KnowledgeGraph()
    ws.save_graph(gid, g)
    out.success(f"Created {gid}", id=gid)


@graph.command("add-node")
@click.argument("graph_id")
@click.option("--id", "node_id", required=True)
@click.option("--type", "node_type", type=click.Choice([t.value for t in GraphNodeType]), required=True)
@click.option("--label", required=True)
@click.option("--planned/--observed", default=True)
@click.option("--provenance", required=True)
@click.pass_context
def graph_add_node(
    ctx: click.Context, graph_id: str, node_id: str, node_type: str, label: str, planned: bool, provenance: str
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    try:
        g.add_node(GraphNode(id=node_id, node_type=GraphNodeType(node_type), label=label, planned=planned, provenance=provenance))
    except Exception as exc:
        _fail(out, str(exc))
        return
    ws.save_graph(graph_id, g)
    out.success(f"{graph_id}: added node {node_id}", graph_id=graph_id, node_id=node_id)


@graph.command("add-edge")
@click.argument("graph_id")
@click.option("--id", "edge_id", required=True)
@click.option("--from", "from_id", required=True)
@click.option("--type", "edge_type", type=click.Choice([t.value for t in GraphEdgeType]), required=True)
@click.option("--to", "to_id", required=True)
@click.option("--provenance", required=True)
@click.option("--derived/--not-derived", default=False)
@click.pass_context
def graph_add_edge(
    ctx: click.Context,
    graph_id: str,
    edge_id: str,
    from_id: str,
    edge_type: str,
    to_id: str,
    provenance: str,
    derived: bool,
) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    try:
        g.add_edge(
            GraphEdge(
                id=edge_id, from_id=from_id, edge_type=GraphEdgeType(edge_type), to_id=to_id, provenance=provenance, derived=derived
            )
        )
    except Exception as exc:
        _fail(out, str(exc))
        return
    ws.save_graph(graph_id, g)
    out.success(f"{graph_id}: added edge {edge_id}", graph_id=graph_id, edge_id=edge_id)


@graph.command("list")
@click.pass_context
def graph_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for gid in ws.list_ids("graphs"):
        g = ws.load_graph(gid)
        rows.append({"id": gid, "nodes": len(g.nodes), "edges": len(g.edges)})
    out.table(rows, title="Knowledge Graphs")


@graph.command("show")
@click.argument("graph_id")
@click.pass_context
def graph_show(ctx: click.Context, graph_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    findings = validate_knowledge_graph(g)
    if out.is_json:
        out.json({"graph": g.to_dict(), "findings": [f.__dict__ for f in _findings_as_plain(findings)]})
    else:
        out.console.print(Markdown(render_knowledge_graph(g, findings)))


@graph.command("validate")
@click.argument("graph_id")
@click.pass_context
def graph_validate(ctx: click.Context, graph_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    findings = validate_knowledge_graph(g)
    out.findings(findings, title=f"Validation: {graph_id}", record_id=graph_id)
    _exit_if_errors(out, findings)


@graph.command("dependents")
@click.argument("graph_id")
@click.argument("node_id")
@click.pass_context
def graph_dependents(ctx: click.Context, graph_id: str, node_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    direct = g.direct_dependents(node_id)
    indirect = g.indirect_dependents(node_id)
    if out.is_json:
        out.json(
            {
                "node_id": node_id,
                "direct": [{"id": n.id, "label": n.label} for n in direct],
                "indirect": [{"id": n.id, "label": n.label} for n in indirect],
            }
        )
    else:
        out.table([{"id": n.id, "label": n.label} for n in direct], title=f"Direct dependents of {node_id}")
        out.table([{"id": n.id, "label": n.label} for n in indirect], title=f"Indirect dependents of {node_id}")


@graph.command("contradictions")
@click.argument("graph_id")
@click.pass_context
def graph_contradictions(ctx: click.Context, graph_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    rows = [{"from": e.from_id, "to": e.to_id, "provenance": e.provenance} for e in g.contradictions()]
    out.table(rows, title="Contradictions")


@graph.command("divergences")
@click.argument("graph_id")
@click.pass_context
def graph_divergences(ctx: click.Context, graph_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    g = ws.load_graph(graph_id)
    rows = [{"id": n.id, "label": n.label} for n, _ in g.divergences()]
    out.table(rows, title="Planned but not Observed")


# ---------------------------------------------------------------------------
# Wiki Pages (v2 §19 / §38, arena-wiki-page-template.md)
# ---------------------------------------------------------------------------


def _wiki_referenced_records(
    ws: Workspace, page: WikiPage
) -> tuple[dict[str, KnowledgeUnit], dict[str, DecisionRecord], dict[str, RepoAudit], dict[str, WorkItem]]:
    """
    Load (best-effort) the records a WikiPage references, keyed by ID, for
    passing into ``validate_wiki_page``/``derive_wiki_header``. A record ID
    that fails to load is simply omitted from its dict -- that omission is
    exactly what surfaces as WIKI_REFERENCE_NOT_FOUND, so no separate
    error handling is needed here.
    """
    units: dict[str, KnowledgeUnit] = {}
    for uid in page.knowledge_unit_ids:
        try:
            units[uid] = ws.load_knowledge_unit(uid)
        except (RecordNotFound, RecordCorrupted):
            pass
    decisions: dict[str, DecisionRecord] = {}
    for did in page.decision_ids:
        try:
            decisions[did] = ws.load_decision(did)
        except (RecordNotFound, RecordCorrupted):
            pass
    audits: dict[str, RepoAudit] = {}
    for aid in page.audit_ids:
        try:
            audits[aid] = ws.load_repo_audit(aid)
        except (RecordNotFound, RecordCorrupted):
            pass
    work_items: dict[str, WorkItem] = {}
    for wid in page.work_item_ids:
        try:
            work_items[wid] = ws.load_work_item(wid)
        except (RecordNotFound, RecordCorrupted):
            pass
    return units, decisions, audits, work_items


def _validate_wiki_page_full(ws: Workspace, page: WikiPage) -> list[Finding]:
    """
    Run both validation layers together: layer 1 (``validate_wiki_page``,
    the page's own local shape -- no other records involved) plus layer 2
    (``validate_wiki_references``, whether its references actually
    resolve, given the records loaded here). Every `wiki` CLI command that
    reports findings runs both layers so a caller never has to remember
    which one to invoke.
    """
    units, decisions, audits, work_items = _wiki_referenced_records(ws, page)
    return validate_wiki_page(page) + validate_wiki_references(page, units, decisions, audits, work_items)


@cli.group()
def wiki() -> None:
    """Manage Arena Wiki pages (v2 §19/§38). Fixed 18-page index (00-17)."""


@wiki.command("create")
@click.option(
    "--page",
    "page_number",
    type=click.Choice([p.value for p in WikiPageNumber]),
    required=True,
    help="Canonical page number 00-17 (v2 §38 index). The title is derived from this and cannot be set independently.",
)
@click.option("--content", default="", help="Authored prose content.")
@click.option("--scope", default="")
@click.option("--source", default="")
@click.option("--repository-revision", default="")
@click.option("--updated-by", default="")
@click.option("--knowledge-unit", "knowledge_unit_ids", multiple=True, help="Referenced Knowledge Unit ID (repeatable).")
@click.option("--decision", "decision_ids", multiple=True, help="Referenced Decision Record ID (repeatable).")
@click.option("--audit", "audit_ids", multiple=True, help="Referenced Repo Audit ID (repeatable).")
@click.option("--work-item", "work_item_ids", multiple=True, help="Referenced Work Item ID (repeatable).")
@click.option("--depends-on", "dependencies", multiple=True, help="Another WikiPage ID this page depends on (repeatable).")
@click.pass_context
def wiki_create(
    ctx: click.Context,
    page_number: str,
    content: str,
    scope: str,
    source: str,
    repository_revision: str,
    updated_by: str,
    knowledge_unit_ids: tuple[str, ...],
    decision_ids: tuple[str, ...],
    audit_ids: tuple[str, ...],
    work_item_ids: tuple[str, ...],
    dependencies: tuple[str, ...],
) -> None:
    """
    Create (or overwrite) the Wiki page for a canonical page number.

    There is exactly one WikiPage per page number (id = ARENA-WIKI-<NN>),
    not one per creation call -- re-running `create` on the same --page
    replaces its content/references but the id and title stay pinned to
    that page number. Like every other `create` in this CLI, the record is
    always persisted, even if validation reports ERROR-severity findings;
    those findings are surfaced, not used to block the write.
    """
    ws, out = _ws(ctx), _out(ctx)
    number = WikiPageNumber(page_number)
    page = WikiPage(
        id=Workspace.wiki_page_id(number),
        page_number=number,
        content=content,
        scope=scope,
        source=source,
        repository_revision=repository_revision,
        updated_by=updated_by,
        knowledge_unit_ids=list(knowledge_unit_ids),
        decision_ids=list(decision_ids),
        audit_ids=list(audit_ids),
        work_item_ids=list(work_item_ids),
        dependencies=list(dependencies),
    )
    findings = _validate_wiki_page_full(ws, page)
    ws.save_wiki_page(page)
    out.findings(
        findings,
        title=f"Created {page.id} ({page.title})",
        record_id=page.id,
        also={"id": page.id, "page_number": number.value, "title": page.title, "created": True},
    )


@wiki.command("update")
@click.argument("page_id")
@click.option("--content", default=None, help="Replace the authored prose content.")
@click.option("--scope", default=None)
@click.option("--source", default=None)
@click.option("--repository-revision", default=None)
@click.option("--updated-by", default="")
@click.option("--add-knowledge-unit", "add_units", multiple=True)
@click.option("--add-decision", "add_decisions", multiple=True)
@click.option("--add-audit", "add_audits", multiple=True)
@click.option("--add-work-item", "add_work_items", multiple=True)
@click.option("--depends-on", "add_dependencies", multiple=True, help="Add a WikiPage ID this page depends on.")
@click.option("--change", "change_note", default="", help="Free-text description of what changed, for change_history.")
@click.option("--semantic-change", is_flag=True, default=False, help="Mark this update as a semantic (not editorial) change.")
@click.option("--related-decision-id", default=None, help="Decision ID this semantic change is grounded in.")
@click.pass_context
def wiki_update(
    ctx: click.Context,
    page_id: str,
    content: Optional[str],
    scope: Optional[str],
    source: Optional[str],
    repository_revision: Optional[str],
    updated_by: str,
    add_units: tuple[str, ...],
    add_decisions: tuple[str, ...],
    add_audits: tuple[str, ...],
    add_work_items: tuple[str, ...],
    add_dependencies: tuple[str, ...],
    change_note: str,
    semantic_change: bool,
    related_decision_id: Optional[str],
) -> None:
    """
    Edit an existing Wiki page and append a change_history entry.

    This is the only way narrative/reference edits are recorded over time
    -- there is one WikiPage per page number, so updates append to
    change_history rather than creating a new dated record. Always
    persists, consistent with this CLI's create/lifecycle write semantics.
    """
    ws, out = _ws(ctx), _out(ctx)
    page = ws.load_wiki_page(page_id)
    added: list[str] = []
    if content is not None:
        page.content = content
    if scope is not None:
        page.scope = scope
    if source is not None:
        page.source = source
    if repository_revision is not None:
        page.repository_revision = repository_revision
    for uid in add_units:
        if uid not in page.knowledge_unit_ids:
            page.knowledge_unit_ids.append(uid)
            added.append(uid)
    for did in add_decisions:
        if did not in page.decision_ids:
            page.decision_ids.append(did)
            added.append(did)
    for aid in add_audits:
        if aid not in page.audit_ids:
            page.audit_ids.append(aid)
            added.append(aid)
    for wid in add_work_items:
        if wid not in page.work_item_ids:
            page.work_item_ids.append(wid)
            added.append(wid)
    for dep in add_dependencies:
        if dep not in page.dependencies:
            page.dependencies.append(dep)
    from datetime import datetime, timezone

    page.updated_by = updated_by or page.updated_by
    page.last_updated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    page.change_history.append(
        WikiChangeHistoryEntry(
            timestamp=page.last_updated,
            updated_by=updated_by,
            change=change_note,
            is_semantic_change=semantic_change,
            related_decision_id=related_decision_id,
            referenced_records_added=added,
        )
    )
    findings = _validate_wiki_page_full(ws, page)
    ws.save_wiki_page(page)
    out.findings(
        findings,
        title=f"Updated {page.id} ({page.title})",
        record_id=page.id,
        also={"id": page.id, "title": page.title},
    )


@wiki.command("list")
@click.pass_context
def wiki_list(ctx: click.Context) -> None:
    ws, out = _ws(ctx), _out(ctx)
    rows = []
    for pid in ws.list_ids("wiki_pages"):
        p = ws.load_wiki_page(pid)
        rows.append(
            {
                "id": p.id,
                "page_number": p.page_number.value,
                "title": p.title,
                "last_updated": p.last_updated,
                "has_content": bool(p.content.strip()),
            }
        )
    out.table(rows, title="Wiki Pages")


@wiki.command("show")
@click.argument("page_id")
@click.pass_context
def wiki_show(ctx: click.Context, page_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    page = ws.load_wiki_page(page_id)
    units, decisions, audits, work_items = _wiki_referenced_records(ws, page)
    findings = validate_wiki_page(page) + validate_wiki_references(page, units, decisions, audits, work_items)
    header = derive_wiki_header(page, units.values(), decisions.values())
    if out.is_json:
        out.json(
            {
                "wiki_page": to_dict(page),
                "title": page.title,
                "header": dataclasses.asdict(header),
                "findings": [f.__dict__ for f in _findings_as_plain(findings)],
            }
        )
    else:
        out.console.print(Markdown(render_wiki_page(page, header, findings=findings)))


@wiki.command("validate")
@click.argument("page_id")
@click.pass_context
def wiki_validate(ctx: click.Context, page_id: str) -> None:
    ws, out = _ws(ctx), _out(ctx)
    page = ws.load_wiki_page(page_id)
    findings = _validate_wiki_page_full(ws, page)
    out.findings(findings, title=f"Validation: {page_id}", record_id=page_id)
    _exit_if_errors(out, findings)


@wiki.command("render")
@click.argument("page_id")
@click.option("--to", "out_path", type=click.Path(dir_okay=False), default=None, help="Write rendered Markdown to this file instead of stdout.")
@click.pass_context
def wiki_render(ctx: click.Context, page_id: str, out_path: Optional[str]) -> None:
    """Render a Wiki page to Markdown matching arena-wiki-page-template.md."""
    ws, out = _ws(ctx), _out(ctx)
    page = ws.load_wiki_page(page_id)
    units, decisions, audits, work_items = _wiki_referenced_records(ws, page)
    header = derive_wiki_header(page, units.values(), decisions.values())
    findings = validate_wiki_page(page) + validate_wiki_references(page, units, decisions, audits, work_items)
    markdown = render_wiki_page(page, header, findings=findings)
    if out_path:
        Path(out_path).write_text(markdown, encoding="utf-8")
        out.success(f"Rendered {page_id} -> {out_path}", id=page_id, path=out_path)
    elif out.is_json:
        out.json({"id": page_id, "markdown": markdown})
    else:
        out.console.print(Markdown(markdown))


# ---------------------------------------------------------------------------
# Workspace export (v2 §37/§38 companion templates -- artifact assembly only)
# ---------------------------------------------------------------------------


def _export_summary(plan) -> dict[str, Any]:
    findings = plan.all_findings()
    return {
        "generated_at": plan.generated_at,
        "workspace_root": plan.workspace_root,
        "pack_version": plan.pack_version,
        "record_count": len(plan.items),
        "missing_wiki_pages": sorted(i.record_id for i in plan.items if i.kind == "wiki_page" and i.missing),
        "has_errors": has_errors(findings),
        "error_count": sum(1 for f in findings if f.severity == Severity.ERROR),
        "warning_count": sum(1 for f in findings if f.severity == Severity.WARNING),
    }


@cli.group(invoke_without_command=True)
@click.option(
    "--to",
    "export_dir",
    type=click.Path(file_okay=False),
    default="export",
    help="Directory to write the export tree into (created if missing). Default: ./export.",
)
@click.pass_context
def export(ctx: click.Context, export_dir: str) -> None:
    """
    Assemble the existing per-record renderers into a Markdown artifact
    tree. This is deliberately an *assembly* operation, not a second
    source of truth -- it runs the same validate_*/render_* functions
    every other command uses and writes their output to
    export/<kind>/<id>.md, plus export/index.md and export/wiki/<NN>-*.md
    for the closed 18-page canonical index. A canonical Wiki page that was
    never created shows up as missing in the index, never as a
    synthesized placeholder.

    Bare `arena export` builds the plan and writes it (always writes,
    consistent with this CLI's create/finalize always-persist semantics --
    findings, including ERROR severity, are reported alongside the write,
    not used to block it). Use `arena export validate` first for a
    pre-flight check that writes nothing.
    """
    ctx.ensure_object(dict)
    ctx.obj["export_dir"] = export_dir
    if ctx.invoked_subcommand is not None:
        return
    ws, out = _ws(ctx), _out(ctx)
    plan = build_export_plan(ws)
    written = write_export_plan(plan, Path(export_dir))
    findings = plan.all_findings()
    summary = _export_summary(plan)
    if out.is_json:
        out.json(
            {
                **summary,
                "export_dir": str(export_dir),
                "files_written": len(written),
                "findings": [f.__dict__ for f in _findings_as_plain(findings)],
            }
        )
    else:
        out.findings(findings, title=f"Exported to {export_dir}")
        out.console.print(
            f"[bold green]{len(written)} file(s) written to {export_dir}[/bold green] "
            f"({summary['record_count']} record(s), {len(summary['missing_wiki_pages'])} "
            "canonical Wiki page(s) missing)."
        )


@export.command("validate")
@click.pass_context
def export_validate(ctx: click.Context) -> None:
    """
    Run the full load -> validate -> resolve references -> validate
    cross-record invariants -> derive projections pipeline and report
    findings, without writing anything to disk. Use this to check whether
    an export would be clean before actually producing one.
    """
    ws, out = _ws(ctx), _out(ctx)
    plan = build_export_plan(ws)
    findings = plan.all_findings()
    if out.is_json:
        out.json(
            {
                **_export_summary(plan),
                "findings": [f.__dict__ for f in _findings_as_plain(findings)],
            }
        )
    else:
        out.findings(findings, title="Export validation")
        summary = _export_summary(plan)
        out.console.print(
            f"[bold]{summary['record_count']}[/bold] record(s) considered; "
            f"{len(summary['missing_wiki_pages'])} canonical Wiki page(s) missing."
        )
        if summary["missing_wiki_pages"]:
            out.console.print(f"  missing: {', '.join(summary['missing_wiki_pages'])}")
    _exit_if_errors(out, findings)


@cli.command("html")
@click.option(
    "--to",
    "html_dir",
    type=click.Path(file_okay=False),
    default="export-html",
    help="Directory to write the HTML artifact tree into (created if missing). Default: ./export-html.",
)
@click.pass_context
def html_export(ctx: click.Context, html_dir: str) -> None:
    """
    Build the same export plan `arena export` builds, then render it as a
    browsable HTML tree instead of (or alongside) the Markdown one.

    This is a pure presentation step over an already-built `ExportPlan` --
    it calls `build_export_plan` once, the same function `arena export`
    calls, and then hands the resulting plan to `arena_agent.html`, which
    reads only `ExportPlan`/`ExportItem` fields (already-rendered
    Markdown, findings, missing flags, manifest metadata). It does not
    revalidate, rederive, or reinterpret anything -- if `arena export
    validate` reports something, this command's output reports the exact
    same thing, just as HTML instead of Markdown.

    Like bare `arena export`, this always writes (findings, including
    ERROR severity, are reported alongside the write, not used to block
    it). Use `arena export validate` first for a pre-flight check.
    """
    ws, out = _ws(ctx), _out(ctx)
    plan = build_export_plan(ws)
    written = write_html_export(plan, Path(html_dir))
    findings = plan.all_findings()
    summary = _export_summary(plan)
    if out.is_json:
        out.json(
            {
                **summary,
                "html_dir": str(html_dir),
                "files_written": len(written),
                "findings": [f.__dict__ for f in _findings_as_plain(findings)],
            }
        )
    else:
        out.findings(findings, title=f"HTML export written to {html_dir}")
        out.console.print(
            f"[bold green]{len(written)} file(s) written to {html_dir}[/bold green] "
            f"({summary['record_count']} record(s), {len(summary['missing_wiki_pages'])} "
            "canonical Wiki page(s) missing)."
        )


# ---------------------------------------------------------------------------
# Content scanning (Ingested Content Contract, v2 §4.1)
# ---------------------------------------------------------------------------


@cli.command("scan-content")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--attach-to-report",
    "attach_to_report",
    default=None,
    help=(
        "FinalReport ID (v2 §4.1) to append this scan's flags to, as "
        "content_scan_anomalies entries. Explicit only -- running "
        "scan-content without this option never touches any report "
        "(conformance audit Recommendation R2). Fails if the report "
        "does not exist; never creates one."
    ),
)
@click.pass_context
def scan_content(ctx: click.Context, path: str, attach_to_report: Optional[str]) -> None:
    """Scan a file for anti-pattern phrases / directive-shaped text (v2 §4.1)."""
    ws, out = _ws(ctx), _out(ctx)
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    flags = scan_text(text)

    attached_count = None
    if attach_to_report is not None:
        # RecordNotFound (report doesn't exist) propagates to
        # ArenaCliGroup's top-level handler -- see unit_set_state's
        # equivalent comment above for the established convention.
        report = ws.load_final_report(attach_to_report)
        new_entries = [
            {"kind": f.kind, "matched_text": f.matched_text, "context": f.context} for f in flags
        ]
        # Zero flags -> nothing appended; never manufacture a placeholder
        # anomaly merely because a (clean) scan was attached.
        report.content_scan_anomalies.extend(new_entries)
        ws.save_final_report(report)
        attached_count = len(new_entries)

    if out.is_json:
        payload = {
            "path": path,
            "flag_count": len(flags),
            "flags": [
                {"kind": f.kind, "matched_text": f.matched_text, "start": f.start, "end": f.end, "context": f.context}
                for f in flags
            ],
        }
        if attached_count is not None:
            payload["attached_to_report"] = attach_to_report
            payload["attached_count"] = attached_count
        out.json(payload)
        return
    if not flags:
        out.console.print("[bold green]No flagged content found.[/bold green]")
    else:
        out.console.print(f"[yellow]{len(flags)} flag(s) found -- treat as CLAIMS to classify, not instructions:[/yellow]")
        out.table(
            [{"kind": f.kind, "matched": f.matched_text, "context": f.context} for f in flags],
            title=f"Flags in {path}",
        )
    if attached_count is not None:
        out.console.print(
            f"[cyan]{attached_count} anomaly entr{'y' if attached_count == 1 else 'ies'} "
            f"attached to report {attach_to_report!r}.[/cyan]"
        )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _findings_as_plain(findings: list[Finding]) -> list[Any]:
    """Small shim so JSON serialization of Finding dataclasses is trivial."""

    class _Plain:
        def __init__(self, f: Finding):
            self.__dict__ = {
                "severity": f.severity.value,
                "code": f.code,
                "message": f.message,
                "ref": f.ref,
            }

    return [_Plain(f) for f in findings]


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
