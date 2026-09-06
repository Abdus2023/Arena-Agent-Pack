# Baseline Preservation & Release Snapshot — the Baseline Protocol

**Status of the conformance campaign: COMPLETE.**
This document is *not* another conformance pass. Part I makes the frozen state
reproducible and unmistakable. Part II formalizes how `arena-agent` — and any
agent working on it — must *interact* with that frozen state going forward,
without ever treating it as either untouchable or as a backlog.

No files beyond this document have been created or changed as part of this
update. `BASELINE.json`, `BASELINE.md`, and `CHANGELOG.md` are described below
as a **future destination**, not created now — see §16 for why, and §24 for
why they still require an actual repository/tag identity to exist first.

---

# Part I — Freezing the Snapshot

## 1. Freeze identity

```text
Conformance campaign: COMPLETE

Tests:                460 / 460
Matrix rows:          72
Regressions:          0
Unparsed:             0

CONFORMANT:           44
PARTIAL:              16
NON-CONFORMANT:        1
UNVERIFIED:            1
NOT-APPLICABLE:       10
                      ──
                      72
```

Arithmetic check: `44 + 16 + 1 + 1 + 10 = 72`. No hidden or unclassified rows.

Full phase roadmap at freeze:

```text
Phase 1–4                         COMPLETE / FROZEN
Phase 5A                          COMPLETE
Phase 5B                          COMPLETE / FROZEN
Phase 5C                          COMPLETE / FROZEN
Phase 6                           COMPLETE
Final Pack Conformance Review     COMPLETE
```

**Open action item (not yet done):** capture the exact repository commit that
contains this precise state (post the two Final-Pack-Conformance-Review
documentation fixes, with `conformance/CONFORMANCE_MATRIX.md` showing
44/16/1/1/10 = 72 and the full suite at 460/460), and create an immutable tag
against it. Until that tag exists, this document describes the *intended*
baseline identity, not yet a *realized* one — see §14.

## 2. Preserve the evidence chain

The baseline is not just a number — it is the full chain that produced it, and
nothing in this chain should be silently regenerated, rewritten, or "cleaned
up" outside an explicit new phase:

```text
arena-agent-instructions-pack-v2.md
        ↓
requirements / templates
        ↓
conformance/CONFORMANCE_MATRIX.md
        ↓
implementation
        ↓
tests
        ↓
460/460 result
        ↓
independent final re-audit
```

## 3. Add a baseline marker

Prefer a repository tag / release marker over another mutable document.

```text
conformance-baseline-v1
```

(or whatever version/release convention the project already uses — the naming
detail is negotiable, the semantics are not.)

The tag means, precisely:

> **The state at which the stated conformance campaign was completed and frozen.**

It does **not** mean perfect conformance, and it does not mean "everything is
CONFORMANT." It means the evidence was gathered, independently re-checked, and
deliberately accepted as the campaign's endpoint.

## 4. Make the residuals explicit

The remaining non-CONFORMANT rows are classified findings, not an accidental
backlog. Each status has a distinct, fixed meaning:

| Status | Meaning |
|---|---|
| `PARTIAL` | Some portion of the requirement is implemented/enforceable, but a defined portion remains outside the current implementation boundary or cannot honestly be machine-verified. A bounded, disclosed limitation — investigated and characterized, not forgotten. Examples: R14 claim expiry, R10 execution-state reconciliation, R16 causal classification-strengthening detection, R4 sampled-coverage inspection proof. |
| `NON-CONFORMANT` | A known, unresolved requirement against the pack. Its existence is part of the truth of the baseline — a matrix where everything mysteriously becomes CONFORMANT is *less* trustworthy than one willing to preserve a negative finding. |
| `UNVERIFIED` | The implementation appears compatible or plausible, but the campaign did not establish sufficient machine-checkable evidence to promote the row to CONFORMANT. `implemented ≠ verified`. Must not be silently upgraded later just because "it obviously works." |
| `NOT-APPLICABLE` | An explicitly scoped-out boundary, not missing work. E.g. R7/R8 were moved here because the package is a record/validate/report/export tool, not an execution engine exercising external effects or authority itself. |

This distinction prevents a future engineer — or future agent — from
interpreting the `16 + 1 + 1 = 18` non-fully-conformant rows as an accidental
backlog of 18 unfinished tasks.

## 5. The reopening rule

```text
FROZEN BASELINE
      │
      ├── observation/documentation
      │        └── does not reopen campaign
      │
      └── ordinary feature work
               └── separate engineering work
                        └── conformance remediation
                                 └── requires explicit new phase
```

Core rule, most compactly:

```text
A residual conformance finding is evidence about the baseline;
it is not authorization to modify the baseline.

Discovery does not imply authorization.
```

## 6. Three clean directions after freezing

**A. Baseline release (recommended immediate next step)**
Tag/archive the 460/460 state and finish the campaign administratively.

**B. Standalone documentation touch-up**
Update the stale `arena_agent_py/README.md` "241 tests" statement. Deliberately
**not** conformance remediation.

**C. New engineering phase**
Open one explicitly scoped problem — e.g. the remaining `NON-CONFORMANT` row —
as its own phase, without altering the frozen baseline except through that
phase's own authorized, re-audited outcome.

## 7. What must NOT be done under the closed campaign's authority

```text
❌ Fix the remaining NON-CONFORMANT row
❌ Convert PARTIAL → CONFORMANT merely because it is desirable
❌ Invent verification for the UNVERIFIED row
❌ Rewrite the pack's section references
❌ Modify the frozen matrix merely for cosmetic improvement
❌ Expand R14 / R10 / R16 beyond their accepted boundaries
❌ Add authority machinery to resolve R7
❌ Add external-effect machinery to resolve R8
❌ Reopen Phase 5A / 5B / 5C
❌ Run another generic "final audit"
```

## 8. Why the pack-internal citation errors stay untouched

```text
§24.1 → references §32   actual Change-Impact Analysis → §36
§9.2  → references §29   actual WorkItem State block   → §27
§24.2 → references §29   actual Lifecycle Log concept  → §27 (no "Lifecycle Log" heading exists in the pack text)
§15.1 → references §33   actual Knowledge Graph        → §34
earlier-known: §37       actual Final Report            → §39/§40
```

These carry a dedicated conceptual category, distinct from both "implementation
defect" and "remediation task":

> **NORMATIVE-SOURCE OBSERVATION** — a characteristic of the normative source
> used by the campaign, not a defect in what was built against it.

Recorded per-item, so a future agent never rediscovers the ambiguity and
resolves it a different, inconsistent way:

```text
Observation:  §24.1 references §32 for Change-Impact Analysis.
Resolution used by campaign:  follow the actual named section/content
                               (§36), not the stale numeric cross-reference.
Status:  accepted observation; pack unchanged; implementation unchanged.
```

A corrected "v2.1" pack, if ever produced, would be its own separate
pack-maintenance project (see §26) — not a continuation of this conformance
campaign, and not an implicit license to bend the implementation to match a
wrong citation.

## 9. The matrix as a governance artifact

`conformance/CONFORMANCE_MATRIX.md` is a **decision artifact**, not merely a
report:

```text
Requirement → Interpretation → Implementation evidence → Test evidence
    → Independent verification → Disposition
```

Changing a disposition later (e.g. `PARTIAL → CONFORMANT`) without reopening
the underlying decision through a new phase would destroy the evidence
discipline the whole campaign was built on.

## 10. The resulting project shape

```text
                    CANONICAL PACK
                          │
                          ▼
                   REQUIREMENTS
                          │
                          ▼
                CONFORMANCE MATRIX
                          │
                          ▼
                    IMPLEMENTATION
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Models      Validation     Storage
             │            │            │
             └────────────┼────────────┘
                          ▼
                     Reporting → Export → HTML → CLI / Operator

                    GOVERNANCE
                         │
                         ▼
                  FROZEN BASELINE
                         │
              ┌─────────┴─────────┐
              ▼                   ▼
      existing evidence     future phases
                                   │
                            explicit decision
```

## 11. Standing lifecycle from here forward

```text
FROZEN CONFORMANCE BASELINE
         │
  explicit new authorization
         │
         ▼
   NEW SCOPED PHASE
         │
investigation → tests first → implementation → targeted verification
         → full regression → independent re-audit
         │
         ▼
NEW BASELINE / EXPLICITLY ACCEPTED CHANGE
```

## 12. Summary of Part I

The project has: canonical vocabulary reconciliation, explicit
implementation-only vocabulary disclosure, lifecycle enforcement,
execution-state transition enforcement, claim-expiry detection, ownership
conflict detection, decision override attribution, TrustTier attribution,
Stop Condition closed-set enforcement, provenance completeness, content-scan
evidence attachment, WorkItem persistence semantics, Wiki derivation,
deterministic export, a pure HTML projection, architecture-direction
enforcement, CLI/storage/E2E checks, 460 regression tests, an independent
final audit, explicitly disclosed residual limitations, and a synchronized
72-row matrix. More importantly, the project now knows **what it does not know
or enforce** — often more valuable than accumulating more code.

---

# Part II — From Frozen Baseline to a Baseline Protocol

Part I answers *"what was true when the campaign ended?"* Part II answers the
next question: *"how must future work interact with that truth?"* — turning
the snapshot into an operational contract rather than a static report.

The protocol answers four questions:

1. What exactly is frozen?
2. How do we know a later checkout derives from it?
3. When does a change remain ordinary work?
4. When does a change require an explicit new conformance decision?

## 13. Baseline ≠ branch ≠ release

Three concepts worth keeping separate:

| Concept | Definition |
|---|---|
| **Baseline** | A verified historical state (`460/460`, 72 requirements, `44/16/1/1/10`). Immutable as a decision artifact. |
| **Development branch** | A place where new work happens. May diverge from the baseline. |
| **Release** | A product/version decision. May or may not coincide with a conformance baseline. |

```text
Frozen conformance baseline
        │
        ├── development branch A
        ├── documentation branch
        └── future remediation branch
```

A future commit can be **better software** while simultaneously being
**different from the frozen conformance baseline** — that is not a
contradiction, it's the whole point of separating the three concepts.

## 14. The baseline identity is a tuple, not a number

`460/460` is useful, but it is not the baseline by itself. Reproducible
evidence requires knowing *which source state* produced those numbers:

```text
B = (
    repository_identity,   -- commit / tag
    pack_identity,          -- exact v2 artifact used
    matrix_identity,        -- exact frozen CONFORMANCE_MATRIX.md
    test_identity,          -- exact suite + result
    disposition_set         -- 44 / 16 / 1 / 1 / 10, per-row
)
```

`460/460` without knowing which source state produced those tests is weak
evidence. `baseline-v1 → commit X → pack V2 → matrix M → 460/460 →
44/16/1/1/10` is reproducible. A future audit can then ask **"are we
evaluating the same thing?"** before asking **"is it still conformant?"**

A future agent should be able to answer all of:

1. Which repository state?
2. Which pack (exact version/content)?
3. Which matrix?
4. Which tests?
5. Which Python/tooling environment?
6. Which residual dispositions?
7. Which known pack ambiguities (§8)?
8. Which scope exclusions?

That turns "someone once said 460 tests passed" into **reconstructable
evidence**.

## 15. Baseline identity must be immutable

Once `conformance-baseline-v1` is created, it should never be moved to
another commit. If a mistake is discovered later, don't move the tag —
create a new one:

```text
baseline-v1
    └── historical truth (unchanged forever)

baseline-v2
    └── new evaluated state
```

Same principle as preserving an audit record rather than rewriting history —
already the standing rule for this matrix's own Changelog (three-part
correction structure, never silent overwrite).

## 16. A baseline manifest — and the trap of adding one carelessly

A useful *future* artifact is a small machine-readable manifest:

```json
{
  "baseline": "conformance-baseline-v1",
  "pack": "arena-agent-instructions-pack-v2",
  "matrix_rows": 72,
  "tests_passed": 460,
  "tests_total": 460,
  "regressions": 0,
  "unparsed": 0,
  "conformance": {
    "CONFORMANT": 44,
    "PARTIAL": 16,
    "NON-CONFORMANT": 1,
    "UNVERIFIED": 1,
    "NOT-APPLICABLE": 10
  },
  "campaign_status": "COMPLETE"
}
```

This file must **describe** the baseline, never dynamically recompute it —
otherwise it recreates the exact failure mode this campaign repeatedly
eliminated elsewhere: *a derived artifact pretending to be historical
evidence.*

There is also an architectural trap: the project already has Pack → Matrix →
Tests → Implementation as sources that must not independently drift. Adding
`BASELINE.json` as a *sixth*, separately-hand-maintained source would recreate
"the gate that prevents hand-maintained lists from drifting was itself a
hand-maintained list with a hole." Its role must stay strictly downstream:

```text
Pack → Matrix → Baseline manifest       (manifest summarizes the matrix)
```

or, if generated:

```text
Frozen matrix → baseline snapshot       (mechanically derived, not hand-typed)
```

It should never become a second, independently-edited conformance matrix.

**Not created now** — see §24 for why (no repository tag exists yet to anchor
it to).

## 17. Immutable evidence categories

Restating §14's tuple as five distinct things worth freezing:

| | Category | What it captures |
|---|---|---|
| A | Source identity | The Git commit |
| B | Requirement identity | The exact pack version/content used |
| C | Matrix identity | The exact matrix at completion |
| D | Test identity | The exact test suite and result |
| E | Decision identity | The explicit residual dispositions |

## 18. Baseline comparison must be causal, not numeric

Suppose six months from now there are 510 tests and 74 requirement rows.
That does **not** automatically mean the project improved. The comparison
must be:

```text
BASELINE V1: 460 tests, 72 rows, 44 C / 16 P / 1 NC / 1 UV / 10 N/A
                              ↓
CURRENT STATE: 510 tests, 74 rows, ...
```

then ask **what changed**, not merely "what's the new percentage":

```text
requirements added          implementation changed
requirements removed        tests added
requirements reinterpreted  residuals resolved
scope changed               new residuals introduced
pack changed
```

This preserves causality instead of collapsing history into a single score.

## 19. Pack changes must be treated as their own axis

If the pack later becomes `arena-agent-instructions-pack-v2.1` with a new
requirement, the new matrix cannot be compared against the old one as though
nothing changed:

```text
v2 → baseline V1
        │
   pack evolves
        ▼
v2.1 → new conformance campaign → baseline V2
```

A conformance result is only meaningful together with its normative input:
`pack version + implementation state + evaluation methodology`. A result
without its normative input is incomplete.

## 20. Preserve dispositions as categories, not a score

Explicitly avoid ever collapsing the matrix into something like
`Conformance = 61%` or `84.7%`. That destroys real distinctions:

- `PARTIAL` is not "half correct."
- `UNVERIFIED` is not "probably wrong."
- `NOT-APPLICABLE` must never be counted as failure.

The categorical result — `44 demonstrated / 16 bounded / 1 unresolved / 1
unverified / 10 outside scope` — is strictly more informative than any single
percentage, and must remain the reporting format.

## 21. Baseline delta, once a second baseline exists

The useful artifact after further work is not another full audit from
scratch — it's a **delta** against the parent baseline:

```text
BASELINE V1              NEW WORK              BASELINE V2
───────────                                    ───────────
R14  PARTIAL         ─────────────────►        R14  CONFORMANT
R10  PARTIAL                                   R10  PARTIAL
R16  PARTIAL                                   R16  PARTIAL
R7   N/A                                       R7   N/A
R1   PARTIAL                                   R1   PARTIAL
```

```text
R14 PARTIAL → CONFORMANT
Reason:   claim-expiry semantics completed under new policy contract.
Evidence: <link/reference>
Tests:    <new tests added>
```

Far easier to audit than reconstructing the entire history from scratch.

## 22. Delta analysis must detect regressions too

If a later baseline shows `R14 CONFORMANT / R10 PARTIAL / R16
NON-CONFORMANT`, the important discovery is not "R14 improved" — it's "R16
regressed." Every delta must be classified per-row as one of:

```text
UNCHANGED   IMPROVED   REGRESSED   NEW   REMOVED   RECLASSIFIED   SCOPE-CHANGED
```

A regression is exactly as reportable as an improvement — the campaign's
credibility depends on treating both symmetrically.

## 23. Test count is not a quality metric

`460 → 600` tests does not by itself mean the project got better; tests can
increase because of new functionality, previously-uncovered gaps, test
splitting, redundant additions, or expanded requirements. Conversely,
`460 → 430` can be perfectly legitimate if tests were consolidated. The
meaningful comparison is always `requirements + behavior + evidence +
coverage + residuals`, never raw test-count inflation.

This guards against **"test theater"** — adding tests until the number looks
impressive. The campaign's invariant has always been:

```text
Requirement → specific behavior → specific test → evidence
```

The 460 count is an *output* of that process, never the objective itself.

## 24. Code volume is not a quality metric either

The same caution applies to implementation size. The campaign's repeated,
correct instinct was the **smallest justified change**, not "add
infrastructure to look more conformant":

```text
R12 required one provenance field.
R15 required a closed Stop Condition map.
R19 required a small enum and validation.
R21 required optional cross-record resolution.
R17 required explicit related Decision IDs.
R8 / R7 required scope disclosures rather than invented machinery.
```

That pattern must survive past the campaign's close, into every future
phase.

## 25. Architectural restraint is itself a preserved property

One of the campaign's strongest outcomes is not any individual feature — it
is the repeated, deliberate refusal to implement semantics the evidence did
not justify:

```text
R4  → no fake sampled-inspection heuristic
R7  → no invented authority algebra
R8  → no fake External Effect Contract
R14 → no lifecycle bypass
R10 → no staleness heuristic
R16 → no invented classification-history mechanism
```

Standing rule, worth stating as a first-class agent instruction:

> **When the evidence does not support a semantic claim, preserve the
> limitation instead of manufacturing machinery to make the matrix green.**

## 26. Change Classification System

Future changes should be classified before deciding how much ceremony they
need — not every change is "Phase 7":

| Class | Description | Example |
|---|---|---|
| **A** | Documentation | Fix README's stale "241 tests" |
| **B** | Non-semantic implementation | Improve HTML formatting without changing meaning |
| **C** | Behavioral change | Change CLI behavior |
| **D** | Conformance remediation | Resolve R14 claim expiry completely |
| **E** | Pack/normative-source change | Correct §24.1's stale section reference in the pack itself |

Each class carries a different review burden. Class A/B changes never touch
the frozen baseline's meaning; Class D/E changes always require an explicit
new phase (D) or a separate pack-maintenance project (E, see §8).

## 27. Conformance Impact Assessment (a lightweight bridge, not a new phase)

Not implemented now — the next conceptual layer between everyday engineering
and formal remediation. A lightweight assessment for any change that
*touches* frozen territory would ask:

```text
1. Which frozen baseline is the parent?
2. Which files/components change?
3. Which matrix rows could be affected?
4. Does the normative interpretation change?
5. Does the demonstrated behavior change?
6. Does the evidence remain valid?
7. Does the residual disposition change?
8. Is a new conformance phase required?
```

## 28. Impact ≠ remediation

A change can touch a requirement's code without requiring remediation:

```text
Change: refactor ExecutionState enum implementation without changing behavior (R10)
Impact: yes — R10 code touched.
Semantic change: no.
Evidence: still valid.
Remediation: no.
```

versus:

```text
Change: allow ISSUED → RECONCILED directly (R10)
Impact: yes.
Semantic change: yes.
Frozen R10 claim: potentially invalidated.
New conformance decision: required.
```

This distinction prevents bureaucracy on harmless changes while preserving
rigor on semantic ones. The overall decision rule is proportional, not
absolute:

```text
change
   │
   ├── does it alter a frozen semantic claim?
   │
   ├── NO  → ordinary engineering
   └── YES → explicit conformance-impact decision
```

A typo fix is not equivalent to changing lifecycle semantics. A new renderer
feature is not automatically a pack revision. A new test is not automatically
a new conformance campaign.

## 29. Decision procedure for a future agent receiving a task

```text
REQUEST
   │
   ▼
Does it touch frozen conformance semantics?
   │
   ├── NO  → ordinary engineering
   │
   └── YES
        │
        ▼
     Identify affected matrix row(s)
        │
        ▼
     Does the request explicitly authorize conformance remediation?
        │
        ├── NO  → STOP / clarify scope
        │
        └── YES → create new phase
```

The critical branch is **STOP / clarify scope**, not "I'll just fix it while
I'm in there." That is the same discipline already enforced throughout the
campaign (stop-and-reconcile before implementing on any design ambiguity).

## 30. The baseline is a reference layer, not a lifecycle state

Two explicit architectural non-decisions, stated so they are never
accidentally reversed:

- **Do not** add `BaselineState` or `CONFORMANCE_BASELINE` to `WorkItem`'s
  lifecycle vocabulary (`PLANNED`/`EXECUTING`/`VERIFIED`/etc.). The baseline
  is a governance/reference artifact, not a state any record moves through —
  conflating the two would blur domain lifecycle semantics with audit
  history.
- **Do not** turn `validation.py` into a baseline-management engine. Keep the
  five-role layering (`models.py → validation.py → storage/reporting → export
  → html → CLI`) exactly as it is; baseline identity lives at the
  conformance/governance layer, outside that stack. Otherwise the application
  would start depending on its own historical audit state — backwards.

## 31. A possible future directory (destination, not a task)

```text
conformance/
├── CONFORMANCE_MATRIX.md      -- the detailed 72-row decision artifact
├── BASELINE.json              -- machine-readable identity + summary
├── BASELINE.md                -- short human-readable explanation
└── CHANGELOG.md               -- historical evolution of conformance decisions
```

**Do not create these merely because they sound useful.** The frozen baseline
first needs an actual repository/tag identity (§3, §15) to anchor
`BASELINE.json`/`BASELINE.md` to — creating them against an unrealized tag
would itself be exactly the kind of "artifact pretending to be historical
evidence" §16 warns against.

If eventually created, `BASELINE.md` should not duplicate the matrix — it
should be small, e.g.:

```text
CONFORMANCE BASELINE

This directory records the frozen endpoint of the Arena Agent Prompt
Instructions Pack v2 conformance campaign.

Baseline:     conformance-baseline-v1
Tests:        460/460
Matrix:       72 rows
Disposition:  44 CONFORMANT
              16 PARTIAL
               1 NON-CONFORMANT
               1 UNVERIFIED
              10 NOT-APPLICABLE

This baseline is historical and immutable. Residual findings are not
automatically authorized work items. Any remediation requires an explicitly
scoped future phase.
```

The matrix remains the detailed authority; the manifest and README only
summarize it.

## 32. What happens as the repository moves past the tag

```text
baseline-v1
    ├── commit A
    ├── commit B
    ├── commit C
    └── current HEAD
```

Current HEAD is no longer literally the baseline — that's fine and expected.
The only question that matters is: **has current HEAD invalidated any
baseline claim?** That's an impact question (§27–§28), never an assumption
either way.

- A feature that doesn't alter tested semantics (e.g. `arena report diff`)
  coexists fine — baseline V1 simply remains valid as historical evidence, no
  "Phase 7" required just because a file changed.
- A feature that does alter tested semantics (e.g. modifying lifecycle
  transition rules) requires identifying the affected rows and evaluating
  impact — but still not necessarily rerunning the whole campaign; the
  process should be proportional to the actual scope affected.

## 33. The final conceptual model — four layers

```text
                NORMATIVE LAYER
                      │
                   Pack v2
                      │
                      ▼
               EVALUATION LAYER
                      │
                72-row matrix
                      │
                      ▼
                BASELINE LAYER
                      │
              460/460 frozen state
                      │
                      ▼
               ENGINEERING LAYER
                      │
             future repository changes
```

Rule between the last two layers:

> Engineering changes may diverge from the baseline, but may not silently
> rewrite what the baseline means.

## 34. The governing rule

If only one rule survives from the entire campaign, it is this:

```text
┌────────────────────────────────────────────────────┐
│                    BASELINE RULE                    │
│                                                      │
│  A frozen conformance result is historical          │
│  evidence, not an implicit backlog.                 │
│                                                      │
│  Discovery does not authorize remediation.          │
│                                                      │
│  Any change to a residual finding requires          │
│  explicit new scope and a new decision.             │
└────────────────────────────────────────────────────┘
```

This is particularly important now that the project is developed in an
**agentic** manner: future agents must inherit not only the code and tests,
but the discipline governing *when they are allowed to change what has
already been established.*

## 35. Recommended sequence from here

```text
STEP 1  Identify exact Git commit
STEP 2  Create immutable baseline tag ("conformance-baseline-v1")
STEP 3  Record baseline identity (this document + eventual BASELINE.json)
STEP 4  Preserve final matrix (already done — conformance/CONFORMANCE_MATRIX.md)
STEP 5  Preserve final test result (460/460, already reproducible via `pytest`)
STEP 6  Record residual dispositions (already done — §4 above, matrix Changelog)
STEP 7  Declare campaign CLOSED (already declared)
STEP 8  Only then begin unrelated/new work
STEP 9  Do NOT automatically fix README. Do NOT automatically fix
        NON-CONFORMANT. Do NOT automatically resolve PARTIAL. Do NOT modify
        the pack. Each remains an independent, separately-authorized decision.
```

Steps 4–7 are already satisfied by the completed campaign and this document.
**Steps 1–2 remain the only concrete, not-yet-executed action**: this sandbox
workspace has no git history/tag mechanism wired up for a real release
process, so creating the actual immutable tag is an external action for
whatever VCS/release tooling the project uses outside this workspace — this
document is what that tag should point at and what it should be understood to
mean once created.

## 36. Endpoint

The campaign does not end with "find the next problem." It ends with "we have
established a trustworthy reference state." Future work can now be creative
again — improving the CLI, reporting, integrations, new domain models — while
the frozen baseline remains behind it as an anchor, not a cage:

```text
                 FROZEN BASELINE
                        │
           explicit future decisions
                        │
        ┌───────────────┼───────────────┐
        ▼                ▼                ▼
   documentation     feature work     remediation
   (Class A/B)        (Class B/C)      (Class D/E,
        │                │              new phase)
        ▼                ▼                ▼
    separate          separate         separate
    change             change           phase
```
