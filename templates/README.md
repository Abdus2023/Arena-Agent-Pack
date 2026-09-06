# Arena Agent Templates — Index & Usage Guide

This folder contains the fillable companion templates for
[`../arena-agent-instructions-pack.md`](../arena-agent-instructions-pack.md).
The pack defines the rules (contracts, separations, stop conditions); these
templates are where you actually *do* the work while staying compliant with
those rules.

Every template traces back to specific pack sections — check the header note
at the top of each file if you want the exact rationale for a field.

---

## The Nine Templates

| # | File | Pack Reference | Produces |
|---|---|---|---|
| 1 | `arena-repo-reality-audit-template.md` | §5, §28 | Ground-truth inventory of what actually exists in the repository at a pinned commit |
| 2 | `arena-knowledge-unit-table-template.md` | §6–7, §16, §19, §29 | Atomic, classified knowledge units decomposed from source material |
| 3 | `arena-knowledge-graph-template.md` | §34 | Node/edge graph linking units, components, requirements, evidence, decisions |
| 4 | `arena-work-item-template.md` | §12, §27, §31 | Executable work items with a Plan → Authorization → Execution → Observation → Verification lifecycle log |
| 5 | `arena-change-impact-analysis-template.md` | §35 | Pre-change impact assessment across 12 categories before any unit/component is modified |
| 6 | `arena-decision-record-template.md` | §24, §25 | Explicit record of ambiguity/conflict, used instead of silent resolution or guessing |
| 7 | `arena-counterexample-template.md` | §22, §23, §36 | Failure records, split into Observed Failure vs. Reproducible Defect, with minimization |
| 8 | `arena-final-report-template.md` | §39, §40, §43 | End-of-operation report proving the Completion Contract was actually satisfied |
| 9 | `arena-wiki-page-template.md` | §37 | Durable knowledge-base pages (00 Status … 17 Runbooks) for long-term reference |

---

## Suggested Usage Order

The templates map onto the pack's own lifecycle (§42: Source Corpus →
Repository Reality → Classification → Requirement Atoms → Invariant Registry
→ State/Transition Model → Dependency Graph → Work Items → Authorization →
Execution → Observation → Evidence → Verification → Wiki). In practice, work
through them in this order:

```
1. REPO REALITY AUDIT  ──────────────────────────────────────────────►  #1
        │
        │  establishes what actually exists before anything else
        ▼
2. KNOWLEDGE UNIT TABLE  ─────────────────────────────────────────────►  #2
        │
        │  decompose source material into atomic, classified units,
        │  cross-checked against the audit's PRESENT/ABSENT findings
        ▼
3. KNOWLEDGE GRAPH  ───────────────────────────────────────────────────►  #3
        │
        │  wire units/components/requirements together with provenance;
        │  separate Planned vs. Observed subgraphs
        ▼
4. WORK ITEMS  ─────────────────────────────────────────────────────────►  #4
        │
        │  turn verified units into executable work with an explicit
        │  Plan/Authorization/Execution/Observation/Verification log
        │
        ├──► if ambiguity or conflicting evidence appears at ANY step:
        │        DECISION RECORD  ─────────────────────────────────────►  #6
        │        (block the affected item until resolved; never guess)
        │
        ├──► before executing a change to an existing unit/component:
        │        CHANGE-IMPACT ANALYSIS  ──────────────────────────────►  #5
        │        (run against the current Knowledge Graph's dependents)
        │
        └──► if execution or verification reveals a failure:
                 COUNTEREXAMPLE RECORD  ───────────────────────────────►  #7
                 (Observed Failure → minimize → Reproducible Defect)
        ▼
5. FINAL REPORT  ───────────────────────────────────────────────────────►  #8
        │
        │  close out the operation only once the Completion Contract
        │  checklist is genuinely satisfied
        ▼
6. WIKI PAGES  ──────────────────────────────────────────────────────────►  #9
        │
        │  promote durable, verified knowledge into the long-term
        │  knowledge base (00 Status … 17 Runbooks)
        ▼
   (repeat 1→6 for the next change / audit cycle)
```

### Quick-reference: which template to reach for

| Situation | Use |
|---|---|
| Starting work on an unfamiliar or newly-cloned repo | #1 Repo Reality Audit |
| Have a spec/doc/README to turn into structured knowledge | #2 Knowledge Unit Table |
| Need to see how units/components depend on each other | #3 Knowledge Graph |
| Ready to actually plan, authorize, and execute something | #4 Work Item |
| About to modify an existing unit, interface, or component | #5 Change-Impact Analysis |
| Two sources disagree, or a fact is genuinely unknown | #6 Decision Record |
| Something failed during execution or verification | #7 Counterexample Record |
| Operation is finishing and needs a defensible summary | #8 Final Report |
| Knowledge should persist beyond this operation | #9 Wiki Page |

---

## Cross-Template Linking Conventions

To keep the whole set queryable as one provenance graph, use these ID
prefixes consistently across all files:

| Prefix | Meaning | Defined in |
|---|---|---|
| `ARENA-AUDIT-<date>-<seq>` | Repo Reality Audit | #1 |
| `ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>` | Knowledge Unit | #2 |
| `ARENA-GRAPH-<date>-<seq>` | Knowledge Graph snapshot | #3 |
| `ARENA-UNIT-ID` (work item title) | Work Item | #4 |
| `ARENA-IMPACT-<date>-<seq>` | Change-Impact Analysis | #5 |
| `ARENA-DECISION-<date>-<seq>` | Decision Record | #6 |
| `ARENA-CE-<date>-<seq>` | Counterexample / Failure Record | #7 |
| (report has no separate ID; keyed by operation + timestamp) | Final Report | #8 |
| `<NN> <Page Title>` | Wiki Page | #9 |

Always link by ID rather than duplicating content — e.g. a Work Item
references Knowledge Unit IDs rather than re-describing them, and a Wiki
page references Decision Record IDs rather than re-litigating them.

---

## Non-Negotiable Reminders (from the pack)

These apply across every template in this folder, not just one:

- **No claim without provenance.** Every field with a status/classification must cite its evidence source.
- **No PRESENT/IMPLEMENTED status without repo-audit evidence.** Never infer from docs, READMEs, or architecture diagrams.
- **No silent resolution of ambiguity.** Create a Decision Record (#6) instead.
- **PLAN ≠ AUTHORIZATION ≠ EXECUTION ≠ OBSERVATION ≠ VERIFICATION.** Keep the Work Item (#4) lifecycle log stages distinct.
- **Compilation/build success is never sufficient approval for a change.** Run the Change-Impact Analysis (#5) first.
- **An Observed Failure is not a Reproducible Defect** until minimization and reproduction are confirmed (#7).
- **A task is not complete** until every condition in the Completion Contract (pack §39, checked in #8) is true.
- **Planned architecture must never appear as implemented behavior** on a Wiki page (#9).

When any of these would be violated, the correct action is `STOP` /
`BLOCKED` — not a best-effort guess (pack §25, §26).

---

## File Map

```
arena-agent-instructions-pack.md      (../  — the governing rules)
templates/
├── README.md                             (this file)
├── arena-repo-reality-audit-template.md
├── arena-knowledge-unit-table-template.md
├── arena-knowledge-graph-template.md
├── arena-work-item-template.md
├── arena-change-impact-analysis-template.md
├── arena-decision-record-template.md
├── arena-counterexample-template.md
├── arena-final-report-template.md
└── arena-wiki-page-template.md
```
