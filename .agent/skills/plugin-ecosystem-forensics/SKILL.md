---
name: plugin-ecosystem-forensics
description: Perform provenance-aware technical audits of plugin ecosystems, loader frameworks, and related repositories before extracting architecture or adopting code.
---

# Plugin Ecosystem Forensics

## Purpose

Turn a collection of plugin repositories, loader implementations, and framework references into a structured, evidence-qualified architecture assessment.

## Activation

Use for DeepSeek Harness/vendor analysis, plugin census work, CordisClaw or Botuniverse research, OpenClaw extension audits, and comparative plugin-framework studies.

Do not use repository popularity, README claims, or a collection's name as evidence of implementation quality or adoption readiness.

## Inputs and preconditions

- Candidate repository URLs or an explicit ecosystem scope.
- Target architecture question.
- Exact repository refs where available.
- Target language/runtime and host integration constraints.
- License, security, maintenance, build, and test evidence.
- Destination project and project-boundary constraints.

## Procedure

1. Define the research question and inclusion/exclusion criteria.
2. Inventory each candidate by canonical URL, owner, type, default branch, pinned revision, license, language, and apparent role.
3. Classify candidates as implementation, framework, SDK, plugin, example, catalog, tool, documentation, fork, or archive.
4. Inspect manifests, entrypoints, loader/registry, dependency graph, lifecycle hooks, configuration, tests, CI, and release history.
5. For vendor directories, distinguish vendored source from upstream dependencies and record local modifications where diff evidence exists.
6. For census/index tools, inspect discovery coverage, pagination, deduplication, stale-entry handling, and false-positive/false-negative behavior.
7. For owned-render or tool-owned-render systems, inspect authority boundaries, rendering ownership, injection risks, and data flow.
8. For web-fetch tools, inspect URL policy, redirect handling, content-type limits, SSRF boundaries, timeout/size limits, and untrusted-content treatment.
9. For PR watchers, inspect authentication scope, webhook/polling model, rate limits, deduplication, and event provenance.
10. For session-format tools, inspect schema versioning, migration, backward compatibility, integrity, and privacy.
11. Compare frameworks by composition model, activation, lifecycle, capability surface, isolation, diagnostics, and testability.
12. Extract patterns as ADAPT or REFERENCE unless source revision, license, security, buildability, and compatibility gates justify REUSE.
13. Produce an evidence ledger, contradiction list, architecture synthesis, and prioritized verification backlog.

## Outputs

- Candidate inventory and classification.
- Repository-by-repository audit.
- Comparative architecture matrix.
- Reuse/adapt/reference/reject/hold decisions.
- Evidence ledger and open questions.
- Proposed skills, tools, adapters, and tests.

## Failure handling

Mark a candidate HOLD or BLOCKED when the revision, license, source completeness, or critical security/build evidence is unavailable. Do not invent implementation behavior from a repository name or search snippet.

## Acceptance criteria

- Scope and search limits are documented.
- Each candidate is pinned or marked unpinned.
- Claims have direct source evidence or remain OPEN/CONJECTURE.
- The DSH plugin set and Cordis/Botuniverse/OpenClaw references remain separate candidates until compared.
- No code reuse is recommended without legal, security, and compatibility review.
