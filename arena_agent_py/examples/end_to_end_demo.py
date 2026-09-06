"""
End-to-end demo of the Arena Agent Python library used programmatically
(as opposed to via the `arena` CLI).

Walks through: Repo Audit -> Knowledge Unit -> Work Item (claim, lifecycle,
gates) -> Decision Record (with a Stop Condition override) ->
Counterexample staging -> Change-Impact Analysis -> Knowledge Graph ->
Final Report, with validation run at each step.

Run with:  python examples/end_to_end_demo.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from arena_agent.graph import GraphEdge, GraphNode, KnowledgeGraph
from arena_agent.ids import IdKind, new_dated_seq_id, new_generic_id
from arena_agent.models import (
    ChangeImpactAnalysis,
    CounterexampleRecord,
    DecisionRecord,
    FinalReport,
    GateResult,
    InterpretationOption,
    InventoryItem,
    KnowledgeUnit,
    Ownership,
    RepoAudit,
    WorkItem,
)
from arena_agent.reporting import render_final_report, render_work_item
from arena_agent.storage import Workspace
from arena_agent.validation import (
    has_errors,
    validate_decision_record,
    validate_final_report,
    validate_knowledge_unit,
    validate_repo_audit,
    validate_work_item,
)
from arena_agent.vocab import (
    AuthorizationState,
    ClaimStatus,
    Confidence,
    DecisionStatus,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    ExtractionClass,
    GraphEdgeType,
    GraphNodeType,
    ImpactClass,
    LifecycleState,
    PresenceClass,
    VerificationGate,
    VerificationMethod,
    VerificationResult,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(Path(tmp) / "workspace")
        ws.init()

        # 1. Repository Reality Audit (v2 §6/§28) -----------------------------
        audit = RepoAudit(
            id=ws.next_repo_audit_id(),
            repository="example/ror-core",
            branch_inspected="main",
            commit="deadbeef1234",
            auditor="demo-script",
        )
        audit.inventory.append(
            InventoryItem(
                path="crates/ror-core",
                kind="dir",
                classification=PresenceClass.ABSENT,
                evidence="not found via `git ls-tree -r deadbeef1234`",
            )
        )
        audit.claimed_vs_observed.append(
            {
                "claim": "ror-core crate should exist",
                "source": "ARCHITECTURE.md",
                "observed": "ABSENT",
                "evidence": "git ls-tree",
                "classification": "CONFLICTING",
            }
        )
        findings = validate_repo_audit(audit)
        assert not has_errors(findings)
        ws.save_repo_audit(audit)
        print(f"[1] Repo audit {audit.id} saved. ror-core is ABSENT (not IMPLEMENTED, per v2 §6).")

        # 2. Knowledge Unit reflecting the audit's finding ---------------------
        unit_id = new_generic_id("ror-core", "existence", "status")
        unit = KnowledgeUnit(
            id=unit_id,
            meaning="ror-core crate is architecturally proposed but not present in the repository",
            evidence_class=EvidenceClass.ARCHITECTURAL_PROPOSAL,
            confidence=Confidence.LOW,
            source_location="ARCHITECTURE.md",
            implementation_status=PresenceClass.ABSENT,
            extraction_class=ExtractionClass.IMPLEMENTATION_STATUS,
        )
        unit.provenance["commit"] = audit.commit
        findings = validate_knowledge_unit(unit)
        assert not has_errors(findings)
        ws.save_knowledge_unit(unit)
        print(f"[2] Knowledge unit {unit.id} saved: {unit.evidence_class.value} / {unit.implementation_status.value}")

        # 3. Decision Record: do we proceed to plan the crate anyway? ----------
        decision_id = ws.next_decision_id()
        decision = DecisionRecord(
            id=decision_id,
            question="ror-core does not exist yet -- should we plan its build anyway?",
            raised_by="demo-script",
            sources=["ARCHITECTURE.md", audit.id],
            affected_components=["ror-core"],
            options=[
                InterpretationOption(option_id="A", description="Plan the build, explicitly acknowledging ABSENT status"),
                InterpretationOption(option_id="B", description="Block until a human confirms scope"),
            ],
            overrides_stop_condition=2,  # "a planned component cannot be located"
        )
        decision.status = DecisionStatus.RESOLVED
        decision.chosen_option_id = "A"
        decision.decided_by = "supervisor-1"
        decision.override_scope = "this work item only"
        decision.override_residual_risk = "work item proceeds against a component that does not exist yet"
        decision.rationale = "Human confirmed intent to build ror-core from scratch this sprint."
        findings = validate_decision_record(decision)
        assert not has_errors(findings), findings
        ws.save_decision(decision)
        print(f"[3] Decision {decision.id} resolved: proceed, Stop Condition #2 overridden by supervisor-1.")

        # 4. Work Item, claimed and driven through its lifecycle ---------------
        item = WorkItem(
            id="ARENA-WORK-ROR-CORE-SCAFFOLD",
            title="Scaffold ror-core crate",
            responsibility="Create the initial ror-core crate skeleton",
            source_unit_ids=[unit.id],
            open_decision_ids=[decision.id],
        )
        item.log("plan", actor="demo-script")
        for state in (
            LifecycleState.CLASSIFIED,
            LifecycleState.NORMALIZED,
            LifecycleState.PLANNED,
            LifecycleState.AUTHORIZED,
        ):
            item.lifecycle_state = state
        # authorization_state is a distinct axis from lifecycle_state (v2 §9.1):
        # reaching AUTHORIZED lifecycle-wise requires an explicit, separately
        # recorded grant, not just "we moved the state machine forward".
        item.authorization_state = AuthorizationState.GRANTED
        item.ownership = Ownership(owner="agent-1", claimed_at="2026-09-05T00:00:00Z", status=ClaimStatus.ACTIVE)
        item.lifecycle_state = LifecycleState.EXECUTING
        item.log("execution", actor="agent-1", note="ran `cargo new ror-core`")
        item.execution_state = ExecutionState.COMPLETED
        item.lifecycle_state = LifecycleState.OBSERVED
        item.log("observation", actor="agent-1", note="crate directory now exists")
        item.postconditions = ["crates/ror-core/Cargo.toml exists"]
        for gate in VerificationGate:
            item.gates.append(
                GateResult(gate=gate, method=VerificationMethod.MANUAL_REVIEW, result=VerificationResult.PASS_, evidence="reviewed diff")
            )
        # Likewise, evidence_state must be explicitly VALIDATED (evidence
        # checked, not just captured) before VERIFIED is a truthful claim.
        item.evidence_state = EvidenceState.VALIDATED
        item.lifecycle_state = LifecycleState.VERIFIED
        item.log("verification", actor="agent-1")
        findings = validate_work_item(item)
        assert not has_errors(findings), findings
        ws.save_work_item(item)
        print(f"[4] Work item {item.id} reached VERIFIED with 0 errors.")
        print()
        print(render_work_item(item, findings)[:600] + "\n... [truncated] ...\n")

        # 5. A failure shows up during a later regression run -------------------
        ce_id = ws.next_counterexample_id()
        ce = CounterexampleRecord(
            id=ce_id,
            first_divergence="cargo build fails: missing `lib.rs`",
            expected_behavior="cargo build succeeds",
            actual_behavior="error[E0463]: can't find crate",
        )
        from arena_agent.validation import promote_counterexample
        from arena_agent.vocab import CounterexampleStage

        promote_counterexample(ce, CounterexampleStage.OBSERVED_FAILURE)
        ce.reproduction_command = "cargo build -p ror-core"
        ce.confirmed = True
        promote_counterexample(ce, CounterexampleStage.REPRODUCIBLE_DEFECT)
        ws.save_counterexample(ce)
        print(f"[5] Counterexample {ce.id} promoted to {ce.stage.value}.")

        # 6. Change-Impact Analysis before fixing it -----------------------------
        impact = ChangeImpactAnalysis(
            id=ws.next_change_impact_id(), target_unit_id=unit.id, change_description="add lib.rs", proposed_by="agent-1"
        )
        for cat in impact.categories:
            impact.categories[cat].classification = ImpactClass.NONE
            impact.categories[cat].details = "adding a missing file, no interface change"
        impact.categories["tests"].classification = ImpactClass.LOCAL
        impact.categories["tests"].details = "existing build test will now pass"
        ws.save_change_impact(impact)
        print(f"[6] Change-impact analysis {impact.id}: all 12 categories assessed.")

        # 7. Knowledge Graph tying it together -----------------------------------
        graph = KnowledgeGraph()
        graph.add_node(GraphNode(id="N-ror-core", node_type=GraphNodeType.COMPONENT, label="ror-core", planned=True, provenance=unit.id))
        graph.add_node(GraphNode(id="N-work", node_type=GraphNodeType.ACTION, label=item.title, planned=False, provenance=item.id))
        graph.add_node(GraphNode(id="N-failure", node_type=GraphNodeType.FAILURE, label=ce.first_divergence, planned=False, provenance=ce.id))
        graph.add_edge(GraphEdge(id="E1", from_id="N-work", edge_type=GraphEdgeType.IMPLEMENTS, to_id="N-ror-core", provenance=item.id))
        graph.add_edge(GraphEdge(id="E2", from_id="N-failure", edge_type=GraphEdgeType.OBSERVES, to_id="N-work", provenance=ce.id))
        gid = ws.next_graph_id()
        ws.save_graph(gid, graph)
        print(f"[7] Knowledge graph {gid}: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")

        # 8. Final Report ----------------------------------------------------------
        report = FinalReport(
            id="ARENA-REPORT-DEMO",
            repository=audit.repository,
            branch=audit.branch_inspected or "",
            commit=audit.commit or "",
            scope="Scaffold the ror-core crate skeleton only; the build regression it "
            "surfaced is tracked but not yet fixed.",
            related_audit_ids=[audit.id],
            related_work_item_ids=[item.id],
            objective="Scaffold ror-core crate from an architectural proposal.",
            observed="ror-core did not exist at audit time; work item created it; a build "
            "regression was found and reproduced.",
            changed="Added crates/ror-core with a scaffolded Cargo.toml (missing lib.rs, per open counterexample).",
            knowledge_units=[{"id": unit.id, "status": unit.evidence_class.value, "evidence": "audit " + audit.id}],
            verification_summary="All 14 verification gates recorded as PASS via manual review (see work item).",
            failures=[ce.id],
            open_decision_ids=[],
            evidence_gaps=["lib.rs fix not yet verified"],
            known_limitations=["Only the scaffold was verified; the build regression fix itself is unverified."],
            recommended_next_action="Land the lib.rs fix, re-run the reproduction command, promote counterexample to MINIMIZED-REPRODUCER if further minimized.",
        )
        for key in report.completion_checklist:
            report.completion_checklist[key] = True
        # Only claim what's actually demonstrated: the checklist is complete
        # and there are no ERRORs, but a real evidence_gap remains (the
        # build regression itself isn't fixed yet) -- so the *legitimate*
        # ceiling here is COMPLETE-WITH-WARNINGS, not COMPLETE. Claiming
        # COMPLETE anyway would be exactly the "requested status masquerading
        # as demonstrated completion" pattern validate_final_report exists
        # to catch (STATUS_MASQUERADING).
        report.overall_status = "COMPLETE-WITH-WARNINGS"
        for key in ("no_claim_without_provenance", "no_completion_without_observation", "no_verification_without_evidence"):
            report.core_principle_checklist[key] = True
        findings = validate_final_report(report)
        assert not has_errors(findings), findings
        ws.save_final_report(report)
        print(f"[8] Final report {report.id}: overall_status={report.overall_status.value}")
        print()
        print(render_final_report(report, findings))


if __name__ == "__main__":
    main()
