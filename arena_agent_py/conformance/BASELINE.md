# Conformance Baseline

This directory records the frozen endpoint of the Arena Agent Prompt
Instructions Pack v2 conformance campaign.

```
Baseline:     conformance-baseline-v1
Commit:       3ba15de915b3f99ad51c520ac4e2b3a901a780f4
Tests:        460/460
Matrix:       72 rows
Disposition:  44 CONFORMANT
              16 PARTIAL
               1 NON-CONFORMANT
               1 UNVERIFIED
              10 NOT-APPLICABLE
```

This baseline is historical and immutable. The `conformance-baseline-v1` tag
must never be moved to another commit; a correction, if ever needed, is
recorded via a new tag (`conformance-baseline-v2`, etc.), never by relocating
this one.

Residual findings are not automatically authorized work items. `PARTIAL`,
`NON-CONFORMANT`, and `UNVERIFIED` rows are disclosed, classified findings
about this baseline — not an implicit backlog. Any remediation of a residual
finding requires an explicitly scoped future phase, investigated,
implemented, tested, and independently re-audited on its own terms, resulting
in a new baseline if accepted.

## Files in this directory

| File | Role |
|---|---|
| `CONFORMANCE_MATRIX.md` | The detailed 72-row decision artifact — the authoritative record of every requirement, its interpretation, implementation evidence, test evidence, and disposition. |
| `BASELINE.json` | A post-baseline machine-readable identity and summary manifest for `conformance-baseline-v1`. It records the frozen commit and matrix/test identity; it was added after the frozen commit and does not alter that historical state. |
| `BASELINE.md` | This file — a post-baseline human-readable pointer to the baseline's identity and meaning. |
| `CHANGELOG.md` | A post-baseline chronological pointer to campaign milestones and the baseline-tag table; future baseline tags are appended as new rows, never replacing the v1 row. |
| `BASELINE_PRESERVATION_PLAN.md` | The full Baseline Protocol: what "frozen" means, how residual statuses must be read, the reopening rule, the change-classification system, and the principles behind governance of all future work touching this territory. |
| `CHANGE_CONTROL_CONTRACT.md` | The operational post-baseline change-control contract: change classes A–E, the Baseline Impact Assessment and its four outcomes, mandatory new-phase triggers, v1→v2 delta vocabulary, residual-finding and pack-change protocols, evidence requirements, the agent decision boundary, merge/release gates, and the conditions for establishing baseline-v2. Codifies the rules foreshadowed in Part II of the Baseline Protocol. Does not modify this baseline. |

## Frozen-evidence distinction

The frozen evidence chain is:

```text
conformance-baseline-v1
        ↓
3ba15de915b3f99ad51c520ac4e2b3a901a780f4
        ↓
CONFORMANCE_MATRIX.md at that frozen repository state
```

`BASELINE.json`, `BASELINE.md`, `CHANGELOG.md`, and
`CHANGE_CONTROL_CONTRACT.md` are post-baseline governance artifacts. They may
describe or govern the frozen baseline, but their later creation does not
retroactively make them files of the frozen commit.

## The one rule

> A frozen conformance result is historical evidence, not an implicit
> backlog. Discovery does not authorize remediation. Any change to a
> residual finding requires explicit new scope and a new decision.
