---
name: repository-bootstrap
description: Safely establish project documentation, research records, reusable skills, workflows, and verification gates in an existing repository.
---

# Repository Bootstrap

## Purpose

Initialize or extend a repository workspace without overwriting existing work or overstating project status.

## Activation

Use when asked to create a project foundation, persist research, add an .agent package, establish docs/schemas/tests, or prepare a repository for incremental implementation.

Do not use to generate a full implementation before inspecting the repository and freezing its scope.

## Inputs and preconditions

- Exact owner/repository and target branch.
- Repository read/write permissions.
- Project identity, scope, non-goals, and constraints.
- Existing files and current revision.
- Required deliverables and approval boundaries.

## Procedure

1. Inspect repository metadata, default branch, target branch, current commit, permissions, and working state.
2. Read README, contribution rules, agent instructions, package metadata, CI, and existing architecture.
3. Inspect each intended target path. A 404 for one path does not prove the repository is empty.
4. Record baseline facts, unknowns, and conflicts.
5. Define project charter, architecture boundaries, data contracts, security model, and release gates.
6. Add research under a dedicated path; keep the README concise.
7. Add skills under .agent/skills, workflows under .agent/workflows, tools under .agent/tools, and schemas under .agent/schemas.
8. Create absent files; update existing files only after fetching the current blob SHA.
9. Avoid conflicting parallel writes. Capture each commit SHA.
10. Fetch every changed file back from the target branch and compare content markers.
11. Run repository-specific validators and tests when available.
12. Report persistence separately from technical validation.

## Outputs

- Repository baseline and charter.
- Proposed structure and architecture records.
- Skills, tools, workflows, and schemas as requested.
- Commit identifiers, fetch-back evidence, test results, and open gaps.

## Failure handling

Stop on ambiguous repository/branch identity, insufficient write permission, unreconciled concurrent changes, unsafe overwrite, or unresolved project-boundary conflicts. Report partial completion.

## Acceptance criteria

- Correct repository and branch are explicit.
- Existing files were inspected before edits.
- Proposed and implemented structure are distinguished.
- Existing files were updated using current blob SHAs.
- Commit identifiers were captured.
- Every changed file was fetched back.
- Tests and runtime discovery are reported accurately.
