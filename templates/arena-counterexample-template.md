# Arena Counterexample / Failure Record

> Template derived from: **Arena Agent Prompt Instructions Pack**, §22 (Differential Verification), §23 (Failure Reproducibility Contract), §36 (Prompt: Arena Counterexample Minimizer).
> Create one record per meaningful failure. A failure without sufficient reproduction metadata is an **OBSERVED FAILURE**, not automatically a **REPRODUCIBLE DEFECT** — the two sections below keep that distinction explicit.

---

## Record Identity

| Field | Value |
|---|---|
| Counterexample ID | `ARENA-CE-<yyyymmdd>-<seq>` |
| Status | OBSERVED FAILURE / REPRODUCIBLE DEFECT |
| Related Work Item(s) | |
| Related Knowledge Unit(s) | |
| Related Decision Record(s) | |
| Raised by | |
| Timestamp | |

---

## Section 1 — Observed Failure (always fill this in first)

| Field | Value |
|---|---|
| Source revision | |
| Environment | |
| Action / command that failed | |
| Expected behavior | |
| Actual behavior | |
| Immediate evidence (stdout/stderr/log excerpt) | |

> If the fields below (seed, generator version, isolated input, execution trace) are not yet available, stop here and mark Status = `OBSERVED FAILURE`. Do not upgrade to `REPRODUCIBLE DEFECT` without them.

---

## Section 2 — Reproducible Defect (fill in once reproduction is confirmed)

| Field | Value |
|---|---|
| Identity | |
| Source revision | |
| Environment | |
| Seed | |
| Generator version | |
| Input (exact) | |
| Execution trace | |
| Observations | |
| Expected behavior | |
| Actual behavior | |
| First divergence | |
| Classification | PRODUCTION_DEFECT / REFERENCE_DEFECT / HARNESS_DEFECT / SPECIFICATION_AMBIGUITY / ENVIRONMENT_FAILURE / INFRASTRUCTURE_FAILURE / UNRESOLVED |
| Minimized reproducer | |

### Confirmed reproduction
- [ ] Re-run independently produces the same first divergence
- [ ] Reproduction command recorded below

```
<exact reproduction command>
```

---

## Section 3 — Differential Verification Detail (if applicable — production vs. reference comparison)

| Field | Value |
|---|---|
| Production trace | |
| Reference trace | |
| Normalized observation vectors compared | values / errors / state transitions / scheduler trace / effect trace / resource deltas / capability observations / persistence records / recovery outcome / host interaction |
| First divergence (normalized) | |
| Divergence classification | PRODUCTION_DEFECT / REFERENCE_DEFECT / HARNESS_DEFECT / SPECIFICATION_AMBIGUITY / ENVIRONMENT_FAILURE / INFRASTRUCTURE_FAILURE / UNRESOLVED |

---

## Section 4 — Minimization Record (pack §36)

> The minimized case must remain independently reproducible and must NOT strip away the triggering authority condition, resource boundary, state transition, persistence condition, scheduler ordering, effect lifecycle, or first divergence.

| Field | Value |
|---|---|
| Original case | |
| Minimized case | |
| Removed structure (what was safely dropped) | |
| Preserved invariant(s) (what was kept and why) | |
| First divergence (confirmed unchanged after minimization) | |
| Reproduction command (minimized) | |

### Minimization safety checklist
- [ ] Triggering authority condition preserved
- [ ] Resource boundary preserved
- [ ] State transition preserved
- [ ] Persistence condition preserved
- [ ] Scheduler ordering preserved
- [ ] Effect lifecycle preserved
- [ ] First divergence unchanged

---

## Resolution

| Field | Value |
|---|---|
| Resolution status | OPEN / FIXED / WONT-FIX / DUPLICATE / SPECIFICATION-CLARIFIED |
| Fix reference (commit/PR) | |
| Verified fixed by re-running minimized reproducer? (Y/N + evidence) | |
| Linked decision record (if SPECIFICATION_AMBIGUITY) | |
