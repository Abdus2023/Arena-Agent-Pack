---
name: source-intelligence-audit
description: Audit repositories and technical sources for provenance, completeness, maintenance, licensing, buildability, security, and compatibility before reuse.
---

# Source Intelligence Audit

## Purpose

Determine whether a candidate repository is suitable as code, a library, a design reference, a historical record, or should be rejected/held.

## Activation

Use during GitHub deep research, dependency selection, fork evaluation, vendor inspection, or third-party source adoption.

Do not treat popularity, README statements, stars, or a successful compile as sufficient adoption evidence.

## Inputs and preconditions

- Canonical source URL and candidate identity.
- Exact commit/ref and retrieval date.
- Intended use and target platform/runtime.
- License and attribution requirements.
- Build environment, dependencies, and security boundary.

## Procedure

1. Resolve canonical owner/repository and fork/mirror relationships.
2. Pin the exact revision and relevant paths.
3. Inspect whether the repository contains complete source, a partial implementation, docs, binaries, examples, or a catalog.
4. Inspect license text, SPDX metadata, file notices, bundled assets, and dependency licenses.
5. Inspect build scripts, toolchain, dependencies, native targets/ABIs, CI, and tests.
6. Reproduce a clean build/test where possible; mark unexecuted checks OPEN.
7. Inspect maintenance evidence: releases, tags, commits, issues, PRs, archived status, and CI recency.
8. Inspect permissions, network endpoints, analytics, secrets handling, command execution, input validation, and data flows where relevant.
9. Map target compatibility from explicit API, ABI, toolchain, and device evidence.
10. Assign REUSE, ADAPT, REFERENCE, REJECT, or HOLD with rationale.
11. Record contradictions, gaps, and next verification steps.

## Outputs

- Executive assessment.
- Source-tree and implementation completeness.
- Provenance, license, build, maintenance, security, and compatibility findings.
- Decision matrix and evidence ledger.
- Unresolved questions and verification backlog.

## Failure handling

Keep the candidate HOLD or BLOCKED when revision, license, source completeness, critical build/security evidence, or intended-use compatibility is unavailable. Never infer license compatibility.

## Acceptance criteria

- Revision and inspected paths are identified.
- README claims are separated from code/test observations.
- License and dependency provenance are checked for proposed reuse.
- Build/test status reflects actual execution.
- Security and compatibility claims are scoped.
- Decision rationale and unresolved evidence are recorded.
