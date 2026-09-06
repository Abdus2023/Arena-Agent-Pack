# Arena Final Report

> Template derived from: **Arena Agent Prompt Instructions Pack**, §40 (Arena Final Report Format), governed by §39 (Arena Completion Contract).
> Produce one of these at the end of every substantial Arena operation. Do not mark a task complete unless every "AND" condition in the Completion Contract below is actually satisfied — leave sections `UNKNOWN` / `NOT DONE` rather than fabricating content.

---

## Completion Contract Check (pack §39)

> All must be true before this report can claim the task is complete. If any is false, state so explicitly in the relevant section and set overall status accordingly.

- [ ] Scope known
- [ ] Source identified
- [ ] Repository state identified
- [ ] Work performed
- [ ] Observed result captured
- [ ] Required invariants checked
- [ ] Evidence recorded
- [ ] Failures classified
- [ ] Open ambiguities recorded
- [ ] Final status assigned

Overall status: `COMPLETE / PARTIAL / BLOCKED`

---

# Arena Result

## Identity
- Repository:
- Branch:
- Commit:
- Source:
- Related Repo-Audit ID(s):
- Related Work Item ID(s):

## Objective
<What this operation was asked to accomplish, in the requester's own terms.>

## What Was Actually Observed
<Direct, evidence-backed facts only. No inference, no architecture-as-fact.>

## What Was Inferred
<Explicitly labeled DERIVED conclusions, with the source facts they were derived from.>

## What Was Changed
<Concrete diffs, files, records, or states that were modified, with evidence (commit hash, diff, command output).>

## What Was Not Changed
<Explicitly note anything that was in scope but deliberately left untouched, and why.>

## Knowledge Units
| ID | Status | Evidence |
|---|---|---|
| | | |

## Invariants
| ID | Result | Evidence |
|---|---|---|
| | | |

## Execution
| Action | Result | Evidence |
|---|---|---|
| | | |

## Verification
<Per-requirement PASS/FAIL/PARTIAL/NOT-TESTED/NOT-IMPLEMENTED/BLOCKED/AMBIGUOUS/INAPPLICABLE, each with evidence or counterexample. Reference `arena-work-item-template.md` verification gate tables if used.>

## Failures
<Each failure as an OBSERVED FAILURE at minimum; link to a full `arena-counterexample-template.md` record where reproducibility criteria are met.>

## Open Decisions
<List `ARENA-DECISION-<ID>` links still OPEN.>

## Evidence Gaps
<List anything UNKNOWN and what would resolve it.>

## Recommended Next Action
<Concrete, scoped next step(s) — not a vague "continue investigating".>

---

## No-Claim-Without-Evidence Self-Check (pack §43)

- [ ] No claim without provenance
- [ ] No action without authority
- [ ] No effect without authorization
- [ ] No completion without observation
- [ ] No verification without evidence
- [ ] No semantic change without a decision record
- [ ] No implementation claim without repository proof
- [ ] No recovery claim without causal state
