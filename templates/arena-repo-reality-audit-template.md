# Arena Repository Reality Audit Report

> Template derived from: **Arena Agent Prompt Instructions Pack**, §5 (Repository Reality Rule) and §28 (Prompt: Arena Repository Reality Audit).
> Fill in every field. Use `UNKNOWN` rather than leaving a field blank or guessing.
> Classification values allowed for inventory items: `PRESENT | ABSENT | PLANNED | UNKNOWN | CONFLICTING`.
> Do not infer `PRESENT` from a README, architecture document, issue, roadmap, or planned tree — only from directly observed repository state.

---

## Audit Identity

| Field | Value |
|---|---|
| Audit ID | `ARENA-AUDIT-<yyyymmdd>-<seq>` |
| Repository | |
| Remote URL | |
| Branch / Ref requested | |
| Branch / Ref actually inspected | |
| Commit (short SHA) | |
| Commit (full SHA) | |
| Commit timestamp | |
| Commit author | |
| Working tree clean? (yes/no + diff summary if no) | |
| Auditor (agent/human) | |
| Audit timestamp (UTC) | |
| Tooling used to inspect (e.g. `git ls-tree`, `find`, `cargo metadata`) | |

---

## A. Repository Identity

Describe unambiguously what was inspected: repository origin, protocol, mirror/fork status, and confirmation that branch and commit resolve to the same tree that was walked below.

```
<narrative — 3-6 sentences>
```

---

## B. Commit-Bound Tree Inventory

> Every row must be traceable to an actual command run against the pinned commit above. Record the command in the Evidence column or a shared appendix.

### B.1 Top-level structure

| Path | Type (file/dir) | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | PRESENT | | |

### B.2 Source modules / crates / packages

| Module / Crate / Package | Path | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | PRESENT / ABSENT / PLANNED / UNKNOWN / CONFLICTING | | |

### B.3 Tests

| Test suite / file | Path | Classification | Last known execution evidence | Notes |
|---|---|---|---|---|
| | | | | |

### B.4 Workflows / CI

| Workflow | Path | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | | | |

### B.5 Generated artifacts

| Artifact | Path / location | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | | | |

### B.6 Documentation

| Document | Path | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | | | |

### B.7 Execution evidence found in-repo (logs, CI records, fixtures, etc.)

| Item | Path / location | Classification | Evidence | Notes |
|---|---|---|---|---|
| | | | | |

---

## C. Claimed Architecture vs. Observed Implementation

> For each component/claim named in architecture docs, README, roadmap, issues, or prompts, state the claim, then state what was actually observed in B above. Never let column 3 be inferred from column 2.

| Claimed component / behavior | Source of claim (doc/section) | Observed status | Evidence | Classification |
|---|---|---|---|---|
| | | | | PRESENT / ABSENT / PLANNED / UNKNOWN / CONFLICTING |

---

## D. Evidence Gaps

> List everything that could not be confirmed with direct observation, and exactly what evidence would resolve it.

| Gap ID | Description | What is missing | How to close the gap |
|---|---|---|---|
| GAP-001 | | | |

---

## E. Contradictions

> List every place where two sources (docs vs. tree, doc vs. doc, commit vs. branch head, etc.) disagree. Do not resolve silently — create an `ARENA-DECISION-<ID>` reference if resolution requires authority (see decision record template).

| Contradiction ID | Statement A (source) | Statement B (source) | Impact | Linked decision record |
|---|---|---|---|---|
| CONFLICT-001 | | | | ARENA-DECISION-... (or "none yet") |

---

## F. Recommended Next Inspection

> What should be examined next, and why, given the gaps/contradictions above. Do not recommend proceeding to architecture decomposition or implementation claims until blocking gaps are addressed.

```
<narrative or numbered list>
```

---

## Audit Constraints Confirmed

- [ ] No repository files were modified during this audit.
- [ ] No PRESENT classification was inferred from documentation alone.
- [ ] Every CONFLICTING item has a corresponding entry in section E.
- [ ] Every UNKNOWN item has a corresponding entry in section D.
- [ ] Commit/branch pinning is explicit and unambiguous (see Audit Identity).
