---
name: arena-evidence-workspace
description: Use the Arena CLI and .arena records to track repository audits, bounded work, decisions, counterexamples, evidence gates, reports, and exports.
---

# Arena Evidence Workspace

## Purpose

Use the Arena Agent Pack's existing Python CLI as the durable record and validation layer for agent work. The CLI records and validates evidence; it is not the execution engine.

## Activation

Use for multi-phase repository work, research, implementation, verification, or any task requiring durable auditability.

Do not use it as proof that an external action occurred unless the record contains independently checkable evidence of that action.

## Inputs and preconditions

- Installed Arena CLI and its version.
- Target repository path.
- Objective, scope, and acceptance criteria.
- Available command outputs, diffs, test reports, and source references.
- Workspace location and data-sensitivity classification.

## Procedure

1. Confirm `arena --help` and the CLI version before using command syntax.
2. Initialize or inspect the workspace: `arena --workspace .arena init`.
3. Create a read-only repository audit and scan the target path.
4. Decompose the objective into bounded work items with explicit dependencies and exit criteria.
5. Record decisions and unresolved questions before irreversible choices.
6. During execution, record commands actually run, exit codes, outputs, and artifact references.
7. Create counterexamples for observed divergence; promote their classification only with the required reproduction evidence.
8. Add named gates for each acceptance criterion and link the evidence that supports it.
9. Validate work items and the workspace before finalization.
10. Export Markdown/HTML projections only after validating the source records.
11. Review exports against the source workspace; do not treat exports as a second source of truth.

## Outputs

- Repository audit.
- Work-item and decision records.
- Counterexample and change-impact records where relevant.
- Evidence gates and final report.
- Validated Markdown/HTML export.

## Failure handling

Do not finalize COMPLETE when required gates fail or evidence is missing. Preserve INVALID, BLOCKED, MISSING, NOT_APPLICABLE, and NOT_RUN as distinct conditions. If the CLI is unavailable, state that and do not fabricate records.

## Acceptance criteria

- CLI version and commands are recorded.
- Audits are read-only and tied to the target repository.
- Work is decomposed into bounded items.
- Gates reference actual evidence.
- Counterexamples are not promoted without reproduction.
- Export validation passes or failures are reported.
- The CLI's record-keeping role is not confused with action execution.
