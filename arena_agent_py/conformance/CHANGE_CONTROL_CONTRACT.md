# Baseline Change-Control Contract

**Status:** Proposed post-baseline governance artifact

**Applies to:** `Arena-Agent-Pack` after `conformance-baseline-v1`

**Frozen baseline:** `conformance-baseline-v1`

**Principle:** A frozen conformance baseline is historical evidence, not an open backlog.

**Relationship to existing governance:** This contract is the operational,
post-freeze change-control layer referenced by `BASELINE_PRESERVATION_PLAN.md`
Part II (the Baseline Protocol). It formalizes the change-classification
system (§26), Conformance Impact Assessment (§27–29), impact outcomes,
mandatory-phase triggers, delta vocabulary (§21–22), residual-finding
protocol (§5, §11), pack-change protocol (§8, §19), evidence requirements,
agent decision boundary (§29), merge/release rules, and the baseline-v2
establishment conditions (§35) into a single normative contract. It does
**not** modify `conformance-baseline-v1`, `CONFORMANCE_MATRIX.md`,
`BASELINE.json`, or any historical disposition. Where this contract and the
Baseline Protocol describe the same rule, they agree; the Baseline Protocol
remains the record of *why* the baseline was frozen, and this contract is
the record of *how changes are evaluated afterward*.

---

## 1. Purpose

This contract defines how changes are evaluated after a conformance baseline has been frozen.

It establishes:

- how a proposed change is classified;
- when a Baseline Impact Assessment is required;
- when ordinary engineering may proceed;
- when a new conformance phase is mandatory;
- when a new baseline may be established;
- how `v1 → v2` differences are recorded;
- how normative-source changes are handled;
- how residual baseline findings are treated;
- how agents and human maintainers divide decision authority.

This contract does **not** modify `conformance-baseline-v1`.

---

## 2. Governing Principle

The frozen baseline answers:

> **What was evaluated, against which normative source and matrix, at a particular repository state, with what evidence and disposition?**

It does not answer:

> **What should be changed next?**

Therefore:

```text
Baseline finding
    ≠
Backlog item
    ≠
Authorization
    ≠
Implementation
    ≠
Verification
```

Discovery does not authorize remediation.

A residual `PARTIAL`, `NON-CONFORMANT`, or `UNVERIFIED` disposition is an accepted historical fact unless a separately authorized change explicitly targets it.

---

## 3. Baseline Immutability

Once published, a baseline identity is immutable.

For `conformance-baseline-v1`, the following must not be rewritten in place:

- baseline tag;
- tagged commit;
- baseline manifest;
- frozen conformance matrix;
- historical test result;
- historical disposition;
- historical scope;
- historical pack identity.

The tag `conformance-baseline-v1` must never be moved.

If the evaluated state changes materially, the correct operation is:

```text
v1
 ↓
new scoped evaluation
 ↓
new evidence
 ↓
new matrix/state
 ↓
v2
```

Never:

```text
v1
 ↓
edit historical evidence
 ↓
pretend v1 changed
```

---

## 4. Baseline Identity

A baseline is identified by the combined identity of:

```text
repository identity
+
repository commit
+
pack identity
+
matrix identity
+
test/evidence identity
+
disposition identity
```

A commit alone is therefore insufficient to define a conformance baseline.

A new commit may be ordinary development.

A new **evaluated conformance state** is a separate event.

---

## 5. Change Classes

Every post-baseline change belongs to one primary class.

### Class A — Documentation / Non-Semantic

Examples:

- spelling corrections;
- formatting;
- explanatory prose;
- navigation improvements;
- non-normative README clarification;
- historical documentation corrections.

Class A does not require a Baseline Impact Assessment unless the change alters normative meaning or changes a claim about implementation/conformance.

---

### Class B — Non-Semantic Engineering

Examples:

- internal refactoring;
- implementation cleanup;
- performance improvements preserving behavior;
- test infrastructure changes;
- code organization changes;
- dependency/tooling changes that do not alter evaluated semantics.

The proposer must be able to demonstrate behavioral preservation where relevant.

A larger test count is not itself evidence of conformance improvement.

---

### Class C — Semantic Engineering

Examples:

- changing validation behavior;
- changing lifecycle transitions;
- changing persistence semantics;
- changing CLI mutation behavior;
- changing record schemas;
- changing status derivation;
- changing cross-record validation;
- changing provenance behavior.

Class C requires a Baseline Impact Assessment.

---

### Class D — Conformance Remediation

A change is Class D when it explicitly targets a frozen conformance row, known baseline gap, or normative obligation represented in the frozen matrix.

Examples:

- implementing a previously `PARTIAL` requirement;
- correcting a `NON-CONFORMANT` behavior;
- adding machine enforcement for a previously unverified obligation;
- changing behavior specifically because of a frozen conformance observation.

Class D requires:

1. explicit scope;
2. explicit authorization;
3. a new scoped phase;
4. evidence requirements;
5. post-change verification.

The frozen baseline remains unchanged.

---

### Class E — Normative-Source Change

Class E applies when the source against which conformance is evaluated changes.

Examples:

- new Prompt Instructions Pack version;
- changed normative requirement;
- changed section numbering with semantic effect;
- changed vocabulary or obligation;
- replacement of the authoritative specification.

Class E must not be handled as ordinary remediation.

The new normative source receives its own identity and evaluation context.

---

## 6. Baseline Impact Assessment

A Baseline Impact Assessment is required whenever a change could alter a semantic claim represented by the frozen baseline.

The assessment asks:

### A. Does the change alter normative meaning?

If yes:

```text
Class E or explicit normative-impact decision
```

### B. Does the change alter behavior represented by a frozen matrix row?

If yes:

```text
CONFORMANCE-IMPACT
```

### C. Does the change merely reorganize implementation while preserving behavior?

If yes:

```text
NO-CONFORMANCE-IMPACT
```

### D. Does the change affect only documentation?

If yes:

```text
NO-CONFORMANCE-IMPACT
```

unless the documentation itself is normative.

### E. Does the change alter evidence rather than implementation?

Determine whether it:

- merely improves observability;
- invalidates previous evidence;
- introduces a new evidence source;
- changes the evaluated claim.

Improved evidence does not automatically mean improved conformance.

---

## 7. Impact Outcomes

Every completed assessment produces one of four outcomes.

### `NO-IMPACT`

The frozen semantic claim remains valid.

Ordinary development may proceed.

No new baseline is required.

---

### `IMPACTED-BUT-NOT-CONFORMANCE`

The change affects implementation or evidence surrounding a baseline claim but does not establish a new conformance state.

Examples:

- internal refactor;
- test harness improvement;
- richer diagnostics.

The baseline remains historical and valid.

---

### `CONFORMANCE-IMPACT`

The change intentionally alters behavior relevant to one or more frozen matrix rows.

A new scoped conformance phase is mandatory.

The baseline is not edited.

---

### `NORMATIVE-IMPACT`

The authoritative source or its normative interpretation has changed.

A new normative evaluation context is mandatory.

The old baseline remains valid against its original source.

---

## 8. Mandatory New-Phase Triggers

A new explicitly scoped phase is mandatory when:

1. a frozen `NON-CONFORMANT` row is being remediated;
2. a frozen `PARTIAL` row is being intentionally strengthened;
3. a frozen `UNVERIFIED` row is being verified;
4. a frozen `CONFORMANT` row may change semantic behavior;
5. a normative source changes;
6. a matrix disposition is intentionally changed;
7. the scope of an evaluated obligation changes;
8. previously excluded behavior becomes included;
9. evidence supporting a frozen claim is intentionally replaced with materially different evidence.

A new phase is **not** required merely because another ordinary commit exists.

---

## 9. Test Count Is Not a Governance Gate

Test quantity must never be used as a substitute for semantic evidence.

For example:

```text
460 → 500 tests
```

does not imply:

```text
conformance improved
```

Likewise:

```text
460 → 450 tests
```

does not imply:

```text
conformance regressed
```

The meaningful unit is the evaluated claim and its evidence.

---

## 10. Delta Vocabulary

A future baseline comparison uses the following controlled vocabulary:

| Delta               | Meaning                                                     |
| ------------------- | ----------------------------------------------------------- |
| `UNCHANGED`         | Same semantic disposition and scope                         |
| `IMPROVED`          | Evidence or implementation materially strengthens the claim |
| `REGRESSED`         | Previously supported claim has weakened                     |
| `NEW`               | Newly evaluated claim                                       |
| `REMOVED`           | Previously evaluated claim is no longer in scope            |
| `RECLASSIFIED`      | Disposition changed                                         |
| `SCOPE-CHANGED`     | Evaluation boundary changed                                 |
| `NORMATIVE-CHANGED` | Authoritative source changed                                |

A delta must identify **why** it occurred.

No silent reclassification is permitted.

---

## 11. Residual Finding Protocol

A residual baseline finding is not automatically an actionable defect.

For example:

```text
Baseline:
R14 = PARTIAL
```

does not authorize:

```text
"Fix R14"
```

Instead:

```text
R14 PARTIAL
    ↓
proposal
    ↓
scope decision
    ↓
authorization
    ↓
new phase
    ↓
implementation
    ↓
verification
```

This prevents the baseline from becoming an implicit backlog.

---

## 12. Matrix Governance

The frozen matrix is a historical decision artifact.

Its historical rows must not be rewritten merely because implementation later changes.

If a future evaluation changes a disposition:

```text
baseline-v1 matrix
        +
new evaluation
        ↓
new matrix/state
```

The new matrix must preserve traceability to the old one.

For example:

```text
R14
v1: PARTIAL
v2: PARTIAL
delta: UNCHANGED
reason: unresolved normative transition tension

R10
v1: PARTIAL
v2: CONFORMANT
delta: IMPROVED
reason: execution transition enforcement added and verified
```

---

## 13. Pack Change Protocol

A change to the Prompt Instructions Pack must first be classified as:

```text
editorial
```

or:

```text
normative
```

Editorial changes may be handled without reopening semantic conformance when they demonstrably preserve meaning.

Normative changes require:

1. new pack identity/version;
2. new evaluation scope;
3. new matrix interpretation;
4. new evidence;
5. new conformance assessment.

Historical observations about the previous pack remain historical.

Pack-internal citation drift must not be silently repaired by changing implementation merely to make the implementation conform to an incorrect citation.

---

## 14. Evidence Requirements

Evidence must correspond to the claim being made.

### Documentation change

Require:

- changed artifact;
- semantic-preservation assessment where necessary.

### Refactor

Require:

- targeted behavioral evidence;
- relevant existing tests;
- architecture/import checks where applicable.

### Semantic change

Require:

- explicit affected behavior;
- targeted tests;
- relevant regression tests;
- validation evidence;
- impact assessment.

### Conformance remediation

Require:

- affected matrix row(s);
- normative requirement;
- implementation evidence;
- dedicated tests;
- regression evidence;
- final disposition.

### Normative-source change

Require:

- old source identity;
- new source identity;
- semantic delta;
- revised matrix;
- new evaluation evidence.

---

## 15. Agent Decision Boundary

An agent may:

- discover a possible impact;
- classify a proposed change;
- identify affected baseline rows;
- propose a phase;
- propose tests;
- produce an impact assessment;
- report evidence;
- recommend a disposition.

An agent may not infer authorization merely from discovery.

In particular:

```text
finding ≠ authorization
```

and:

```text
"baseline gap exists"
```

does not mean:

```text
"implementation is authorized to close it"
```

Authorization must come from the governing workflow.

---

## 16. Merge / Release Rule

A normal merge may proceed when:

```text
change classified
+
impact understood
+
required evidence supplied
+
no conformance gate is violated
```

A conformance-affecting merge additionally requires:

```text
explicit scoped phase
+
defined affected rows
+
targeted evidence
+
regression verification
```

A normative-source change additionally requires:

```text
new normative identity
+
new evaluation context
```

---

## 17. Establishing Baseline-v2

A new baseline may be established only when a new evaluated state is intentionally frozen.

Minimum requirements:

1. explicit scope;
2. identified normative source;
3. identified repository state;
4. updated conformance matrix;
5. complete required test evidence;
6. regression assessment;
7. independent re-audit;
8. v1 → v2 delta;
9. unresolved dispositions explicitly recorded;
10. immutable new tag.

The new baseline must not modify `conformance-baseline-v1`.

Conceptually:

```text
conformance-baseline-v1
        │
        │ historical
        ▼
 scoped change/evaluation
        │
        ├── evidence
        ├── tests
        ├── audit
        └── delta
        │
        ▼
 conformance-baseline-v2
```

---

## 18. What Does Not Require a New Baseline

A new baseline is not required for every:

- commit;
- bug fix unrelated to conformance;
- documentation change;
- test addition;
- refactor;
- CLI usability improvement;
- internal restructuring;
- performance improvement.

A baseline is created when a **new evaluated conformance state is intentionally established**, not whenever development occurs.

---

## 19. Canonical Causal History

The preferred historical chain is:

```text
BASELINE v1
    ↓
PROPOSED CHANGE
    ↓
IMPACT ASSESSMENT
    ↓
ORDINARY MERGE
       OR
NEW SCOPED PHASE
    ↓
TESTS
    ↓
IMPLEMENTATION
    ↓
VERIFICATION
    ↓
REGRESSION ASSESSMENT
    ↓
INDEPENDENT RE-AUDIT
    ↓
NEW EVALUATED STATE
    ↓
BASELINE v2
```

Every transition should preserve enough evidence to reconstruct why it occurred.

---

## 20. Example Decisions

### Example A — README typo

```text
Class: A
Impact: NO-IMPACT
Phase: not required
New baseline: no
```

### Example B — Internal function rename

```text
Class: B
Impact: NO-CONFORMANCE-IMPACT
Evidence: existing suite + targeted import/test verification
New baseline: no
```

### Example C — New lifecycle transition

```text
Class: C
Impact: CONFORMANCE-IMPACT
Phase: mandatory
Affected rows: explicitly identified
New baseline: only after evaluation is intentionally frozen
```

### Example D — Implementing a frozen PARTIAL requirement

```text
Class: D
Impact: CONFORMANCE-IMPACT
Phase: mandatory
Baseline-v1: unchanged
Future disposition: evaluated independently
```

### Example E — New Prompt Pack version

```text
Class: E
Impact: NORMATIVE-IMPACT
New pack identity: required
New matrix: required
New evaluation: required
Baseline-v1: unchanged
```

---

## 21. Core Rule

The system must preserve this distinction:

> **A baseline records what was established. Change control determines what may be changed.**

Therefore:

```text
baseline ≠ backlog
baseline ≠ authorization
baseline ≠ implementation plan
baseline ≠ current truth
```

The baseline is **historical truth about a bounded evaluation**.

Current implementation is evaluated separately.

Future conformance is established separately.

No later development may retroactively rewrite the meaning of the frozen baseline.
