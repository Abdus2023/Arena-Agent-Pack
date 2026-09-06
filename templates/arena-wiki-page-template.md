# Arena Wiki Page Template

> Template derived from: **Arena Agent Prompt Instructions Pack**, §37 (Prompt: Arena Wiki Generator), built on knowledge units from `arena-knowledge-unit-table-template.md`.
> Use one copy of this file per Wiki page. Page numbers/titles below match the canonical Wiki structure in §37 — rename the title but keep the number prefix so ordering is stable.
> Never let planned architecture appear as implemented behavior on any page.

---

## Canonical Page Index (for reference — create one file per page as needed)

```
00 Status
01 Source Corpus
02 Repository Reality
03 Trust Model
04 Semantic Model
05 Invariants
06 State Machines
07 Authority
08 Resources
09 Execution
10 Persistence
11 Recovery
12 Verification
13 Evidence
14 Implementation Inventory
15 Decisions
16 Counterexamples
17 Runbooks
```

---

# <NN> <Page Title>

## Required Header Block

| Field | Value |
|---|---|
| Scope | |
| Source | |
| Repository revision (commit) | |
| Classification (pack §4) | NORMATIVE-SPECIFICATION / ARCHITECTURAL-PROPOSAL / IMPLEMENTED / EXECUTED / TESTED / VERIFIED / OBSERVED / HISTORICAL / DERIVED / EXAMPLE / UNKNOWN / CONFLICTING |
| Implementation status | PRESENT / ABSENT / PLANNED / UNKNOWN / CONFLICTING |
| Evidence status | <what supports the implementation status above> |
| Dependencies | <other Wiki pages / knowledge units this page depends on> |
| Open decisions | `ARENA-DECISION-<ID>` list, or "none" |
| Last updated | |
| Updated by | |

## Content

<The actual page content. Written prose, tables, diagrams as appropriate to the page topic. Every substantive claim should be traceable to a Knowledge Unit ID or Work Item ID.>

## Knowledge Units Referenced

| ID | Relevance |
|---|---|
| ARENA-... | |

## Implementation Inventory (only if page concerns implementation status)

| Component | Status | Evidence | Repo-Audit Reference |
|---|---|---|---|
| | PRESENT / ABSENT / PLANNED / UNKNOWN / CONFLICTING | | |

## Open Ambiguities

| Decision ID | Question | Status |
|---|---|---|
| | | OPEN / RESOLVED / SUPERSEDED |

## Change History

| Date | Change | Author | Reason | Semantic change? (Y/N — if Y, link decision/change record) |
|---|---|---|---|---|

---

## Per-Page Notes by Section (guidance, delete once page is drafted)

- **00 Status** — Overall project/repo status dashboard. Must distinguish claimed vs. observed at a glance; link to latest Repo-Audit and Final Report.
- **01 Source Corpus** — Inventory of all source material ingested (docs, specs, issues), each with its Source-of-Truth Classification.
- **02 Repository Reality** — Mirrors the latest `arena-repo-reality-audit-template.md`; link, don't duplicate, if audit is kept separately.
- **03 Trust Model** — The trust hierarchy in effect (pack §2) and where this repo/project's authority boundaries sit within it.
- **04 Semantic Model** — Core domain concepts, terminology map, and definitions (DEFINITION-class knowledge units).
- **05 Invariants** — Full invariant registry with IDs, statements, and verification obligations.
- **06 State Machines** — All formally defined states/transitions (pack §8–9); flag any compound transitions and their decomposition.
- **07 Authority** — Capability/authority model, derivation rules, forbidden authority patterns in effect (pack §11).
- **08 Resources** — Resource dimensions tracked and their accounting model (pack §10).
- **09 Execution** — How execution is performed, observed, and logged; links to Work Item lifecycle logs.
- **10 Persistence** — Durable state, journaling, what's persisted vs. transient (pack §14).
- **11 Recovery** — Recovery/reconciliation semantics for indeterminate states.
- **12 Verification** — Verification model layers (pack §20) and what's covered vs. not.
- **13 Evidence** — Evidence taxonomy and provenance requirements in effect (pack §15).
- **14 Implementation Inventory** — Full claimed-vs-observed matrix across the whole project (aggregated from repo audits).
- **15 Decisions** — Index of all `ARENA-DECISION-<ID>` records, open and resolved.
- **16 Counterexamples** — Index of all reproducible failure records.
- **17 Runbooks** — Operational procedures for running audits, verifications, recoveries, etc.
