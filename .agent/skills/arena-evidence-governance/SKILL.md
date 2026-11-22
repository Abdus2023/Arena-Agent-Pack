---
name: arena-evidence-governance
description: Use Arena Agent Pack records and CLI to govern work-item lifecycle, decisions, counterexamples, change impact, and evidence-constrained final reports.
---

# Arena Evidence Governance

## Purpose
Apply the Arena Agent Pack as a durable record-keeping and validation layer for auditable agent workflows. The package records and validates evidence; it is not an execution engine and does not authorize external effects.

## Activation
Use when creating or managing work items, ownership claims, lifecycle transitions, verification gates, decisions, stop-condition overrides, counterexamples, change-impact analyses, or final completion reports.

Do not use this skill to execute external actions, infer success from exit codes alone, or promote claims beyond the evidence recorded in the workspace.

## Inputs
- Arena CLI/package revision and Python runtime (Python 3.10+).
- Workspace path (default `.arena`).
- Bounded objective, scope, owner and related record IDs.
- Required gates, stop conditions, evidence references and acceptance criteria.
- Exact command output and validation findings.

## Procedure
1. Initialize or select the workspace with `arena --workspace PATH init`; keep the JSON workspace under version control when an auditable history is required.
2. Create a bounded Work Item with responsibility, ownership expectations and acceptance criteria.
3. Claim work with an explicit owner. Track authorization, execution state, evidence state and lifecycle state as separate dimensions.
4. Advance only through legal transitions. Typical progression is CLASSIFIED → NORMALIZED → READY → IN-PROGRESS → VALIDATING → VERIFIED; never jump directly to VERIFIED.
5. Define gates with a method, result and evidence reference. A PASS gate is only as strong as the cited evidence and its scope.
6. Create Decision Records for alternatives, selected choice, rationale, scope and attribution. Record any stop-condition override explicitly.
7. Stage Counterexamples as observations. Promote to stronger classifications only when the required reproduction/evidence is present.
8. Create Change-Impact records and obtain the required approval before treating an impact analysis as accepted.
9. Validate each record with its record-specific CLI command; preserve findings rather than hiding incomplete records.
10. Create Final Reports only after recording work performed, evidence, outstanding decisions and scope. Use report checks for required completion-contract items.
11. Finalize only at the evidence-derived status ceiling. Incomplete checklist or ERROR findings prevent COMPLETE; warnings, evidence gaps or open decisions constrain the result.
12. Store command, exit code, stdout/stderr, workspace revision and evidence references for material transitions.

## Outputs
- Validated work-item and gate records.
- Attributed decision and stop-condition override records.
- Classified counterexamples with reproduction evidence.
- Change-impact record and approval.
- Final Report whose status does not exceed its evidence ceiling.

## Failure handling
Stop a lifecycle transition when the CLI rejects it. Do not override validation findings by editing JSON directly. Mark incomplete evidence as OPEN or BLOCKED. Do not claim a final report is COMPLETE when the checklist or evidence ceiling does not support it.

## Acceptance criteria
- Every work item has bounded scope and responsibility.
- Lifecycle, authorization, execution and evidence states remain distinct.
- Decisions and overrides have attribution and scope.
- Counterexample promotion has required evidence.
- Change-impact approval is explicit.
- Final report status is evidence-derived and not status-masquerading.
- The CLI is used for persistence and validation.
- No external side effect is implied by an Arena record.

## Source references
- `arena-agent-instructions-pack-v2.md`
- `arena_agent_py/README.md`
- `arena_agent_py/arena_agent/cli.py`
- `arena_agent_py/arena_agent/validation.py`

## Validation status
The package README documents 241 tests for its recorded revision; do not transfer that count or result to a different revision without a fresh test run.
