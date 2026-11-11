---
name: continuity-and-process-extraction
description: Continue multi-turn technical work without skipping phases and extract durable processes, decisions, and evidence into reusable artifacts.
---

# Continuity and Process Extraction

## Purpose

Restore the exact state of a multi-turn project, identify the next unresolved unit of work, and convert repeatable processes into maintainable skills, tools, or workflows.

## Activation

Use when the operator says continue, resume, pick up from a cutoff, refers to previous decisions, or asks to turn prior work into reusable processes.

Do not use for a standalone factual answer or when the current turn contains all required state and no continuity operation is needed.

## Inputs and preconditions

- Current objective and latest user instruction.
- Available conversation summaries and prior decisions.
- Relevant files, repository refs, branches, commits, and tool outputs.
- Phase/state ledger, if present.
- Explicit exclusions and project boundaries.

Never infer that a prior proposal was implemented. If an earlier state cannot be recovered, mark it OPEN and ask only for the essential missing item.

## Procedure

1. Resolve the project and workstream identity.
2. Retrieve the latest durable state, including branch, commit, worktree status, last completed phase, next phase, blockers, and operator decisions.
3. Build a source timeline: user requirements, decisions, proposals, actions, observed results, and verified results.
4. Reconcile contradictions using the newest direct evidence; preserve unresolved conflicts rather than silently selecting one.
5. Identify the last completed gate and the next unresolved gate.
6. Continue from that gate. Do not repeat completed work or skip uncompleted phases.
7. For each new claim, attach its evidence class and verification status.
8. When extracting a process, identify stable inputs, outputs, invariants, branches, failure modes, and handoffs.
9. Classify the result as a skill, computational tool, workflow, schema, or evidence record.
10. Update the continuation ledger with completed, blocked, and next actions.

## Outputs

- Continuity snapshot.
- Decision and contradiction ledger.
- Next-step plan.
- Extracted skill/tool/workflow candidates.
- Updated state and evidence records.

## Failure handling

Stop if the target project cannot be identified, the relevant revision cannot be established, or a requested operation would overwrite work without current evidence. Mark missing history OPEN; do not reconstruct it from guesswork.

## Acceptance criteria

- The exact project and revision are stated.
- Completed, proposed, executed, observed, and verified work are separated.
- The next action follows the last confirmed state.
- No completed phase is silently repeated.
- No unresolved phase is silently skipped.
- Contradictions and missing evidence remain visible.
