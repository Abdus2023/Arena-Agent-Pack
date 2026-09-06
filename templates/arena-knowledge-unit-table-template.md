# Arena Knowledge Unit Table

> Template derived from: **Arena Agent Prompt Instructions Pack**, §6 (Arena Knowledge Transformation), §7 (Stable Arena Knowledge IDs), §16 (Decomposition Contract), §19 (Arena Wiki Extraction Contract), §29 (Prompt: Arena Source Decomposition).
> One row = one atomic knowledge unit (a single responsibility, requirement, invariant, transition, dependency, etc.). Do not merge unrelated units to save space. Do not split a single indivisible requirement across rows.

---

## How to use this table

1. Every unit gets a **stable ID** in the form `ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>` (see pack §7). IDs are never reused for a materially different obligation.
2. Every unit gets exactly one **Source-of-Truth Classification** (see pack §4): `NORMATIVE-SPECIFICATION | ARCHITECTURAL-PROPOSAL | IMPLEMENTED | EXECUTED | TESTED | VERIFIED | OBSERVED | HISTORICAL | DERIVED | EXAMPLE | UNKNOWN | CONFLICTING`.
3. Every unit gets exactly one **Wiki extraction category** (see pack §19): `DEFINITION | PRINCIPLE | REQUIREMENT | INVARIANT | TRANSITION | DEPENDENCY | INTERFACE | ERROR | VERIFICATION | IMPLEMENTATION STATUS | EVIDENCE | EXAMPLE | LIMITATION | OPEN DECISION`.
4. `Implementation status` must come from repository reality evidence (see repo-audit template), never from architecture text.
5. Leave any field `UNKNOWN` rather than guessing. Do not silently resolve ambiguity — link an `ARENA-DECISION-<ID>` instead.

---

## Master Table

| Field | Description |
|---|---|
| **ID** | Stable identifier, `ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>` |
| **Meaning** | One or two sentence plain statement of the atomic unit |
| **Source location** | Document / file / path / line or section reference |
| **Extraction classification** | DEFINITION / PRINCIPLE / REQUIREMENT / INVARIANT / TRANSITION / DEPENDENCY / INTERFACE / ERROR / VERIFICATION / IMPLEMENTATION STATUS / EVIDENCE / EXAMPLE / LIMITATION / OPEN DECISION |
| **Evidence classification** | NORMATIVE-SPECIFICATION / ARCHITECTURAL-PROPOSAL / IMPLEMENTED / EXECUTED / TESTED / VERIFIED / OBSERVED / HISTORICAL / DERIVED / EXAMPLE / UNKNOWN / CONFLICTING |
| **Scope** | Which component(s)/module(s) this unit governs |
| **Inputs** | What the unit consumes (data, signals, preconditions) |
| **Outputs** | What the unit produces |
| **Affected components** | Downstream/upstream components touched |
| **Dependencies** | Other unit IDs this depends on |
| **Forbidden dependencies** | Explicitly disallowed relationships (see pack §17) |
| **Trust level** | Trust boundary this unit operates within |
| **Authority implications** | Any authority/capability requirement or effect (pack §11) |
| **Resource implications** | Any resource dimension touched (pack §10) |
| **State transitions** | States entered/exited, if applicable (pack §8–9) |
| **Invariants** | Referenced invariant IDs and description |
| **Positive cases** | Example(s) where the unit's condition holds |
| **Negative cases** | Example(s) where the unit's condition is violated |
| **Failure modes** | Known failure behavior |
| **Verification obligation** | What must be checked, and how (pack §20) |
| **Implementation status** | PRESENT / ABSENT / PLANNED / UNKNOWN / CONFLICTING — from repo-audit evidence only |
| **Evidence status** | What evidence exists to support current status |
| **Confidence** | High / Medium / Low + rationale |
| **Open ambiguity / decision link** | `ARENA-DECISION-<ID>` if unresolved, else "none" |
| **Related items** | Related knowledge unit IDs |

---

## Blank Row Template (copy per unit)

```markdown
### ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>

- Meaning:
- Source location:
- Extraction classification:
- Evidence classification:
- Scope:
- Inputs:
- Outputs:
- Affected components:
- Dependencies:
- Forbidden dependencies:
- Trust level:
- Authority implications:
- Resource implications:
- State transitions:
- Invariants:
- Positive cases:
- Negative cases:
- Failure modes:
- Verification obligation:
- Implementation status:
- Evidence status:
- Confidence:
- Open ambiguity / decision link:
- Related items:
```

---

## Compact Tabular Form (for many units at once)

| ID | Meaning | Source | Extraction Class | Evidence Class | Deps | Trust | Auth | Resources | State Txn | Invariants | Impl. Status | Evidence Status | Confidence | Decision Link |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARENA-... | | | | | | | | | | | | | | |

---

## Dependency Graph (companion artifact)

> After populating the table, express the dependency edges separately so cycles and forbidden patterns (pack §17) can be checked mechanically.

```text
ARENA-A-1 --requires--> ARENA-B-2
ARENA-B-2 --constrains--> ARENA-C-3
```

| Edge | From | To | Type | Provenance | Inferred? (must be explicit if DERIVED) |
|---|---|---|---|---|---|
| | | | defines / requires / constrains / depends-on / implements / tests / verifies / contradicts / derived-from / produces / consumes / authorizes / persists / recovers / observes / blocks / supersedes | | yes (DERIVED) / no |

---

## Loss-Detection Report (companion artifact, required per pack §29)

> Confirms every source requirement mapped to at least one output unit, and flags anything dropped.

| Source requirement / statement | Mapped to unit ID(s) | Mapping status | Notes |
|---|---|---|---|
| | | MAPPED / PARTIALLY MAPPED / UNMAPPED | |

---

## Table Completion Checklist

- [ ] Every unit has exactly one Evidence classification.
- [ ] Every unit has exactly one Extraction classification.
- [ ] No `Implementation status = PRESENT` without a linked repo-audit evidence reference.
- [ ] No ambiguity silently resolved — every unresolved conflict has a decision link.
- [ ] Dependency graph contains no undeclared forbidden-pattern edges (pack §17).
- [ ] Loss-detection report accounts for 100% of source statements (MAPPED, PARTIALLY MAPPED, or UNMAPPED — none silently skipped).
