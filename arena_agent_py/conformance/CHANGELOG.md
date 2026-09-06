# Conformance Changelog

This file is a short, chronological pointer to how the conformance campaign
evolved. The detailed evidence for every entry below lives in
`CONFORMANCE_MATRIX.md`'s own `### Changelog` section (inside the "Baseline
record" heading) — this file does not duplicate that detail, it only orients
a reader to where each milestone sits and what the tally was at each point.

| Milestone | Tests | Rows | C / P / NC / UV / N-A | Status |
|---|---|---|---|---|
| Pre-Phase-5A baseline | — | 72 | 33 / 16 / 9 / 6 / 8 | historical |
| Post-R13 | — | 72 | 34 / 15 / 9 / 6 / 8 | historical |
| Post-R9 | — | 72 | 35 / 14 / 9 / 6 / 8 | historical |
| Post-Phase-5A batch (final) | — | 72 | 39 / 15 / 9 / 1 / 8 | Phase 5A COMPLETE |
| Post-Phase-5B R3+R15 | — | 72 | 40 / 14 / 9 / 1 / 8 | historical |
| Post-Phase-5B R3+R15+R19 | — | 72 | 41 / 13 / 9 / 1 / 8 | historical |
| Post-Phase-5B R3+R15+R19+R21 | 344/344 | 72 | 42 / 13 / 8 / 1 / 8 | historical |
| Post-Phase-5B (+R17) | — | 72 | — | Phase 5B COMPLETE / FROZEN |
| Post-Phase-5C (R8→R4→R18→R2) | 449/449 | 72 | 44 / 15 / 2 / 1 / 10 | Phase 5C COMPLETE / FROZEN |
| Post-Phase-6 (R14→R10→R16→R7→R1) | 460/460 | 72 | 44 / 16 / 1 / 1 / 10 | Phase 6 COMPLETE |
| Final Pack Conformance Review | 460/460 | 72 | 44 / 16 / 1 / 1 / 10 | **conformance-baseline-v1** |

Two documentation-only defects were found and corrected during the Final Pack
Conformance Review itself (no behavioral or test change): the matrix's own
"## Summary tally" section had gone stale after Phase 5B and was not updated
through Phases 5C/6; and row 1.3 cited a nonexistent finding-code name. Both
are recorded with full "Original claim / Correction / Resolution" detail in
`CONFORMANCE_MATRIX.md`'s Changelog.

## Baseline tags

| Tag | Commit | Meaning |
|---|---|---|
| `conformance-baseline-v1` | `3ba15de915b3f99ad51c520ac4e2b3a901a780f4` | Frozen endpoint of the Final Pack Conformance Review: 460/460 tests, 72 matrix rows, 44/16/1/1/10 disposition. Immutable — never moved. |

Future baselines (`conformance-baseline-v2`, etc.), if ever cut, are appended
here as new rows, never by editing or replacing the row above. See
`BASELINE_PRESERVATION_PLAN.md` §21–22 for how a baseline delta between two
tags should be read (per-row UNCHANGED / IMPROVED / REGRESSED / NEW / REMOVED
/ RECLASSIFIED / SCOPE-CHANGED classification), and §26–29 for how to decide
whether an incoming change is ordinary engineering or requires a new,
explicitly scoped conformance phase before it can move a residual row.

The operational rules for evaluating every post-baseline change are codified
in `CHANGE_CONTROL_CONTRACT.md`: change classes A–E, the Baseline Impact
Assessment and its four outcomes (NO-IMPACT / IMPACTED-BUT-NOT-CONFORMANCE /
CONFORMANCE-IMPACT / NORMATIVE-IMPACT), mandatory new-phase triggers,
evidence requirements per change class, the agent/human decision boundary,
merge and release gates, and the minimum requirements for establishing
`conformance-baseline-v2`. That contract governs future work; it does not
alter any historical row above.
