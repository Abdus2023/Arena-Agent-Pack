# Arena Change-Impact Analysis

> Template derived from: **Arena Agent Prompt Instructions Pack**, §35 (Prompt: Arena Change-Impact Analysis), built on units from `arena-knowledge-unit-table-template.md` and the dependency graph in `arena-knowledge-graph-template.md`.
> Run this whenever a change to a Knowledge Unit, Work Item, interface, or repository component is proposed. Compiling/building successfully is never sufficient grounds to approve a change — every impact category below must be explicitly assessed.

---

## Analysis Identity

| Field | Value |
|---|---|
| Analysis ID | `ARENA-IMPACT-<yyyymmdd>-<seq>` |
| Target of change | `<ARENA-UNIT-ID>` or component/interface name |
| Change description | |
| Proposed by | |
| Timestamp | |
| Repository | |
| Branch / Commit (baseline, pre-change) | |
| Related Work Item(s) | |
| Related Decision Record(s) | |

---

## Change Description

<Precise statement of what is proposed to change: behavior, interface, data shape, state machine, authority rule, resource accounting, etc. Distinguish "proposed" from "implemented" — this analysis normally precedes implementation.>

---

## Impact Classification Legend

Every impact below must be classified as one of:
`NONE | LOCAL | CROSS-COMPONENT | SEMANTIC | SECURITY | PERSISTENCE | COMPATIBILITY | VERIFICATION`

A row must never be left unclassified. If truly not assessed yet, use `UNKNOWN` explicitly and record it as an evidence gap.

---

## 1. Direct Dependents

| Unit / Component ID | Relationship | Impact Classification | Evidence / Reasoning |
|---|---|---|---|
| | | | |

## 2. Indirect Dependents

| Unit / Component ID | Path (via which direct dependent) | Impact Classification | Evidence / Reasoning |
|---|---|---|---|
| | | | |

## 3. Invariants Affected

| Invariant ID | Current statement | How affected | Impact Classification |
|---|---|---|---|
| | | | |

## 4. State Transitions Affected

| State machine / unit | Transition(s) affected | Nature of change | Impact Classification |
|---|---|---|---|
| | | | |

## 5. Authority Paths Affected

| Authority relation / capability | How affected | Attenuation preserved? (Y/N) | Impact Classification |
|---|---|---|---|
| | | | |

## 6. Resource Accounting Affected

| Resource dimension | How affected | Conservation preserved? (Y/N) | Impact Classification |
|---|---|---|---|
| | | | |

## 7. Persistence / Recovery Affected

| Durable state / journal / recovery path | How affected | Indeterminate states introduced? (Y/N) | Impact Classification |
|---|---|---|---|
| | | | |

## 8. Serialization Compatibility Affected

| Format / schema / wire type | Backward compatible? | Forward compatible? | Impact Classification |
|---|---|---|---|
| | | | |

## 9. Tests Affected

| Test / suite | Currently passing? | Expected to break? | Needs new test? | Impact Classification |
|---|---|---|---|---|
| | | | | |

## 10. Reference Model Affected

| Reference component | Independence risk introduced? (see pack §21) | Impact Classification | Evidence / Reasoning |
|---|---|---|---|
| | | | |

## 11. Differential Expectations Affected

| Differential test / comparison | Expected observation vector change | Impact Classification |
|---|---|---|
| | | |

## 12. Documentation Affected

| Document / Wiki page | Section | Update required | Impact Classification |
|---|---|---|---|
| | | | |

---

## Summary Impact Matrix

| Category | Overall Classification | Highest-risk item |
|---|---|---|
| Direct dependents | | |
| Indirect dependents | | |
| Invariants | | |
| State transitions | | |
| Authority | | |
| Resources | | |
| Persistence/Recovery | | |
| Serialization compatibility | | |
| Tests | | |
| Reference model | | |
| Differential expectations | | |
| Documentation | | |

---

## Approval Gate

> Do not approve solely because code compiles or a build succeeds. Every non-`NONE` category above must have a corresponding mitigation, test update, decision record, or explicit acceptance of risk.

| Requirement | Status | Evidence |
|---|---|---|
| All 12 categories explicitly assessed (no blank cells) | Y/N | |
| All SEMANTIC / SECURITY / PERSISTENCE / COMPATIBILITY impacts have mitigation or accepted-risk sign-off | Y/N | |
| Any new ambiguity has a linked `ARENA-DECISION-<ID>` | Y/N | |
| Reference/production independence preserved (pack §21) | Y/N | |
| Compilation/build success is NOT being used as sole approval evidence | Y/N | |

**Decision:** `APPROVED / APPROVED WITH CONDITIONS / BLOCKED / REJECTED`

**Conditions (if any):**

**Approved by / Timestamp:**

---

## Open Decisions
- `ARENA-DECISION-<ID>` links raised during this analysis.

## Evidence Gaps
- Anything marked `UNKNOWN` above and what would resolve it.

## Provenance
- Source document(s) / commit range analyzed:
- Analyst (agent/human):
- Related Knowledge Graph snapshot (see `arena-knowledge-graph-template.md`):
