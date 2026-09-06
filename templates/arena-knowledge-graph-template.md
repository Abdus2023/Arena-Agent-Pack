# Arena Knowledge Graph

> Template derived from: **Arena Agent Prompt Instructions Pack**, §34 (Prompt: Arena Knowledge Graph Builder), consuming units from `arena-knowledge-unit-table-template.md` and feeding `arena-change-impact-analysis-template.md`.
> The graph must separate planned architecture from observed implementation, and every edge must carry provenance. Inferred edges must be explicitly marked `DERIVED` — never presented as directly sourced.

---

## Graph Identity

| Field | Value |
|---|---|
| Graph ID | `ARENA-GRAPH-<yyyymmdd>-<seq>` |
| Repository | |
| Branch / Commit snapshot | |
| Built by | |
| Timestamp | |
| Source Knowledge Unit table(s) | |
| Source Repo-Audit(s) | |

---

## Node Type Legend (pack §34)

`Source | Claim | Requirement | Invariant | Component | Interface | Capability | Resource | Transition | Action | Artifact | Test | Evidence | Failure | Decision | Commit | Version`

## Edge Type Legend (pack §34)

`defines | requires | constrains | depends-on | implements | tests | verifies | contradicts | derived-from | produces | consumes | authorizes | persists | recovers | observes | blocks | supersedes`

---

## 1. Node Registry

> Every node must be traceable to a Knowledge Unit ID, Repo-Audit item, Work Item, or Decision Record. Nodes with no such reference are not permitted (mark `UNKNOWN` provenance instead of fabricating a node).

| Node ID | Node Type | Label | Planned or Observed? | Provenance (unit/audit/work-item/decision ID) |
|---|---|---|---|---|
| N-001 | Component | | PLANNED / OBSERVED | |

---

## 2. Edge Registry

> Every edge must carry provenance. Mark `Inferred? = DERIVED` explicitly for any edge not directly stated in a source — never blend inferred and observed edges without the flag.

| Edge ID | From Node | Edge Type | To Node | Provenance | Inferred? (DERIVED / no) | Notes |
|---|---|---|---|---|---|---|
| E-001 | N-001 | | | | | |

---

## 3. Planned vs. Observed Partition

> Explicit separation required by pack §34 — never let a PLANNED subgraph silently merge with the OBSERVED subgraph.

### 3.1 Planned Architecture Subgraph

| Node/Edge ID | Description | Source (doc/architecture) |
|---|---|---|
| | | |

### 3.2 Observed Implementation Subgraph

| Node/Edge ID | Description | Source (repo-audit evidence) |
|---|---|---|

### 3.3 Divergences Between the Two Subgraphs

| Planned item | Observed item (or ABSENT) | Divergence type | Linked Decision Record (if any) |
|---|---|---|---|
| | | missing / contradicting / superseded / not-yet-built | |

---

## 4. Contradiction Check

> Any two edges/nodes with a `contradicts` relationship, or divergent claims about the same subject, must be listed here — never silently dropped or auto-resolved.

| Contradiction ID | Node/Edge A | Node/Edge B | Description | Linked Decision Record |
|---|---|---|---|---|
| | | | | `ARENA-DECISION-...` or "none yet" |

---

## 5. Traversal Views (optional, derive as needed)

### 5.1 Dependency View (`depends-on`, `requires`, `constrains`)
```text
N-001 --requires--> N-002
N-002 --constrains--> N-003
```

### 5.2 Verification View (`tests`, `verifies`)
```text
N-010 --tests--> N-001
N-011 --verifies--> N-002
```

### 5.3 Authority/Resource View (`authorizes`, `consumes`, `produces`)
```text
N-020 --authorizes--> N-001
N-001 --consumes--> N-030
```

### 5.4 Lifecycle View (`persists`, `recovers`, `observes`, `supersedes`)
```text
N-001 --persists--> N-040
N-040 --recovers--> N-041
```

---

## 6. Change-Impact Hook

> When a node/edge changes, generate an `arena-change-impact-analysis-template.md` seeded from this graph's direct/indirect dependents (edges of type `depends-on`, `requires`, `constrains`, `implements` pointing at or from the changed node).

| Changed Node/Edge | Direct dependents (from graph) | Linked Change-Impact Analysis ID |
|---|---|---|
| | | `ARENA-IMPACT-...` |

---

## Graph Integrity Checklist

- [ ] Every node has provenance to a Knowledge Unit, Repo-Audit item, Work Item, or Decision Record.
- [ ] Every edge has provenance.
- [ ] Every inferred edge is explicitly marked `DERIVED`.
- [ ] Planned and Observed subgraphs are kept visibly separate (section 3).
- [ ] All `contradicts` relationships are logged in section 4 with a decision link or explicit "none yet".
- [ ] No node/edge implies implementation status without repo-audit backing.
