# Arena Work Item Template

> Template derived from: **Arena Agent Prompt Instructions Pack**, §12 (Action Contract), §16 (Decomposition Contract), §27 (Standard Arena Work Item), §31 (Prompt: Arena Work Planner).
> One file/section per work item. A work item is derived from one or more Knowledge Units (see `arena-knowledge-unit-table-template.md`) and, once authorized/executed/observed, feeds evidence back into that table.
> Reminder: PLAN ≠ AUTHORIZATION ≠ EXECUTION ≠ OBSERVATION ≠ VERIFICATION. Fill each section only when that stage has actually happened.

---

## <ARENA-UNIT-ID> — <Title>

### Responsibility
<Exactly one semantic responsibility — if you need "and", split into two work items.>

### Source Knowledge Units
| Knowledge Unit ID | Relationship |
|---|---|
| | implements / verifies / derived-from |

### Evidence Classification
- Classification:
- Source:
- Repository:
- Branch:
- Commit:
- Evidence level:
- Confidence:

### Inputs
| Input | Type | Trust | Validation |
|---|---|---|---|
| | | | |

### Outputs
| Output | Type | Meaning | Evidence |
|---|---|---|---|
| | | | |

### Authority
- Required authority:
- Authority source:
- Attenuation:
- Forbidden authority:

### Resources
- CPU:
- Memory:
- Time:
- Concurrency:
- Storage:
- Tool calls / network / other:
- Resource budget (initial = available + reserved + consumed + released):

### Dependencies
- Upstream (must complete first):
- Downstream (blocked on this):
- Forbidden (must not depend on):

### State
```text
<state> --<guard/action>--> <state>
```

### Preconditions
1.

### Postconditions
1.

### Invariants
1. "<ARENA-...>" —

### Failure Modes
| Failure | State | Required behavior | Evidence |
|---|---|---|---|
| | | | |

### Persistence
- Durable state:
- Journal:
- Recovery behavior:
- Indeterminate states and reconciliation path:

---

## Lifecycle Log

> Append-only. Do not edit past entries; add corrections as new entries. This is the record that separates PLAN from AUTHORIZATION from EXECUTION from OBSERVATION from VERIFICATION.

### 1. Plan
- Planned by:
- Timestamp:
- Goal:
- Actions proposed:
- Expected outputs:
- Blocking conditions identified:

### 2. Authorization
- Authorized by (human/governance/supervisor):
- Timestamp:
- Authority granted (scope, attenuation):
- Conditions attached:
- If not yet authorized: state `NOT AUTHORIZED` explicitly — do not proceed to execution.

### 3. Execution
- Executed by (agent/tool/human):
- Timestamp start / end:
- Command(s) / action(s) actually run:
- Environment:
- Exit status:
- stdout / stderr (or reference to log artifact):
- Side effects produced:
- If not yet executed: state `NOT EXECUTED` explicitly.

### 4. Observation
- Observed state after execution:
- Artifacts produced:
- Resource consumption observed:
- External effects observed:
- Durability evidence:
- Unexpected behavior:
- Classify each item as EXPECTED / OBSERVED / INFERRED / UNKNOWN — never upgrade INFERRED to OBSERVED.

### 5. Verification
- Verified by:
- Timestamp:
- Requirement(s) checked:
- Result: PASS / FAIL / PARTIAL / NOT-TESTED / NOT-IMPLEMENTED / BLOCKED / AMBIGUOUS / INAPPLICABLE
- Evidence (for PASS) or minimal counterexample (for FAIL):
- Verification Gates (pack §38) — mark each PASS / FAIL / PARTIAL / NOT-APPLICABLE / BLOCKED, never omitted:

| Gate | Result | Evidence |
|---|---|---|
| Identity | | |
| Scope | | |
| Semantics | | |
| Authority | | |
| Resources | | |
| State | | |
| Effects | | |
| Persistence | | |
| Recovery | | |
| Determinism | | |
| Independence | | |
| Evidence | | |
| Reproducibility | | |
| Documentation | | |

---

## Open Decisions
- List any `ARENA-DECISION-<ID>` links required before this item can proceed further.

## Provenance
- Source document(s):
- Repository / branch / commit:
- Extraction method:
- Related work items:
