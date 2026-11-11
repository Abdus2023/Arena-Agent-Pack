---
name: github-research-to-project
description: Convert scoped GitHub research into a provenance-aware project proposal, evidence ledger, architecture, backlog, and reusable skills.
---

# GitHub Research to Project

## Purpose

Turn a supplied GitHub profile, repository set, or research dossier into a bounded engineering project without confusing discovery, documentation, code reuse, or implementation.

## Activation

Use when asked to deeply investigate repositories, compare candidate implementations, extract a best-of architecture, name or bootstrap a project, or persist research and skills.

Do not use to copy code automatically or merge independent projects without explicit approval.

## Inputs and preconditions

- Research objective and target domain.
- Repository URLs or supplied dossier.
- Target platform, runtime, language, and resource constraints.
- Destination repository/branch if persistence is requested.
- Licensing, security, privacy, and project-boundary constraints.

## Procedure

1. Define scope, inclusion/exclusion criteria, and search limits.
2. Resolve canonical repository identity, default branch, visibility, archive state, and exact revision.
3. Classify each candidate: implementation, framework, SDK, application, plugin, example, documentation, binary, fork, mirror, or archive.
4. Inspect source tree, build files, dependency manifests, license, releases, activity, CI, tests, platform requirements, and security-sensitive behavior.
5. Record source URL, revision, file paths, retrieval date, claim, evidence type, status, limitations, and next verification.
6. Separate REUSE, ADAPT, REFERENCE, REJECT, and HOLD decisions.
7. Extract architecture by responsibility, trust boundary, data flow, lifecycle, and interface contracts.
8. Build a priority backlog with observable exit criteria and dependencies.
9. Identify reusable procedures and create narrow skills with skill-creator.
10. Persist only to the confirmed destination. Fetch existing files before updates and use current blob SHAs.
11. Fetch changed files back and compare content markers.
12. Report what was inspected, proposed, implemented, executed, observed, verified, and left open.

## Outputs

- Scope statement and candidate inventory.
- Evidence ledger and source provenance.
- Reuse decision matrix.
- Architecture proposal and ADR candidates.
- Prioritized backlog and reusable skill candidates.
- Persistence and verification report.

## Failure handling

Mark HOLD/BLOCKED when source revision, license, build/security evidence, or destination authority is unresolved. Do not recommend code reuse based on README or search snippets alone.

## Acceptance criteria

- Search scope and omissions are recorded.
- Candidates are classified and pinned or marked unpinned.
- Material claims have evidence or remain OPEN.
- Code adoption is separated from design reference.
- Project boundaries and integration contracts are explicit.
- Repository writes use current blob SHAs and are fetched back.
- No compatibility or implementation claim exceeds available evidence.
