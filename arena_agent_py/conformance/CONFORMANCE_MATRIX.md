# Repository-Wide Conformance Audit — Arena Agent Pack v2.0.0

**Audit date:** 2026-09-06
**Auditor:** this session, applying the pack's own Verification Model (§20) to the implementation
**Scope:** `arena_agent/` (all modules) + `tests/` (all suites), against
`arena-agent-instructions-pack-v2.md` (the canonical spec — see Appendix C
changelog note in that document; v1 is superseded but both remain
independently referenceable per standing project instruction).
**Method:** static cross-reference of every `§`-tagged comment/docstring in
the implementation against the pack section it cites, followed by reading
the cited pack section itself to check the citation is accurate (not just
present), followed by checking that a named test actually exercises the
claimed behavior (not just that a test file exists).

**Non-goal:** this audit does not redesign anything. Where it finds a gap,
it records the gap and a suggested disposition; it does not close the gap
unless directed to in a later turn.

## Baseline record

This matrix is accepted as the current conformance baseline, not a to-do
list to clear wholesale. Per explicit direction, the 22 recommendations
below are triaged into three separate classes of work — evidence/test
hardening, small normative enforcement gaps, and new semantic subsystems
deserving their own design phases — executed as a controlled, re-audited
sequence rather than as simultaneous changes across semantic layers (doing
the latter would make it impossible to attribute a future conformance
regression to a specific change).

```
Pack: Arena Agent Instructions Pack v2.0.0
Implementation: arena-agent
Phases frozen: 1-4
Tests: 460/460 PASS
Conformance rows: 72

  CONFORMANT          44
  PARTIAL             16
  NON-CONFORMANT       1
  UNVERIFIED           1
  NOT-APPLICABLE      10
```

**Self-correction note (found while preparing the R9 update):** re-parsing
this document's own tables mechanically (the same method this audit uses
throughout, precisely to catch exactly this kind of error) showed that the
"34 CONFORMANT / 16 PARTIAL / ... / 5 UNVERIFIED" figure stated in the
previous turn's prose was a transcription error, not a re-verified count —
the file's actual post-R13 rows summed to 34 CONFORMANT / **15** PARTIAL /
9 NON-CONFORMANT / **6** UNVERIFIED / 8 NOT-APPLICABLE. R9 then moved row
1.28 from PARTIAL to CONFORMANT, giving the 35/14/9/6/8 total above, which
*is* freshly re-derived from the file as it stands right now (see the
Changelog for the exact recount command's output). This correction is
recorded here rather than silently overwritten, consistent with the
audit's own standard: no tally is asserted without being machine-recounted
against the document it describes.

**Roadmap** (adopted; **all of Phase 5A is now complete** — R13, R9, and
the R5/R6/R11/R12/R20/R22 batch — see the Changelog below; **Phase 5B is
FROZEN** — R3, R15, R19, R21, and R17 are all DONE, in the locked
execution order R3 → R15 → R19 → R21 → R17, and independently re-audited
with zero downgrades (see the Phase 5B re-audit Changelog entry);
**Phase 5C is now FROZEN** — R8 → R4 → R18 → R2, locked order, all four
DONE and independently re-audited with zero downgrades, one prose-only
drift found and fixed (see the Phase 5C re-audit Changelog entry);
**Phase 6 is now COMPLETE** — R14 → R10 → R16 → R7 → R1, locked order, all
five DONE; R14 is DONE (row 2.16 moves NON-CONFORMANT → PARTIAL), R10 is
DONE (row 2.2 moves NON-CONFORMANT → PARTIAL), R16 is DONE (row 3.4 moves
NON-CONFORMANT → PARTIAL), R7 is DONE (row 1.25 moves NON-CONFORMANT →
NOT-APPLICABLE-by-disclosed-scope; documentation-only, mirrors R8's §13
resolution), and R1 is DONE (row 1.5 moves NON-CONFORMANT → PARTIAL; new
`TrustTier` enum + `DecisionRecord.decided_by_trust_tier`, scoped narrowly
to §26.2's override attribution)):

```
CONFORMANCE BASELINE (this document, original form)
        |
        v
Phase 5A -- Evidence Hardening -- COMPLETE
        |
        +-- R13  [DONE -- see Changelog]
        +-- R9   [DONE -- see Changelog]
        +-- R5 / R6 / R11 / R12 / R20 / R22  [ALL DONE -- see Changelog]
        |
        v
Phase 5B -- Closed-Set / Cross-Record Hardening (locked order) -- FROZEN
        |
        +-- R3   [DONE -- see Changelog]
        +-- R15  [DONE -- see Changelog]
        +-- R19  [DONE -- see Changelog]
        +-- R21  [DONE -- see Changelog]
        +-- R17  [DONE -- see Changelog]
        |
        v
   Re-audit  [DONE -- 0 downgrades, 1 stale-count drift found & fixed]
        |
        v
Phase 5C -- Small never-sequenced Class-2 items (locked order) -- FROZEN
        |
        +-- R8   [DONE -- see Changelog]
        +-- R4   [DONE -- see Changelog]
        +-- R18  [DONE -- see Changelog]
        +-- R2   [DONE -- see Changelog]
        |
        v
   Re-audit  [DONE -- 0 downgrades, 1 prose-only drift found & fixed (R18 row 3.6)]
        |
        v
Phase 6 -- Coordination + Execution Semantics (locked order) -- COMPLETE
        |
        +-- R14  Sec.24 ownership/claim expiry [DONE -- see Changelog]
        +-- R10  Sec.15 execution-state reconciliation [DONE -- see Changelog]
        +-- R16  Sec.26.2 override/strengthening link [DONE -- see Changelog]
        +-- R7   Sec.11 Authority Contract [DONE -- see Changelog]
        +-- R1   Sec.3  TrustTier [DONE -- see Changelog]
        |
        v
   Re-audit
        |
        v
Final Pack Conformance Review
```

**Standing architectural constraint carried into every future phase:**
none of this work moves validation into `models.py`, `cli.py`, `export.py`,
or `html.py`. New cross-record checks belong in `validation.py`, following
the same explicit-reference pattern already established by
`validate_wiki_references()`. `models -> validation -> storage/reporting ->
export -> html -> CLI presentation` remains the one-way layering.

**§13 (External Effect Contract) disposition:** rather than manufacturing
an External Effect subsystem merely to obtain a green matrix cell, the
adopted position is to document (R8, Phase 5C) that `arena-agent` is
deliberately a record/validation/reporting system, not an execution
engine, and that §13 is out of scope for that reason. This keeps §13 at
NOT-APPLICABLE-by-disclosed-scope rather than converting it into
NON-CONFORMANT-by-omission or building unneeded scope to close it. The
disclosure itself now lives in code (`arena_agent`'s package docstring
and `WorkItem`'s docstring), not just in this matrix -- see row 1.27 and
the Changelog entry for R8.

### Changelog

- **Phase 5A / item 1 (R13) — DONE.** Added
  `tests/test_cli.py::test_work_claim_rejects_second_owner_while_active`:
  a dedicated negative-path test proving that an `ACTIVE` claim by owner A
  rejects a second claim by owner B (non-zero exit, current owner named in
  both plain-text and `--json` output), leaves the `Ownership` record
  (`owner`/`status`/`claimed_at`) byte-for-byte unchanged, and that owner A
  can still act afterward (proving no partial state corruption occurred
  underneath the observable rejection). No implementation code changed —
  `cli.py`'s existing `work_claim` rejection (lines ~389-397) was already
  correct; only the missing executable evidence was added. Row 2.15
  upgraded from PARTIAL/UNVERIFIED to CONFORMANT. Full suite: 242/242
  passing (241 prior + this one).

- **Phase 5A / item 2 (R9) — DONE.** Added `tests/test_architecture.py`
  (4 tests): a project-wide, AST-only generalization of
  `test_html.py::test_html_module_does_not_import_storage_or_validate_or_derive`
  to every module in `arena_agent/`, per the exact 9-step scope given for
  this task:
  1. An explicit `ALLOWED_IMPORTS` table defines the authoritative
     per-module dependency rules (the layering documented at the top of
     the file), with `vocab`/`ids` as universal leaf dependencies and
     `graph` treated as a shared low-level value type rather than a policy
     layer (same status as `vocab`/`ids`, since `validation`/`storage`/
     `reporting` all legitimately hold a `KnowledgeGraph` value).
  2–3. `ast.parse` extracts only local `arena_agent.*` imports from each
     module's source text; the parser never imports/executes
     `arena_agent` itself, so a real circular-import wouldn't be
     accidentally papered over by Python's own import-order tolerance.
  4. `test_project_wide_import_direction_matches_v2_section_14` rejects
     any import not present in that module's allowed set.
  5. `vocab`/`ids`/`graph` are threaded through the allow-list explicitly
     as shared dependencies, not as a blanket exemption.
  6. Failure messages name the importing module, the forbidden imported
     module, and the violated rule (e.g. `"models.py imports
     'validation', which is not in its allowed set. Violated rule:
     'models' is only permitted to import ['vocab']..."`) — confirmed by
     a **self-test**: `models.py` was temporarily mutated in a scratch
     edit to `from .validation import Finding`, the test was re-run and
     failed with exactly that message shape, then the file was reverted
     before continuing (see row 1.28-check for the full record).
  7. Ran `tests/test_architecture.py` alone first — 4/4 passed against
     the real, unmodified tree.
  8. Ran the complete suite — **246/246 passing** (242 prior + 4 new).
  9. Updated row 1.28 (PARTIAL/UNVERIFIED → CONFORMANT) and this
     Changelog, only after steps 7–8 both passed.

  **No production code was changed** — the AST audit found zero actual
  §14 violations in the existing import graph; the layering already
  documented and manually verified in the original audit was already
  fully compliant, and is now protected by an executable test rather than
  a one-time manual check. Two extra tests beyond the minimum ask were
  included as belt-and-suspenders: `test_no_module_imports_cli` (the
  single most severe possible inversion, checked independently of the
  per-module allow-list) and
  `test_no_circular_imports_among_local_modules` (a DAG check built from
  source text alone, deliberately *not* derived from `ALLOWED_IMPORTS`, so
  a mistake in that table cannot simultaneously hide a real cycle); plus
  `test_allowed_imports_table_covers_every_module`, which guards the
  allow-list itself from silently going stale as new modules are added.

  During this update, re-parsing the matrix's own tables also surfaced
  and corrected a transcription error in the previous turn's summary
  tally (see the Self-correction note above) — the tally now shown is
  freshly machine-recounted, not carried forward from prose.

- **Phase 5A / items 3–8 (R5, R6, R11, R12, R20, R22) — ALL DONE. Phase
  5A is now complete.** Before writing any tests, the R6/R12/R20/R22
  IDs in the user's proposed batch description didn't match this
  document's own R-numbering (their "provenance shape" was R12 not R6,
  and "resume-by-another-agent"/"concurrent decomposition"/"no-silent-
  overwrite" weren't R-numbered at all in this matrix) — reconciled with
  the user via `ask_user` before proceeding, per instruction to use this
  matrix's actual R5/R6/R11/R12/R20/R22 mapping rather than guess.

  - **R5** (row 1.15, §6.2 identity-fallback): added
    `test_unknown_identity_no_reason_is_a_warning` +
    `test_unknown_identity_with_reason_recorded_is_not_flagged` to
    `tests/test_validation.py`. No implementation change — the code was
    already correct. Row 1.15: UNVERIFIED -> CONFORMANT.

  - **R6** (row 1.19, §9.1 failure-branch transitions): added 56
    parametrized cases to `tests/test_validation.py` —
    `test_every_documented_failure_branch_transition_is_individually_legal`
    (7 cases, one per documented branch, not just the one previously
    sampled) and `test_failure_branch_from_wrong_source_state_is_illegal`
    (49 cases: every wrong-source/failure-state combination outside the
    one legal pairing per branch). No implementation change. Row 1.19:
    UNVERIFIED -> CONFORMANT.

  - **R11** (row 2.4, §15.1 supersession): added
    `test_superseded_decision_without_forward_link_is_a_warning`,
    `test_superseded_decision_with_forward_link_is_clean_on_that_axis`,
    `test_non_superseded_decision_is_never_flagged_for_missing_forward_link`.
    No implementation change. Row 2.4: UNVERIFIED -> **PARTIAL, not
    CONFORMANT** — R11 was scoped (by explicit design, confirmed in the
    original matrix) to only the narrower `DecisionRecord.status ==
    SUPERSEDED` mechanism; row 2.4's separately-flagged general-case gap
    (§15.1 for Work Items/Knowledge Units transitioning to `HISTORICAL`)
    remains a real, open, unnumbered gap that this recommendation never
    claimed to close.

  - **R12** (row 2.5, §16 Provenance Contract) — **scope changed after a
    dedicated investigation phase, run before any code or matrix change,
    per the user's explicit "look closer first, don't decide yet"
    direction.** Investigated, in order: (1) §16's exact wording --
    confirmed `classification` is a flat, required key in the provenance
    mapping itself, with no textual license to represent it via an
    existing field; (2) KnowledgeUnit/WorkItem's actual schema --
    confirmed `evidence_class` is a distinct, always-populated top-level
    field, a different concept from a provenance-*block*-level
    classification (relevant to artifacts with no `evidence_class` at
    all, e.g. a graph node/edge's provenance string), with no existing
    alias/equivalence convention anywhere in the codebase; (3) every
    provenance construction/consumption path -- confirmed `confidence`
    (classification's pack-adjacent sibling field) was ALSO never
    auto-populated anywhere, establishing the working precedent that
    `None`-until-caller-supplied is how this dict already treats a
    required-but-caller-supplied field. Conclusion: a real §16 gap, not a
    representation-equivalence question -- confirmed with the user via
    `ask_user` before implementing. Added `classification` to
    `_default_provenance()` in `models.py` (default `None`, justified by
    the investigation above, not merely convenient; purely additive;
    confirmed backward-compatible since `export.py`/`html.py` never
    reference `provenance` at all). Added 4 tests, 2 shape + 2 semantic
    (per explicit instruction not to let a 13-key shape test merely
    encode a superficial pass):
    `test_default_provenance_matches_pack_section_16_field_list_exactly`,
    `test_provenance_is_attached_by_default_to_every_provenance_bearing_record`,
    `test_provenance_classification_defaults_to_none_like_its_pack_neighbor_confidence`
    (pins down *why* `None` is correct, not just that it's present), and
    `test_provenance_classification_can_hold_a_real_evidence_class_value`
    (confirms the field can actually carry a real §5 `EVIDENCE-CLASS`
    value, distinct from the record's own `evidence_class`, not just an
    inert always-`None` placeholder). Row 2.5: UNVERIFIED -> CONFORMANT.
    The full `claim / correction / resolution` record is written out
    verbatim at row 2.5 itself, per the user's requested format, rather
    than only summarized here.

  - **R20** (row 4.9, §35.3 `INAPPLICABLE` alias) — **turned out to be
    moot.** Before writing a new test, a check of `tests/test_vocab.py`
    found `test_v1_inapplicable_alias_matches_v2_not_applicable` already
    exists and predates this audit. The original row 4.9 "no test found"
    claim was itself a false-negative (an incomplete grep, not a real
    gap). No test was added; row 4.9 corrected to CONFORMANT without
    introducing a redundant duplicate test.

  - **R22** (Part 7, `ClaimStatus`/`DecisionStatus` docstring labeling):
    rewrote both docstrings in `vocab.py` to explicitly state they are
    implementation-only vocabularies not present in Appendix A (matching
    the disclosure style already used for `ResolutionStatus`/
    `OverallStatus`). Added
    `test_claim_status_and_decision_status_disclose_non_pack_provenance`
    to `tests/test_vocab.py`, asserting the disclosure text is actually
    present (so it can't silently regress). Part 7's two PARTIAL rows:
    PARTIAL -> CONFORMANT.

  **Net effect of this batch:** 66 new test cases (2 + 56 + 3 + 4 + 0 + 1),
  one small additive implementation change (the `classification`
  provenance field, added only after a dedicated investigation phase
  confirmed it was a real gap and that `None` was the semantically
  correct default — not assumed), one docstring-only implementation
  change (R22), one corrected pre-existing false-negative claim (R20),
  and one scope clarification obtained from the user before implementing
  (R12). Full suite: **312/312 passing** (246 prior + 66 new). Phase 5A
  (R13, R9, R5, R6, R11, R12, R20, R22 — 8 items total) is now fully
  complete.

- **Phase 5B / item 1 (R3, row 1.11) — DONE.** Investigation: re-read
  §5.1's Confidence table verbatim alongside its explicit constraint
  sentence. Confirmed the table lists a floor for every one of its seven
  named classes (`VERIFIED`/`EXECUTED` → `HIGH`-implying but the
  constraint sentence only forbids `LOW`/`NONE`; `TESTED`/`IMPLEMENTED`/
  `OBSERVED` → `MEDIUM`; `DERIVED`/`ARCHITECTURAL-PROPOSAL` → `LOW`), and
  that `MIN_CONFIDENCE_FOR_CLASS` genuinely had no entry at all for
  `DERIVED`/`ARCHITECTURAL-PROPOSAL` — a real gap, not an
  alternate-representation question (there is no other place in the
  schema that enforces a floor for these two classes). Fix: added
  `EvidenceClass.DERIVED: Confidence.LOW` and
  `EvidenceClass.ARCHITECTURAL_PROPOSAL: Confidence.LOW` to
  `MIN_CONFIDENCE_FOR_CLASS` in `vocab.py`, with an inline comment
  disclosing — but deliberately not resolving — the adjacent, narrower
  ambiguity around `VERIFIED`/`EXECUTED`'s floor (table implies `HIGH`,
  constraint sentence only forbids `LOW`/`NONE`, permitting `MEDIUM`);
  per the governing rule, a fix scoped to one gap must not silently
  expand into resolving a second, separate textual tension. No change
  needed in `validation.py` — the existing generic
  `CONFIDENCE_TOO_LOW_FOR_CLASS` check already reads from this dict, so
  extending the dict alone was sufficient (smallest possible additive
  change, per standing practice). Added 6 tests to `tests/test_validation.py`:
  `test_derived_or_architectural_proposal_with_none_confidence_is_an_error`
  (parametrized, both classes, negative path), `test_derived_or_architectural_proposal_with_low_confidence_is_clean`
  (parametrized, both classes, proves the floor itself is not
  over-strict), `test_unknown_or_example_with_none_confidence_is_never_flagged`
  (parametrized, proves the deliberate *absence* of a floor for these two
  classes remains correct — a floor here would itself be a semantic
  overreach). Row 1.11: PARTIAL → CONFORMANT, with the disclosed
  `VERIFIED`/`EXECUTED` ambiguity noted explicitly in the row rather than
  silently dropped. Full suite: **318/318 passing** (312 prior + 6 new).

- **Phase 5B / item 2 (R15, row 3.2) — DONE.** Investigation: read §26.1's
  exact 13 numbered Stop Conditions verbatim. Confirmed
  `DecisionRecord.overrides_stop_condition` was already range-checked
  1–13 (`INVALID_STOP_CONDITION_NUMBER`) — that half of the row was
  already CONFORMANT — but `FinalReport.stop_conditions_triggered`
  (a free-form `list[dict[str, Any]]`) had its entries iterated for
  BLOCKED-substantiation purposes without any check that an entry's
  `"condition"` value was actually one of the 13 defined numbers. This
  matched row 3.2's original PARTIAL claim exactly — a real, confirmed
  gap, not an alternate representation elsewhere in the schema. Fix:
  added `vocab.STOP_CONDITIONS: dict[int, str]`, a closed 13-entry
  lookup table (pack-literal description text keyed by condition
  number), mirroring `MIN_CONFIDENCE_FOR_CLASS`'s existing dict style
  rather than introducing a new `_StrEnum` (the 13 conditions are
  pack-numbered, not pack-named, so a plain dict keeps the same shape as
  the field it validates). Added one new check in `validate_final_report`
  (`validation.py` only, per the standing architectural constraint) that
  each `stop_conditions_triggered` entry's `"condition"` key is a member
  of `STOP_CONDITIONS`, reusing the existing `INVALID_STOP_CONDITION_NUMBER`
  finding code since both call sites enforce the same normative
  requirement. No change to `models.py` — `stop_conditions_triggered`'s
  shape (free-form list of dicts) was not itself the gap, only its
  unvalidated values were, so the field was left exactly as-is (smallest
  possible additive change). Added 4 tests to `tests/test_validation.py`:
  `test_stop_conditions_triggered_with_a_real_condition_number_is_not_flagged`
  (parametrized 1 and 13, boundary check), `test_stop_conditions_triggered_with_an_invalid_condition_number_is_rejected`
  (parametrized 0, 14, 99, the string `"3"`, and `None` — negative path
  per the governing rule, covering out-of-range, off-by-one, wrong-type,
  and missing-value cases together), and
  `test_stop_conditions_triggered_invalid_number_is_flagged_even_when_not_blocked`
  (proves the new check runs regardless of `overall_status`, since a
  triggered-then-overridden condition can appear on a report that is not
  itself BLOCKED). Row 3.2: PARTIAL → CONFORMANT. Full suite:
  **326/326 passing** (318 prior + 8 new; includes the pre-existing
  `test_invalid_stop_condition_number_rejected` and the two pre-existing
  BLOCKED-substantiation tests referenced above, all still passing
  unmodified).

  **Net effect of Phase 5B so far (R3 + R15):** 14 new test cases (6 for
  R3 + 8 for R15), two small additive `vocab.py` changes (a dict
  extension and a new closed lookup table), one small additive
  `validation.py` change (one new check reusing an existing finding
  code), zero changes to `models.py`/`cli.py`/`export.py`/`html.py`.
  Full suite: **326/326 passing** (312 at the Phase 5A checkpoint + 6
  (R3) + 8 (R15) = 326).

- **Phase 5B / item 3 (R19, row 4.4) — DONE.** Investigation performed
  before any code change, per the explicit discipline requested for this
  item: (1) extracted §31's exact literal text (the Work Planner prompt,
  line ~1373): "Separate: PLAN, AUTHORIZATION, EXECUTION, OBSERVATION,
  VERIFICATION" — 5 values, uppercase in the pack; (2) checked all 17
  Appendix A vocabularies (A.1–A.17) and confirmed none of them define
  this set — it is Sec 25–34 *prompt* prose (§0.4 explicitly classifies
  §§25–34 as prompts for sub-agents, not the normative core), the same
  disclosure category as `ClaimStatus`/`DecisionStatus` (R22); (3)
  inventoried every live use of `LifecycleLogEntry.stage`/`WorkItem.log()`
  across `models.py`, `validation.py`, `cli.py` (5 call sites), and
  `tests/test_storage.py`/`tests/test_validation.py`: all of them already
  use exactly the same 5 lowercase values (`plan`, `authorization`,
  `execution`, `observation`, `verification`), with zero variants or
  typos present anywhere live; (4) confirmed the existing values already
  correspond 1:1 to the pack's 5 named stages (modulo case), so introducing
  the enum required no semantic change, only a closure of the existing set;
  (5) no implementation-only value was found that needed separate
  classification before changing anything. Casing decision: kept the
  pre-existing lowercase spelling rather than renaming to the pack
  prompt's uppercase, because (unlike `VerificationGate`, which matches
  Appendix A.9's Title-case exactly since that vocabulary is genuinely
  pack-defined) this vocabulary has no Appendix-A-mandated spelling to
  conform to — renaming would have been an unforced, non-additive change
  to every existing call site and on-disk record, which the governing
  rule ("do not redesign semantics merely to increase the conformance
  score") counsels against. This scope decision is recorded in
  `vocab.WorkItemStage`'s own docstring, not just here.

  Fix: added `vocab.WorkItemStage` (closed 5-value `_StrEnum`).
  `LifecycleLogEntry.stage`'s type annotation changed from `str` to
  `WorkItemStage` (field itself, its values, and its on-disk spelling all
  unchanged — purely a type-annotation tightening, not a rename). Updated
  `cli.py`'s 5 `item.log(...)` call sites to pass `WorkItemStage` members
  instead of bare literal strings (`work create` → `WorkItemStage.PLAN`,
  `work claim`/`work authorize` → `WorkItemStage.AUTHORIZATION`,
  `work set-state`'s `stage_map` → `WorkItemStage.EXECUTION`/
  `.OBSERVATION`/`.VERIFICATION`). Added one new check to
  `validate_work_item` (`validation.py` only, per the standing
  architectural constraint): every `lifecycle_log` entry's `stage` must
  construct successfully as a `WorkItemStage`, else
  `INVALID_LIFECYCLE_LOG_STAGE` fires — mirrors the pre-existing
  `validate_wiki_page_local` pattern of defensively re-checking
  `page.page_number` against `WikiPageNumber` even though `WikiPage`'s
  own `__post_init__` already coerces it, since a hand-constructed or
  JSON-round-tripped `LifecycleLogEntry` might not have gone through
  `WorkItem.log()` at all. Deliberately left `storage.py`'s JSON-loading
  path for `lifecycle_log` untouched (out of R19's stated scope, and
  unnecessary regardless: `WorkItemStage` values are plain strings, so
  the new `validation.py` check catches an invalid stage the same way
  whether it arrived as a raw string or an enum member).

  Added 13 tests to `tests/test_validation.py`:
  `test_lifecycle_log_entry_with_a_real_stage_is_not_flagged`
  (parametrized, all 5 values — boundary-complete, not just one sample
  value), `test_lifecycle_log_entry_with_an_invalid_stage_is_rejected`
  (parametrized: typo `"excecution"`, wrong-case `"Execution"`/
  `"EXECUTION"` — proving the closed set is case-sensitive, an unrelated
  word `"cleanup"`, empty string, digit string `"6"`, and `None`),
  `test_lifecycle_log_entry_stage_accepts_the_enum_member_directly`
  (semantic: confirms a `WorkItemStage` member itself, not just its
  string value, round-trips and validates cleanly — per the standing
  practice that shape/field tests must be semantic, not just
  presence/shape checks). The 2 pre-existing tests that already exercised
  this field (`test_verified_without_lifecycle_log_is_an_error`,
  `test_fully_valid_verified_work_item_has_no_errors`) were run
  unmodified and both still pass, confirming no regression to the
  existing literal-string membership check (`required_stage not in
  stages_logged`), since `WorkItemStage` is a `str` subclass and compares
  equal to its plain value. A manual CLI smoke test (`work create` →
  `work claim` → `work show --json` → `work validate`) additionally
  confirmed the full round trip serializes/deserializes/validates
  cleanly end-to-end with no `INVALID_LIFECYCLE_LOG_STAGE` false
  positive. Row 4.4: PARTIAL → CONFORMANT. Full suite: **339/339 passing**
  (326 prior + 13 new).

  **Net effect of Phase 5B so far (R3 + R15 + R19):** 27 new test cases
  (6 + 8 + 13), three small additive `vocab.py` changes (one dict
  extension, two new closed enums/lookup tables), two small additive
  `validation.py` changes (two new checks, one reusing an existing
  finding code), one type-annotation-only change in `models.py`
  (`LifecycleLogEntry.stage: str` → `WorkItemStage`, no value/shape
  change), five call-site updates in `cli.py` (literal strings →
  enum members, no behavior change), zero changes to `export.py`/
  `html.py`/`storage.py`. Full suite: **339/339 passing** (312 at the
  Phase 5A checkpoint + 6 (R3) + 8 (R15) + 13 (R19) = 339).

- **Phase 5B / item 4 (R21, row 4.11) — DONE.** Investigation: read §36's
  exact literal text (the Change-Impact Analysis prompt, its last line):
  "If the changed unit has open claims from other agents (§24.1), flag
  the conflict before proceeding." Cross-referenced §24.1 ("Ownership /
  Claiming"), the only section defining what an "open claim" is: it
  explicitly *permits* proposing a Change-Impact Analysis against an
  already-claimed item ("It MAY observe, verify, or propose a
  Change-Impact Analysis against it") — so §36's rule is specifically
  about *flagging*, not *blocking*, making a WARNING-severity finding the
  correct choice, not an ERROR. Checked `ChangeImpactAnalysis` (bare
  `target_unit_id: str`, no ownership-shaped field) and confirmed
  `Ownership`/`ClaimStatus` exist only on `WorkItem` — `KnowledgeUnit` has
  no ownership field anywhere in this schema. This is a real, structural
  scope limit (same shape as R11's `DecisionRecord`-only narrowing): the
  check can only ever fire when `target_unit_id` resolves to a
  `WorkItem`, since there is no ownership concept to check on a
  `KnowledgeUnit` target at all — disclosed explicitly in the fix and in
  row 4.11, not silently treated as full §36 coverage.

  Fix: `validate_change_impact_analysis` gained an optional
  `work_items: dict[str, WorkItem] | None` parameter, mirroring
  `validate_wiki_references`'s existing optional-mapping cross-record
  pattern exactly (checks only run when a mapping is supplied; an
  unresolved target is skipped, not treated as clean) — this function
  still never touches storage itself. New check:
  `CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM` (WARNING) fires when the target
  resolves to a `WorkItem` with `ownership.status == ACTIVE` and a
  different `ownership.owner` than `analysis.proposed_by`. Wired into
  real usage: added `cli.py::_impact_target_work_item_map` (a small,
  additive helper mirroring `_wiki_referenced_records`'s "load if
  present, tolerate `RecordNotFound`/`RecordCorrupted`" pattern) and
  passed its result into `impact set`/`impact approve`/`impact show`/
  `impact validate`, so the check isn't a dormant library function nobody
  calls. No changes to `models.py`, `export.py`, or `html.py` — `export.py`
  deliberately left as-is (Phase 3 is permanently frozen and R21's scope
  was `validation.py`, with `cli.py` wiring as a natural, minimal
  extension of it, not a new export-pipeline behavior).

  Added 5 tests to `tests/test_validation.py`:
  `test_change_impact_target_with_active_claim_by_another_agent_is_flagged`
  (positive), `test_change_impact_target_claimed_by_the_same_proposer_is_not_a_conflict`
  (same agent continuing its own work is correctly not a conflict),
  `test_change_impact_target_with_released_claim_is_not_a_conflict`
  (proves the check reads `ownership.status`, not merely whether an
  owner string is present — only `ACTIVE` counts as "open"),
  `test_change_impact_conflict_check_is_skipped_without_a_work_items_mapping`
  and `test_change_impact_conflict_check_is_skipped_when_target_is_not_in_the_mapping`
  (both negative: omitting the mapping, or supplying one that doesn't
  resolve the target, must not silently assert "no conflict" as if it had
  been checked). A manual CLI smoke test (`work create` → `work claim` →
  `impact create` with a different `--proposed-by` → `impact validate`)
  additionally confirmed `CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM` fires
  correctly end-to-end through real storage. Row 4.11: NON-CONFORMANT →
  CONFORMANT. Full suite: **344/344 passing** (339 prior + 5 new).

  **Net effect of Phase 5B so far (R3 + R15 + R19 + R21):** 32 new test
  cases (6 + 8 + 13 + 5), three small additive `vocab.py` changes, three
  small additive `validation.py` changes (three new checks / parameters),
  one type-annotation-only change in `models.py`, and additive-only
  `cli.py` changes (enum-member call sites for R19; one new helper
  function plus 4 call sites gaining an optional keyword argument for
  R21) — zero changes to `export.py`/`html.py`/`storage.py` across all
  of Phase 5B so far. Full suite: **344/344 passing** (312 at the Phase
  5A checkpoint + 6 (R3) + 8 (R15) + 13 (R19) + 5 (R21) = 344). Phase 5B
  locked order remaining: R17 (last, by design — override semantics are
  the most coupled to the cross-record machinery just hardened above).

- **Phase 5B, Recommendation R17 (row 3.5, v2 §26.2 — last item in the
  locked order, closing Phase 5B):** Investigated with a stop-first
  discipline given R17's stated higher coupling. Read §26.1/§26.2
  verbatim; confirmed the 13 Stop Conditions are already a closed,
  structurally identifiable set (`DecisionRecord.overrides_stop_condition`,
  range-checked 1-13) and that the 4 mandatory override-metadata elements
  are already enforced (row 3.3, CONFORMANT). Confirmed the
  status-strengthening bypass (override does not retroactively change a
  classification) is real but is row 3.4 / Recommendation R16's gap, not
  R17's — correctly left untouched, preserving the class boundary.
  Constructed the exact negative case for row 3.5 directly in code before
  writing any implementation: a fully valid, fully-attributed
  `DecisionRecord` overriding Stop Condition #2 (zero findings on its own,
  as it should be — a legitimate authorized override) paired with a
  `FinalReport` whose `stop_conditions_triggered` never mentions Stop
  Condition #2 at all — confirmed this produces zero findings today,
  exactly the "override made the trigger invisible" outcome v2 §26.2
  explicitly forbids.

  **Stopped and reconciled an object-model ambiguity before implementing**
  (per the R3/R12 precedent): to check "does this report account for every
  override that happened," `validate_final_report` needs to know which
  `DecisionRecord`(s) a report relates to. Neither existing field covers
  this — `open_decision_ids` means "still OPEN, caps overall_status ceiling"
  (a *resolved* override decision never belongs there), and
  `blocking_decision_id` is singular and only meaningful when
  `overall_status == BLOCKED` (the pack's own worked example is an override
  that lets the operation proceed to COMPLETE, not stay BLOCKED). Presented
  three options to the user (add a new field mirroring the existing
  `related_audit_ids`/`related_work_item_ids` pattern; a validation-only
  parameter with nothing persisted; or narrowing the check's scope to
  `blocking_decision_id` only with the narrower coverage disclosed). User
  selected the new-field option, with explicit reasoning: the persisted
  report must be able to *prove* which decisions it accounted for, not
  just have been checked correctly at creation time.

  Added `FinalReport.related_decision_ids: list[str]` (`models.py`,
  additive only, mirrors the existing `related_audit_ids`/
  `related_work_item_ids` shape exactly). `validate_change_impact_analysis`
  is unaffected.

  **First-draft correction, caught and directed by the user before this
  entry was finalized:** the initial implementation accepted `decisions`
  as a bare `Iterable[DecisionRecord]` and used `Severity.WARNING` for the
  visibility check. The user's review identified two concrete defects
  with this shape: (1) a bare iterable cannot distinguish "the caller
  didn't supply decisions" from "the caller supplied decisions but this
  particular related ID doesn't resolve" — a dangling
  `related_decision_ids` entry passed through completely unflagged; and
  (2) §26.2 states the visibility requirement with "MUST", which this
  codebase's own convention (`WIKI_REFERENCE_NOT_FOUND` for a dangling
  WikiPage reference) already treats as ERROR, not WARNING. Both were
  corrected before this row was marked CONFORMANT:

  `validate_final_report` (`validation.py`) now takes an optional
  `decisions: Optional[dict[str, DecisionRecord]] = None` parameter — a
  `{id: DecisionRecord}` mapping, mirroring `validate_wiki_references`'s
  dict-mapping shape exactly. When supplied, it runs two unconditional
  checks (not gated on `overall_status == BLOCKED`, matching
  `INVALID_STOP_CONDITION_NUMBER`'s existing reasoning) for every ID in
  `report.related_decision_ids`: first, the ID must resolve in the
  mapping, else `RELATED_DECISION_NOT_FOUND` (Severity.ERROR); second, for
  every resolved decision whose `overrides_stop_condition` is set, that
  condition number must appear in `report.stop_conditions_triggered`,
  else `OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT` (Severity.ERROR). Both
  checks skip entirely (no manufactured pass/fail) when `decisions` is
  omitted, the same "skip if unresolved" semantics as R21's `work_items`
  parameter and the pre-existing `blocking_decision` parameter.

  `cli.py` gained `--related-decision` on `report create` and a new
  `_related_decisions(ws, r) -> dict[str, DecisionRecord]` helper (mirrors
  `_load_blocking_decision`'s/`_impact_target_work_item_map`'s
  tolerate-`RecordNotFound`/`RecordCorrupted` pattern, but returns a dict
  keyed by ID rather than a list — a dangling or corrupted ID is simply
  omitted from the returned mapping, which is exactly what lets
  `validate_final_report` detect and flag it as `RELATED_DECISION_NOT_FOUND`
  rather than silently dropping it), wired into `report finalize`/
  `report show`/`report validate` so both checks actually run against real
  storage, not just a dormant library function. `reporting.py` gained one
  new display line ("Related Decision ID(s)") in `render_final_report`,
  alongside the existing `related_audit_ids`/`related_work_item_ids`
  lines — presentation only, no new logic, consistent with the five-role
  architectural invariant. `export.py`'s existing single-argument
  `validate_final_report(report, blocking_decision=blocking_decision)`
  call was deliberately left unchanged, the same as R21's precedent with
  `validate_change_impact_analysis` — Phase 3/the export pipeline is
  permanently frozen and out of scope.

  Added 8 tests to `tests/test_validation.py`, covering the user's full
  negative-path checklist:
  `test_final_report_omitting_a_related_overridden_stop_condition_is_flagged`
  (positive — the exact gap case constructed during investigation,
  asserts ERROR severity), `test_final_report_that_lists_the_overridden_condition_is_not_flagged`
  (boundary-negative: correctly-reported override is clean),
  `test_final_report_override_check_is_skipped_without_a_decisions_mapping`
  (omitting the mapping must not silently assert "no violation" for
  either check, as if it had been checked),
  `test_final_report_decision_without_an_override_is_not_flagged` (a
  related decision with no override never fires the override-visibility
  check), `test_final_report_flags_each_missing_override_independently`
  (two related override decisions, only one reflected — the omitted one
  is still flagged, by name, even though the report isn't wholly silent
  about overrides), `test_final_report_with_dangling_related_decision_id_is_flagged`
  (a `related_decision_ids` entry absent from the supplied mapping is now
  detected — the exact defect the user's review caught in the first
  draft), `test_final_report_unrelated_decision_alongside_a_reflected_override_is_clean`
  (an unrelated, non-overriding related decision introduces no finding of
  its own alongside a correctly-reflected override),
  `test_final_report_unrelated_status_strengthening_alongside_override_remains_valid`
  (an overridden condition coexisting with an otherwise-valid, unrelated
  completion claim is not suppressed or masked by the override machinery).
  Added 3 tests to `tests/test_cli.py`:
  `test_report_validate_flags_a_related_override_missing_from_stop_conditions`
  (full CLI round-trip: `decision create` → `decision resolve` →
  `report create --related-decision` → `report validate`),
  `test_report_validate_flags_a_dangling_related_decision_id` (CLI
  round-trip for the dangling-ID case), and
  `test_report_show_records_related_decision_ids` (field round-trip).
  Manual CLI smoke tests additionally confirmed both ERROR cases fire with
  exit code 1 and the positive path clears with exit code 0, through real
  storage end-to-end. Row 3.5: NON-CONFORMANT → CONFORMANT. Full suite:
  **355/355 passing** (344 prior + 8 validation tests + 3 CLI tests = 355;
  the corrected draft's 11 tests supersede the first draft's 7, since the
  first draft's WARNING-severity/list-API tests were rewritten rather than
  kept alongside the corrected ones).

  **Net effect of Phase 5B (R3 + R15 + R19 + R21 + R17, now complete):**
  43 new test cases total (6 + 8 + 13 + 5 + 11), five small additive
  `vocab.py`/`models.py` data-shape changes (three `vocab.py`, one
  type-annotation-only in `models.py` for R19, plus one new field for R17
  — `FinalReport.related_decision_ids`), five small additive
  `validation.py` changes (R3/R15/R19/R21 each added one new check or
  parameter; R17 added one new optional `dict`-shaped parameter plus two
  new checks — `RELATED_DECISION_NOT_FOUND` and
  `OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT`, both ERROR severity), and
  additive-only `cli.py` changes across all five recommendations
  (enum-member call sites for R19; one new helper function plus 4 call
  sites gaining an optional keyword argument for R21; one new CLI option
  plus one new dict-returning helper function plus 3 call sites gaining an
  optional keyword argument for R17) — one presentation-only addition to
  `reporting.py` (R17), zero changes to `export.py`/`html.py`/`storage.py`
  across all of Phase 5B. Full suite: **355/355 passing** (312 at the
  Phase 5A checkpoint + 6 (R3) + 8 (R15) + 13 (R19) + 5 (R21) + 11 (R17)
  = 355). **Phase 5B is now complete** — all five locked-order
  recommendations (R3, R15, R19, R21, R17) are DONE. Per the roadmap, the
  next step is a full Phase 5B re-audit before Phase 6 begins.

- **Phase 5B re-audit — FROZEN.** Per explicit, binding user instruction,
  this was a *fresh* independent re-verification, not a carry-forward of
  the CONFORMANT classifications above: each of R3/R15/R19/R21/R17 was
  re-checked directly against live source (`vocab.py`/`models.py`/
  `validation.py`/`cli.py`), cross-referenced against the pack's literal
  text (not memory), and probed with fresh, isolated positive/negative
  cases plus live end-to-end CLI/storage round-trips (not just re-running
  existing unit tests). Findings: **R3** — `MIN_CONFIDENCE_FOR_CLASS`
  floors unchanged, `CONFIDENCE_TOO_LOW_FOR_CLASS` unconditional and
  correctly cited, 9 fresh probes all matched expectation. **R15** — all
  13 Stop Conditions confirmed word-for-word against §26.1's literal
  text, range check fires unconditionally on both `FinalReport` and
  `DecisionRecord`. **R19** — `WorkItemStage`'s 5 values confirmed
  word-for-word against §31, persisted lowercase representation confirmed
  unchanged via a live CLI round-trip reading the actual on-disk JSON, all
  5 `cli.py` call sites use enum members. **R21** — `work_items`-mapping
  behavior confirmed correct for all 5 cases (active-claim-by-other-agent
  flagged; same-proposer, `RELEASED` status, missing mapping, and
  unresolved target all correctly skip), confirmed end-to-end through a
  live `impact create` → `impact validate` CLI round-trip. **R17** — all 9
  sub-points of the corrected contract re-verified from live source and
  live CLI round-trips (field exists; dict-typed `decisions` param;
  dangling ID and omitted override both ERROR; unrelated status
  strengthening doesn't cross-contaminate; valid override coexists with
  COMPLETE; triggered condition stays visible in
  `stop_conditions_triggered`; all 4 CLI commands wired; `export.py`
  confirmed still single-argument/untouched). **One real drift was found
  and fixed by this re-audit**: row 3.5's evidence cell still read "9
  tests in `test_validation.py`" against a list that already named only 8
  — corrected to "8 tests" (the true, `grep -c`-verified count). This is
  exactly the kind of transcription drift an independent re-audit exists
  to catch; it was a prose-only staleness, not an implementation or
  behavioral regression — **zero of the five recommendations were
  downgraded**. Full repository-wide recount after the fix: **43
  CONFORMANT / 13 PARTIAL / 7 NON-CONFORMANT / 1 UNVERIFIED / 8
  NOT-APPLICABLE = 72 rows, 0 unparsed** (unchanged by the fix, since it
  was prose-only). Full suite: **355/355 passing**, 0 production
  regressions. **Phase 5B is now FROZEN.**

- **Phase 5C / item 1 (R8, row 1.27) — DONE.** Per user direction, R8 —
  along with R2/R4/R18 — was pulled out of its previously-unsequenced
  holding spot in the Class 2 table and given its own short phase
  (Phase 5C), run immediately after Phase 5B's freeze, in the locked order
  R8 → R4 → R18 → R2. Investigation: re-read §13's literal pipeline text
  and its `HostInvoked(E) ⇒ DurableIssued(E)` invariant directly from the
  pack; confirmed via `grep` that no module anywhere in `arena_agent/`
  mentions §13 or an External Effect Contract at all — the scope decision
  documented in this matrix's Baseline record existed *only* in this
  audit artifact, exactly as row 1.27's prior text said. Per R8's own
  definition ("documentation, not necessarily implementation") and the
  governing "do not manufacture scope merely to increase the conformance
  score" rule, no `Effect` object, pipeline, or durability-boundary check
  was added — this package never invokes an external effect, so there is
  nothing for such a check to guard. **Resolution**: added a "Scope: no
  External Effect Contract (v2 §13)" section to `arena_agent`'s package
  docstring explaining why (record-keeping/validation/reporting tool, not
  an execution engine) and what a caller embedding this package inside a
  real effect-invoking system would still need to do itself; added a
  pointer from `WorkItem`'s docstring (the record type closest to §13's
  authority concept via `required_authority`/`forbidden_authority`) to
  that disclosure; added the same disclosure to `README.md`'s "Design
  choices worth knowing about" section for a reader who never opens the
  source. Two new tests in `tests/test_scope_disclosures.py`
  (`test_package_docstring_discloses_no_external_effect_contract`,
  `test_work_item_docstring_points_to_the_external_effect_scope_disclosure`)
  assert the disclosure text is actually present, mirroring R22's
  docstring-disclosure test pattern exactly; sensitivity-checked by
  confirming both assertions fail against a scratch copy of the docstring
  with the disclosure phrase removed. Row 1.27 moved from NON-CONFORMANT
  to NOT-APPLICABLE-by-disclosed-scope. Full suite: **357/357 passing**
  (355 prior + 2 new). Fresh repository-wide recount: **43 CONFORMANT / 13
  PARTIAL / 6 NON-CONFORMANT / 1 UNVERIFIED / 9 NOT-APPLICABLE = 72 rows,
  0 unparsed** (NON-CONFORMANT 7→6, NOT-APPLICABLE 8→9, net row count
  unchanged).

- **Phase 5C / item 2 (R4, row 1.14) — DONE, scope changed.** Investigation:
  re-read §6.1's literal text directly from the pack ("A SAMPLED coverage
  tag MUST NOT be used to justify a PRESENT or ABSENT classification for
  anything not actually inspected"); confirmed `InventoryItem` already has
  all the shape ingredients (`classification`, `coverage`,
  `coverage_method`, `evidence`) and that `validate_repo_audit` already
  enforces `PRESENT_WITHOUT_EVIDENCE` (evidence non-empty) and
  `SAMPLED_WITHOUT_METHOD` (sampling method described) — no object-model
  gap analogous to R17's existed. The premise (\"add an evidence-quality
  check\") turned out to be unimplementable as originally framed: §6.1's
  actual requirement is a real-world fact (was this specific item
  *actually inspected*?) that no validator over persisted strings can
  independently establish — the same "necessary, not sufficient" boundary
  already disclosed at row 1.13 for repository-evidence claims generally.
  Two mechanical proxies were investigated and explicitly rejected before
  implementing anything: (1) flagging duplicate `evidence` strings shared
  across multiple SAMPLED items, and (2) flagging `evidence` that merely
  repeats `coverage_method` verbatim. Both were rejected because they
  would create *false confidence* that §6.1 was verified when only string
  distinctness was checked — two SAMPLED items can legitimately share
  identical, true evidence text (e.g. both genuinely confirmed by the same
  inspection command), and two items can have superficially distinct
  evidence that is equally uninspected. Stopped and reconciled this finding
  with the user before implementing, per the R3/R12/R17 stop-and-reconcile
  precedent; the user confirmed the disclosure-only disposition over both
  proxy-heuristic alternatives. **Resolution**: `InventoryItem`'s
  docstring now carries a full disclosure of this permanent verification
  boundary, naming both rejected proxies and why; `validate_repo_audit`
  gained a code comment pointing to the same disclosure above the two
  existing checks; no new check, field, or heuristic was added. One new
  test, `tests/test_scope_disclosures.py::
  test_inventory_item_docstring_discloses_the_sampling_inspection_limit`,
  asserts the disclosure text is present, mirroring the R8/R22
  disclosure-test pattern; sensitivity-checked by confirming the assertion
  fails against a mutated docstring with the disclosure phrase removed.
  Row 1.14 **remains PARTIAL** — deliberately *not* reclassified to
  NOT-APPLICABLE, since §6.1 is a live, applicable requirement that is
  genuinely partially enforced by the existing checks, unlike R8's §13
  which has no applicable code path in this package at all. Full suite:
  **358/358 passing** (357 prior + 1 new). Tally unchanged (row 1.14 was
  already PARTIAL and remains PARTIAL): **43 CONFORMANT / 13 PARTIAL / 6
  NON-CONFORMANT / 1 UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0 unparsed.**

- **Phase 5C / item 3 (R18, row 3.6) — DONE.** Investigation: re-read §27's
  literal template text directly from the pack, confirming its
  "### Persistence" section has exactly four narrative sub-fields
  (Durable state / Journal / Recovery behavior / Indeterminate states and
  reconciliation path), distinct from the *Verification gate table*'s
  separate "Persistence" row (already modeled via
  `VerificationGate.PERSISTENCE`, already enforced by
  `PASS_WITHOUT_EVIDENCE` -- not part of this gap). Confirmed via `grep`
  that no validation logic anywhere references
  `ExecutionState.INDETERMINATE`/`RECONCILED` at all -- that reconciliation
  behavior is Recommendation R10's future territory (Phase 6), untouched
  here. While re-verifying row 3.6's own original text during this
  investigation, found and corrected a pre-existing authoring
  inconsistency in the matrix itself: the row said "two template sections"
  had no field-level equivalent but named only one ("Persistence"); the
  second is row 1.20's already-tracked, unrelated §9.2 sub-state-mapping
  gap (`WorkItem` has no sub-state field for a refined mapping to attach
  to) -- corrected the cross-reference rather than leaving it unattributed
  or guessing at an unrelated cause. Stopped and reconciled the field
  shape with the user before implementing (plain `str`, not a
  structured/append-only journal) — the user confirmed free-text fields
  matching the existing `required_authority`/`forbidden_authority`/
  `resource_budget` precedent exactly, explicitly rejecting an
  append-only-list shape as adding real behavior (mutation helpers,
  immutability discipline) that would edge toward the "hidden execution
  engine" the user's standing caution for this recommendation warned
  against. **Resolution**: `WorkItem` gained four additive fields --
  `durable_state`, `journal`, `recovery_behavior`,
  `indeterminate_states_reconciliation_path` -- all plain `str`, all
  defaulting to `""`; `reporting.render_work_item` gained a matching
  "### Persistence" section; no CLI wiring was added, matching the
  existing precedent that `required_authority`/`forbidden_authority`/
  `resource_budget` have none either. 6 new tests in
  `tests/test_work_item_persistence_fields.py` (field existence/type/
  default; plain-`str` type via dataclass introspection; round-trip
  through a real `Workspace` JSON save/load, not just in-memory; `to_dict`
  serialization; an explicit negative-path guard proving no new
  `PERSISTENCE`/`JOURNAL`/`RECOVERY` validation finding was introduced;
  an explicit static-source-parsing guard proving `validate_work_item`'s
  own function body contains no reference to `INDETERMINATE`/
  `RECONCILED`, keeping R10's scope demonstrably untouched rather than
  merely asserted untouched) plus 1 new test in `test_reporting.py`
  confirming the section actually renders. All negative-path tests were
  confirmed to fail for the intended reason (missing fields) before the
  implementation was written. Row 3.6 stays CONFORMANT (it already was),
  now with every §27 template section field-mapped -- the row's cross-
  reference to the remaining sub-state-mapping gap now correctly points to
  row 1.20 instead of leaving a dangling "two sections" claim. Full suite:
  **365/365 passing** (358 prior + 7 new). Tally unchanged (row 3.6 was
  already CONFORMANT and remains CONFORMANT): **43 CONFORMANT / 13 PARTIAL
  / 6 NON-CONFORMANT / 1 UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0
  unparsed.**

- **Phase 5C / item 4 (R2, row 1.8) — DONE.** Investigation: §4.1's
  Ingested Content Contract requires that a flagged directive "MUST be
  logged as an anomaly ... and reported in the Final Report," but before
  this change `content_scan.py::scan_text` (real, tested, pure/stateless)
  terminated at `cli.py`'s standalone `scan-content` command -- nothing
  linked a scan result to any `FinalReport`. §4.1's own "(§27)" and
  "(§37)" cross-references were confirmed stale (§27 is the Work Item
  template, with no anomaly concept anywhere in it; §37 is the
  Counterexample Minimizer prompt, not the Final Report, which is
  actually §39/§40) -- treated as pre-existing pack drift, not a new
  ambiguity, by following the same §37→§39/§40 reading convention already
  established in `models.py` at R17. §4.1's own text ("it is evidence
  about the source, not license to act on it") was read as already
  settling the observation-vs-verification question, so a scan flag must
  never be treated as, or allowed to influence, a verification
  conclusion. Two shape precedents existed on `FinalReport`: flat
  `list[str]` (`evidence_gaps`, `known_limitations`) and structured
  `list[dict[str, str]]` (`knowledge_units`, `invariants`, `execution`);
  `known_limitations` was additionally confirmed (via the literal §40
  template skeleton) to already be a precedent for fields added beyond
  the pack's literal template shape. **Stopped and reconciled with the
  user before implementing** (per standing discipline): asked about field
  shape and enforcement approach; the user confirmed a structured
  `list[dict[str, str]]` shape with exactly `kind`/`matched_text`/
  `context` (explicitly excluding `start`/`end` pending a separate future
  decision), but then explicitly overrode the initially-selected
  enforcement answer ("field + validation check") with a detailed
  follow-up rejecting any check that would assert or imply scan
  *coverage* -- reasoning that no existing model establishes which source
  content a `FinalReport` claims to cover, so such a check could only
  assert shape, not real coverage, and would manufacture false
  confidence. **Resolution**: `FinalReport` gained one additive field,
  `content_scan_anomalies: list[dict[str, str]] = field(default_factory=
  list)`, populated only via a new explicit-only CLI option,
  `scan-content --attach-to-report <report-id>` (plain `scan-content`
  never touches any report; the option loads the named report, converts
  each `ContentFlag` to a `kind`/`matched_text`/`context` dict, appends,
  and persists; a nonexistent report ID fails via the pre-existing
  `RecordNotFound` path -- ordinary reference integrity, not a new §4.1
  semantic rule); `validation.py` gained exactly one shape-only check,
  `MALFORMED_CONTENT_SCAN_ANOMALY` (WARNING, fires only when an entry
  lacks `kind`), deliberately not asserting or implying coverage
  completeness, per the user's explicit correction; `reporting.py` gained
  a "## Content Scan Anomalies" section (a table when non-empty, "_none
  flagged_" when empty -- never a manufactured placeholder), captioned
  with §4.1's own "evidence about the source, not license to act on it"
  language, which flows through `html.py`'s existing markdown→HTML
  transform unchanged (no `html.py` edits needed, consistent with the
  five-role invariant). Per binding negative-path discipline, 14 new
  tests in `tests/test_content_scan_final_report.py` were written and
  confirmed to fail for the intended reason (missing field, missing CLI
  option, missing check) before any implementation code was written:
  pre-implementation proof the field didn't exist; field exists and
  defaults to `[]`; zero-flags scans yield `[]` rather than a manufactured
  entry; structured shape is preserved rather than flattened to prose;
  populating anomalies never mutates `failures`/`overall_status` (the
  observation-vs-verification boundary, enforced as a test, not just
  prose); JSON round-trip through real `Workspace` storage; `scan-content`
  alone never mutates any report; `--attach-to-report` appends structured
  flags correctly; attaching to a nonexistent report fails cleanly;
  attaching a clean scan leaves the list empty; a missing-`kind` entry is
  flagged; a well-formed entry is not; an empty list is never flagged; an
  anomaly's mere presence never produces an ERROR-severity finding. Full
  suite: **379/379 passing** (365 prior + 14 new). Row 1.8 moves PARTIAL →
  CONFORMANT: **44 CONFORMANT / 12 PARTIAL / 6 NON-CONFORMANT / 1
  UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0 unparsed** (freshly
  machine-recounted from this file's own tables). **Phase 5C (R8 → R4 →
  R18 → R2) is now entirely DONE**; a full independent re-audit is
  pending before Phase 6 begins, per standing re-audit discipline.

- **Phase 5C re-audit — FROZEN.** Per explicit, binding user instruction,
  this was a *fresh* independent re-verification of R8/R4/R18/R2 directly
  against live source and the pack's own literal text, not a carry-
  forward of the CONFORMANT/PARTIAL classifications above -- mirroring
  the Phase 5B re-audit's method exactly (re-read requirement text,
  re-check implementation location, re-check every claimed behavior,
  re-check test coverage, check for scope leakage into later
  recommendations, check CLI/storage/reporting behavior live, check
  matrix evidence accuracy, recompute the tally from scratch).
  **R8** (§13) — re-read §13's literal pipeline text directly from the
  pack; confirmed via `grep` that no `Effect`/pipeline object,
  `HostInvoked`/`DurableIssued` invariant, or durability-boundary check
  exists anywhere in `arena_agent/*.py`; confirmed the disclosure exists
  in all three claimed locations (package docstring, `WorkItem`
  docstring, `README.md`); both dedicated tests re-run in isolation and
  pass; independently re-derived (not just re-read) that the assertions
  are genuinely sensitive by testing the same logic against a
  disclosure-stripped docstring string and confirming it fails as
  expected; confirmed row 1.27's evidence cell is accurate; confirmed no
  leakage into R18 (`WorkItem`'s later Persistence-field docstring
  addition sits beside, not inside, R8's disclosure paragraph, with its
  own separate attribution). Row 1.27 stands: NOT-APPLICABLE-by-
  disclosed-scope, unchanged. **R4** (§6.1) — re-read §6.1's literal text
  directly from the pack, confirming the exact "MUST NOT be used to
  justify a PRESENT or ABSENT classification for anything not actually
  inspected" wording; re-read `InventoryItem`'s docstring and
  `validate_repo_audit`'s comment in full, confirming both accurately
  restate this boundary and the two rejected mechanical proxies;
  confirmed `PRESENT_WITHOUT_EVIDENCE`/`SAMPLED_WITHOUT_METHOD` still
  exist and fire as documented; re-ran the disclosure test in isolation
  and independently re-confirmed its sensitivity the same way as R8's.
  Row 1.14 stands: PARTIAL, correctly not reclassified to NOT-APPLICABLE
  (a live, applicable requirement that is genuinely partially enforced,
  distinguishing it from R8's true no-code-path case). **R18** (§27) —
  re-read §27's literal "### Persistence" template block directly from
  the pack (`- Durable state:` / `- Journal:` / `- Recovery:` /
  `- Indeterminate states (EXECUTION-STATE, §14/§15):`); confirmed all
  four `WorkItem` fields exist as plain `str`, default to `""`, round-trip
  through real `Workspace` storage, and render under a "### Persistence"
  heading; confirmed via `grep` that `validation.py` contains zero
  references to `INDETERMINATE`/`RECONCILED` anywhere (not just inside
  `validate_work_item`), independently reconfirming R10's territory is
  untouched; all 6 dedicated tests plus the 1 rendering test re-run in
  isolation and pass. **One real drift was found and fixed by this
  re-audit**: row 3.6's evidence cell claimed the four new field names
  matched §27's own Persistence sub-field labels "verbatim" -- false by
  literal comparison: the pack's own labels are "Recovery:" and
  "Indeterminate states (EXECUTION-STATE, §14/§15):", not "Recovery
  behavior:" / "Indeterminate states and reconciliation path:" as
  `recovery_behavior`/`indeterminate_states_reconciliation_path`'s
  rendering labels read. **Original claim**: the four field names/labels
  match §27's own sub-field labels verbatim. **Correction**: false as
  literally stated -- two of the four labels are readable expansions of
  the pack's terser originals, not verbatim quotes; the underlying
  *semantic* mapping (all four §27 Persistence sub-fields now have a
  corresponding `WorkItem` field, correctly ordered, correctly typed) was
  never in question and remains true. **Resolution**: row 3.6's evidence
  cell corrected to quote §27's actual literal labels and disclose the
  two expansions explicitly, rather than silently leaving an inflated
  "verbatim" claim in an audit artifact whose entire purpose is precise
  citation accuracy; no code or test change was needed, since the
  underlying field-mapping claim this prose describes was correct -- this
  was a documentation-only overstatement in the matrix, not a defect in
  the implementation. Row 3.6 stands: CONFORMANT, unchanged. **R2**
  (§4.1) — re-read §4.1's literal text directly from the pack, confirming
  the exact "MUST be logged as an anomaly (§27) and reported in the Final
  Report (§37)" wording and its "evidence about the source, not license
  to act on it" clause; re-read `content_scan.py` in full, confirming
  `scan_text`/`ContentFlag` are unchanged and still pure/stateless;
  confirmed `FinalReport.content_scan_anomalies` exists with the exact
  `kind`/`matched_text`/`context` shape (no `start`/`end`); confirmed
  live and behaviorally (not just by reading the source) that
  `MALFORMED_CONTENT_SCAN_ANOMALY` fires even when `overall_status` is
  `BLOCKED` -- i.e., it sits before, not after, `validate_final_report`'s
  BLOCKED-status early return, since a check placed after that return
  would silently never run for the majority of real BLOCKED reports;
  confirmed via `grep` that `cli.py`'s `--attach-to-report` option is the
  only place `content_scan_anomalies` is ever mutated, and that it
  correctly re-uses the pre-existing `RecordNotFound`→`ArenaCliGroup`
  error-handling path rather than adding a new one; confirmed no
  `ClaimStatus`/`ExecutionState`/`overrides_stop_condition` references
  were introduced anywhere in R2's diff, keeping R14/R10/R16's future
  territory demonstrably untouched; re-ran all 14 dedicated tests in
  isolation and confirmed they pass. Row 1.8 stands: CONFORMANT,
  unchanged. **Overall re-audit result**: one real prose-only drift found
  and corrected (R18's "verbatim" overstatement); **zero of the four
  Phase 5C recommendations were downgraded**; zero implementation or
  behavioral regressions found. Full repository-wide recount after the
  fix: **44 CONFORMANT / 12 PARTIAL / 6 NON-CONFORMANT / 1 UNVERIFIED / 9
  NOT-APPLICABLE = 72 rows, 0 unparsed** (unchanged by the fix, since it
  was prose-only). Full suite: **379/379 passing**, 0 regressions.
  **Phase 5C is now FROZEN.**

- **Phase 6 / item 1 (R14, row 2.16) — investigation and reconciliation
  complete; implementation not yet started.** Read row 2.16 fresh from
  the live matrix (NON-CONFORMANT: `ClaimStatus.EXPIRED` exists in
  `vocab.py` but nothing ever sets it, and no hook exists for a caller to
  supply an expiry policy) and §24.1's exact literal text fresh from the
  pack ("Claims expire per the governing operational policy (not fixed by
  this pack); an expired claim reverts the item to `PLANNED` and MUST
  record the original agent's partial evidence rather than discarding
  it."). Confirmed via `grep` and live calls that `check_claim_expiry`
  does not exist anywhere, `ClaimStatus.EXPIRED`/`RELEASED` are never set
  by any code path (only `ACTIVE`, via `work claim`), and
  `validate_work_item` never references `ownership` in any check --
  matrix's "not even a hook" claim confirmed accurate. **A genuine,
  previously-undisclosed normative tension was found and is recorded at
  row 2.16**: §24.1's mandated `EXECUTING → PLANNED` reversion is already
  an ERROR-severity `LIFECYCLE_BACKWARD_TRANSITION` under
  `validate_lifecycle_transition` (§9.1's own canonical model), confirmed
  live -- the pack itself never reconciles this. **Stopped and reconciled
  with the user before writing any code or tests**, per standing
  discipline. **User's binding resolution**: `check_claim_expiry` must be
  a *pure, mutation-free* detection hook -- it inspects an `ACTIVE`
  claim's age against a caller-supplied policy and returns a `Finding`
  describing an expired claim; it must never mutate `Ownership` or
  `lifecycle_state`, and must never call or bypass
  `validate_lifecycle_transition`. The §9.1↔§24.1 contradiction itself is
  explicitly *not* resolved by this implementation -- neither section is
  silently treated as overriding the other. Applying the actual
  consequence (`ClaimStatus.EXPIRED`, and whatever lifecycle transition
  the caller's governing operational policy actually requires) is a
  separate, explicit, caller-controlled operation (a future CLI mutation
  command), matching the codebase's existing pure-check/explicit-mutate
  separation (`validate_lifecycle_transition` checks, `work set-state`
  mutates). **Policy shape locked**: `max_age: timedelta`, with an
  injectable `now: Optional[datetime]` for deterministic testing --
  chosen over a generic `Callable[[Ownership], bool]` predicate as the
  smallest interface that honors "policy not fixed by this pack" without
  over-generalizing; `now` is evaluation-time context, not policy, so it
  is a separate parameter. **R14's own recommendation text corrected**
  (see the Recommendations table): the original wording ("reverting
  `ClaimStatus.ACTIVE` to `EXPIRED`/`PLANNED`") conflated claim status
  with lifecycle state and implied mutation inside a function that must
  follow this codebase's established pure `check_*`/`validate_*` pattern
  -- corrected to describe a pure detection hook plus a separate explicit
  CLI mutation command. **Boundary against R10 (Phase 6's next item)
  reaffirmed**: R14 detects claim expiry only; it does not implement
  `ExecutionState.INDETERMINATE`/`RECONCILED` reconciliation, which
  remains R10's exclusive, still-untouched territory. **Next step**:
  write negative-path tests (unexpired-ACTIVE-claim → no finding;
  expired-ACTIVE-claim → finding; RELEASED claim → never flagged as
  expired; already-EXPIRED claim → no duplicate finding/mutation;
  malformed/missing `claimed_at` → a distinct validation finding, not an
  invented expiry decision; the hook leaves the `WorkItem` byte-for-byte
  unchanged; the hook never invokes `validate_lifecycle_transition`; no
  `EXECUTING → PLANNED` exception is introduced anywhere in
  `validate_lifecycle_transition`), confirm they fail for the intended
  reason, then implement minimally. Row 2.16 stays NON-CONFORMANT
  (unimplemented); tally unchanged: **44 CONFORMANT / 12 PARTIAL / 6
  NON-CONFORMANT / 1 UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0 unparsed**.
  Full suite unchanged: **379/379 passing**.

- **Phase 6 / item 1 (R14, row 2.16) — implementation DONE.** Following
  the investigation/reconciliation above, wrote negative-path tests
  first (`tests/test_claim_expiry.py`) and confirmed 14 of 15 failed for
  the intended reason (`check_claim_expiry` did not exist yet; the 15th,
  a pre-existing invariant check, correctly passed unconditionally) before
  writing any implementation. Then, per a second explicit user
  clarification on the CLI mutation command's exact boundary (should it
  ever touch `lifecycle_state`, even behind an opt-in flag?), the user
  locked: **ownership-only mutation, with no lifecycle_state path at all,
  not even behind a flag** -- explicitly rejecting a considered
  `--force-lifecycle-planned` option on the grounds that it would still
  fail today (`EXECUTING -> PLANNED` remains `LIFECYCLE_BACKWARD_TRANSITION`)
  and would misleadingly suggest R14 owns lifecycle reconciliation, which
  it does not. Implemented exactly as reconciled: **`validation.py`**
  gained `check_claim_expiry(item, max_age: timedelta, now:
  Optional[datetime] = None) -> list[Finding]` -- pure, returns
  `CLAIM_EXPIRED` for an `ACTIVE` claim whose age exceeds `max_age`,
  `CLAIM_ACTIVE_WITHOUT_TIMESTAMP`/`CLAIM_TIMESTAMP_UNPARSEABLE` for
  malformed `claimed_at` data (never silently treated as expired or
  not-expired), nothing for `RELEASED`/already-`EXPIRED`/unclaimed items;
  boundary semantics are explicit (`age <= max_age` not expired, `age >
  max_age` expired); confirmed via both a live behavioral check and a
  static AST guard (over the function's executable body, with its own
  docstring excluded so legitimate prose cross-references don't produce
  false positives) that it never calls `validate_lifecycle_transition`
  and never references `ExecutionState.INDETERMINATE`/`RECONCILED`,
  keeping R10's territory demonstrably untouched. **`cli.py`** gained
  `work expire-claim <work_id> --max-age-hours <N>` -- re-runs
  `check_claim_expiry` itself rather than trusting the caller's assertion
  (rejects with a non-zero exit and the underlying findings if the claim
  has not actually exceeded the policy); on a genuine expiry, mutates
  `Ownership` ONLY (`ClaimStatus.ACTIVE -> EXPIRED`), preserving `owner`
  and `claimed_at` verbatim as historical evidence per §24.1's own "MUST
  record the original agent's partial evidence rather than discarding
  it" clause; appends a new, auditable `LifecycleLogEntry` recording the
  original owner/timestamp/policy used; `lifecycle_state` is never read
  or written by this command at all -- confirmed live end-to-end (a
  `DISCOVERED` item's `lifecycle_state` was unchanged after expiry) and
  by a dedicated test. Full suite after implementation: **403/403
  passing** (379 prior + 15 `test_claim_expiry.py` + 9
  `test_work_expire_claim_cli.py`). Row 2.16 moves NON-CONFORMANT →
  **PARTIAL, deliberately not CONFORMANT**: the detection and
  evidence-preservation halves of §24.1 are now real, tested, and
  enforced; the `PLANNED`-transition half remains disclosed-open because
  the pack itself contradicts its own §9.1 model on that specific point,
  and this codebase does not silently resolve a pack-level contradiction
  inside application code. Fresh recount: **44 CONFORMANT / 13 PARTIAL /
  5 NON-CONFORMANT / 1 UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0
  unparsed**.

- **Phase 6 / item 2 (R10, row 2.2) — investigation, reconciliation, and
  implementation DONE.** Read §15 literally: "The Arena Agent MUST
  distinguish the EXECUTION-STATE values ... Missing completion evidence
  does not automatically mean 'not executed.' For operations with
  external consequences: Issued + no completion -> INDETERMINATE ->
  Authoritative reconciliation -> Resolved outcome, unless the governing
  specification explicitly defines another semantics." Inventoried the
  existing implementation: `ExecutionState`'s 7-value vocabulary already
  existed (`vocab.py`); `WorkItem.execution_state` already existed
  (default `PLANNED`); the only existing cross-axis check referencing it
  was `EXECUTING_WITHOUT_EXECUTION_STATE_UPDATE` (unrelated -- flags the
  default value persisting past EXECUTING, not sequencing); `work
  set-execution-state` allowed setting the field to *any* value with zero
  transition checking, unlike `work set-state`'s existing check-then-
  mutate gate for `lifecycle_state`. Confirmed no overlap with R14: its
  AST guard already proved `check_claim_expiry` never touches
  INDETERMINATE/RECONCILED, and this territory was genuinely still open.

  A real design ambiguity surfaced (per the binding stop-and-reconcile
  rule) before any code was written: §15's diagram doesn't fit
  `LifecycleState`'s single linear happy-path shape, since `ISSUED` has
  two legitimate follow-ups (`FAILED` terminal, or `INDETERMINATE ->
  RECONCILED`); and §15 itself hedges with "unless the governing
  specification explicitly defines another semantics," which implies a
  policy-dependent staleness dimension the pack does not actually define.
  Reconciled with the user across three explicit questions, all answered
  before implementation began:

  1. **Blocking vs. advisory**: an illegal transition (e.g. `ISSUED ->
     RECONCILED` skipping `INDETERMINATE`) is a **blocking ERROR at the
     CLI** -- `work set-execution-state` checks before mutating and
     refuses the command on any ERROR finding, exactly mirroring `work
     set-state`'s existing pattern -- not a warning-only advisory
     surfaced later via `work validate`.
  2. **Transition shape**: confirmed as `PLANNED -> STARTED -> ISSUED`,
     then `ISSUED` branching three ways to `COMPLETED` / `FAILED` /
     `INDETERMINATE -> RECONCILED` (`RECONCILED` terminal). This requires
     a branching graph structure, not a single ordered sequence like
     `LIFECYCLE_HAPPY_PATH`.
  3. **Stalled-`ISSUED` staleness detection**: explicitly **not** built.
     A proxy of "`lifecycle_state` has progressed past `EXECUTING`
     (reached `OBSERVED`/`VERIFIED`) while `execution_state` is still
     `ISSUED`" was proposed and **rejected** by the user: it would
     introduce a new semantic assumption -- that those lifecycle states
     necessarily imply sufficient execution evidence -- that the pack
     does not itself establish. No timestamp-based expiry policy either,
     since (unlike R14's claim expiry) §15 offers the implementation no
     equivalent "policy deferred to the caller" clause to hang a
     `max_age`-style parameter off of. This is a disclosed, genuinely
     unimplemented gap, not an oversight: the code can detect illegal
     transitions, but cannot determine that an `ISSUED` state has gone
     stale without a governing policy the pack never defines.

  Implemented exactly as reconciled, tests-first (16 tests in
  `tests/test_execution_transition.py` written and confirmed to fail for
  the correct reason -- `ImportError: cannot import name
  'validate_execution_transition'` -- before any implementation code
  existed; later grew to 19 with the addition of AST-guard tests). Added
  `vocab.EXECUTION_TRANSITIONS: dict[ExecutionState, tuple[ExecutionState,
  ...]]`, a closed transition graph transcribed directly from §15's
  diagram. Added `validation.validate_execution_transition(from_state,
  to_state) -> list[Finding]`, mirroring `validate_lifecycle_transition`'s
  existing style: no-op transitions always legal; legal graph edges pass;
  `ISSUED -> RECONCILED` specifically produces
  `EXECUTION_STATE_SKIPPED_INDETERMINATE` (the exact rule §15 states, not
  a generic illegal-transition code, so the message can name the specific
  requirement); any other undefined jump produces
  `EXECUTION_STATE_ILLEGAL_TRANSITION`. Confirmed via AST-guard tests
  (mirroring R14's precedent) that the function's executable body never
  reads `.lifecycle_state`/`LifecycleState` as code and never references
  `datetime`/`timedelta` -- the rejected staleness-proxy design is absent
  by construction, not just by docstring claim. Wired into `cli.py`'s
  `work set-execution-state`: calls the check before mutating, exits 1
  with the findings on any ERROR, otherwise persists as before. Fixed one
  pre-existing test (`tests/test_cli.py::test_full_cli_workflow`) that had
  exercised the previously-permitted illegal jump `PLANNED -> COMPLETED`
  directly -- amended to assert the jump is now rejected
  (`EXECUTION_STATE_ILLEGAL_TRANSITION`) and then route through the newly
  enforced legal path (`STARTED -> ISSUED -> COMPLETED`) instead of
  silently working around the new invariant. Added a dedicated
  `tests/test_work_set_execution_state_cli.py` (7 tests) covering the CLI
  gate specifically: illegal-jump rejection, confirmation that a rejected
  transition does not mutate on-disk state, `ISSUED -> RECONCILED`
  rejection at the CLI layer, the full legal path through `INDETERMINATE`
  to `RECONCILED`, the legal path to `FAILED`, rejection of any exit from
  a terminal state, and `--json` mode reporting the rejection's findings.
  Manually smoke-tested end-to-end (illegal `PLANNED -> ISSUED` skip
  rejected; legal `STARTED -> ISSUED` accepted; illegal `ISSUED ->
  RECONCILED` rejected with the specific skip-code; legal `ISSUED ->
  INDETERMINATE -> RECONCILED` accepted and persisted). Full suite after
  implementation: **429/429 passing** (403 prior + 19
  `test_execution_transition.py` + 7
  `test_work_set_execution_state_cli.py`, with 1 pre-existing test
  amended rather than added). Row 2.2 moves NON-CONFORMANT → **PARTIAL,
  deliberately not CONFORMANT**: the objectively-checkable
  transition-legality rule (including the specific `INDETERMINATE`
  skip-detection §15 names) is now real, tested, and enforced as a
  blocking CLI gate; the policy-dependent "stalled `ISSUED`" staleness
  detection remains a disclosed, genuinely unimplemented gap, exactly
  analogous to how R14 left the `PLANNED`-reversion half of §24.1
  disclosed-open rather than silently deciding it. Fresh recount: **44
  CONFORMANT / 14 PARTIAL / 4 NON-CONFORMANT / 1 UNVERIFIED / 9
  NOT-APPLICABLE = 72 rows, 0 unparsed**.

- **Phase 6 / item 3 (R16, row 3.4) — investigation, reconciliation, and
  implementation DONE.** Read §26.2 literally: "An override changes what
  the agent is permitted to do next; it never retroactively changes a
  classification. Example: overriding Stop Condition 2 ... does not make
  the component `IMPLEMENTED` -- the component remains classified
  `ABSENT`/`PLANNED`." Inventoried the existing implementation and found
  the original recommendation's premise was **factually wrong**: it
  claimed no mechanism existed "to name the affected unit" on an
  override, but `DecisionRecord.related_unit_ids`/`related_work_item_ids`
  already existed (added during earlier Phase 5B work) and were already
  CLI-wired via `decision create --related-unit`/`--related-work-item`.
  What was genuinely missing was narrower: `validate_decision_record`
  never validated either field at all -- no linkage-completeness check,
  no dangling-reference check, nothing. Also confirmed via full command
  inventory that **no CLI command mutates `KnowledgeUnit.
  implementation_status`/`evidence_class` or `WorkItem.evidence_class`
  after creation at all** (only `unit create` sets these; `unit
  set-state`/`work gate`/`work set-execution-state` touch unrelated
  fields) -- so the audit's original "two independent CLI commands race"
  framing described a scenario the actual CLI surface doesn't expose.

  A real representation gap surfaced (per the binding stop-and-reconcile
  rule) before any code was written: "strengthened... in a way the
  override doesn't itself substantiate" is inherently a causal,
  before/after claim, but neither `KnowledgeUnit.implementation_status`/
  `evidence_class` nor `WorkItem.evidence_class` carry any history or
  snapshot (unlike `lifecycle_state`, which has `lifecycle_log`) --
  nothing records a timestamp correlating a classification value to a
  specific override decision. Reconciled with the user across three
  explicit questions, all answered before implementation began:

  1. **Scope**: **link/visibility check only.** Two other options were
     explicitly declined: (a) a narrow rule scoped literally to Stop
     Condition #2 (the pack's only worked example) flagging a related
     unit currently classified `PRESENT`/`IMPLEMENTED` -- rejected because
     it would still assume the current value was *caused by* the
     override, a causal claim the data cannot support (an identical class
     of shortcut already disclosed and rejected in `InventoryItem`'s
     docstring, Recommendation R4, row 1.14, for "two SAMPLED items can
     legitimately share identical, true evidence"); and (b) adding a new
     classification-snapshot field to make a real before/after comparison
     possible -- rejected as a real schema-design surface (when is it
     captured? what if multiple units are related? what about historical
     records predating the field?) not required merely to make §26.2's
     actual link requirement checkable.
  2. **Missing-linkage severity**: **WARNING**
     (`OVERRIDE_WITHOUT_LINKED_UNIT`), matching
     `OVERRIDE_WITHOUT_SCOPE`/`OVERRIDE_WITHOUT_RESIDUAL_RISK`'s existing
     severity tier for adjacent §26.2 completeness gaps -- the override
     itself can still be fully attributed and scoped; a missing link
     makes it less traceable, not itself invalid. (An earlier draft
     answer in this reconciliation round momentarily proposed ERROR before
     being corrected back to WARNING on review -- resolved explicitly
     before any test was written.)
  3. **Dangling-reference severity**: **ERROR**
     (`RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND`), mirroring
     `RELATED_DECISION_NOT_FOUND`'s existing ERROR tier exactly -- a
     dangling reference is the same class of defect regardless of which
     record type it points at.

  Implemented exactly as reconciled, tests-first (11 tests added to
  `tests/test_validation.py`, confirmed to fail for the correct reason --
  `TypeError: validate_decision_record() got an unexpected keyword
  argument` for the mapping-dependent cases, `assert []` for the
  not-yet-implemented `OVERRIDE_WITHOUT_LINKED_UNIT` case -- before any
  implementation code existed). `validate_decision_record` gained two
  optional `units`/`work_items: Optional[dict[str, ...]]` parameters,
  mirroring `validate_final_report`'s existing `decisions` mapping
  pattern exactly (dict, not bare iterable, so "not supplied" is
  distinguishable from "supplied but dangling"; silent skip, not a
  manufactured pass, when a mapping is omitted). Added
  `OVERRIDE_WITHOUT_LINKED_UNIT` (WARNING) inside the existing
  `overrides_stop_condition is not None` block, alongside
  `OVERRIDE_WITHOUT_SCOPE`/`OVERRIDE_WITHOUT_RESIDUAL_RISK`. Added
  `RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND` (ERROR)
  unconditionally on whether the decision is an override at all, since
  `related_unit_ids`/`related_work_item_ids` are general-purpose fields,
  not override-only ones -- only fires when the corresponding mapping is
  actually supplied. Added `cli.py` helpers `_related_units`/
  `_related_work_items_for_decision` (mirroring `_related_decisions`'s
  best-effort-load-tolerate-absence pattern) and wired them into all four
  `decision create`/`resolve`/`show`/`validate` call sites. Manually
  smoke-tested end-to-end through real storage: an override with no
  linked unit correctly showed `OVERRIDE_WITHOUT_LINKED_UNIT`; adding
  `--related-unit` to a real, existing unit correctly suppressed it; a
  dangling `--related-unit` correctly produced `RELATED_UNIT_NOT_FOUND`.
  Added 5 CLI round-trip tests in `tests/test_cli.py` covering the same
  paths through real storage. Full suite after implementation: **445/445
  passing** (429 prior + 11 `test_validation.py` + 5 `test_cli.py`). Row
  3.4 moves NON-CONFORMANT → **PARTIAL, deliberately not CONFORMANT**:
  the affected-unit linkage/visibility requirement is fully implemented,
  tested, and enforced; the causal "strengthened beyond what the override
  substantiates" half of §26.2 remains a genuinely unimplemented,
  disclosed gap -- no classification history is persisted anywhere in
  this schema to make that comparison honestly, exactly the same category
  of disclosed permanent verification boundary already established for
  R4 (row 1.14) and left open by R10/R14 in their own respective domains.
  Fresh recount: **44 CONFORMANT / 15 PARTIAL / 3 NON-CONFORMANT / 1
  UNVERIFIED / 9 NOT-APPLICABLE = 72 rows, 0 unparsed**.

- **Phase 6, R7 (§11 Authority Contract, row 1.25, "if still required")
  investigated and closed.** Extracted §11's literal text: the Arena
  Agent MUST distinguish knowledge/permission/capability/authorization/
  execution; any derivation MUST satisfy `derive(A, C) ⪯ A` for
  attenuable authority (§0.3: a partial order, attenuation only, never
  amplification); no decomposition may introduce ambient authority,
  implicit capability creation, capability duplication, capability
  amplification, hidden capability lookup, or authority smuggling through
  metadata. Critically, **unlike §26.2 (which gave one concrete worked
  example, SC#2, that grounded R16's implementation), §11 gives no
  worked example at all** -- it states the invariant abstractly with no
  `A`/`C` mapped onto any pack concept.

  Inventoried every authority-related field in this codebase:
  `WorkItem.required_authority`/`forbidden_authority`,
  `KnowledgeUnit.authority_implications`, and
  `DecisionRecord.required_authority` are all opaque free-text strings,
  never validated, never CLI-settable via a dedicated mutation command,
  display-only in `reporting.py`. `AuthorizationState.ATTENUATED` exists
  as an enum value but is a status flag on an independent axis (§9.1 --
  "was this request attenuated, yes/no"), not a `⪯` relation between two
  authority values; it does not supply the missing algebra.
  `GraphNodeType.CAPABILITY`/`GraphEdgeType.AUTHORIZES` exist in the
  vocabulary but are wired into no validation or CLI logic anywhere.
  R7's own Recommendations-table worked example -- "a work item's
  authority must not be broader than its claimed source unit's
  `authority_implications`" -- does not actually work as stated, since
  both fields are single free-text strings with no defined ordering to
  check "broader than" against.

  The directly relevant precedent is **R8's own resolution of the
  adjacent §13 (External Effect Contract)**: disclosed out-of-scope, not
  implemented, because this package "is deliberately a record-keeping /
  validation / reporting system, not an execution engine" that never
  crosses an effect/authority-exercising boundary. R8's resolution
  explicitly states the authority-related fields "can inform such a
  caller's own enforcement, but they are not themselves an External
  Effect Contract implementation" -- language that generalizes directly
  to §11.

  **Stop-and-reconcile.** Two structurally different paths were
  presented: (1) disclose as out-of-scope, R8-style, no new type/field/
  check; or (2) build one minimal, additive, checkable case -- e.g. a new
  `WorkItem.capabilities: list[str]` field plus a `validate_work_item`
  check that a work item's capabilities are a subset of its source
  unit's capabilities (`⊆` as the concrete `⪯`). The user selected (1),
  disclosure, with one explicit wording safeguard: the disclosure must
  distinguish "not applicable to this package's enforcement boundary"
  from "§11 is not normative" -- the latter would be incorrect. A
  secondary dependency check was run against §3 (Trust Model, R1's own
  target) to confirm it supplies no authority-value algebra either: §3
  defines a trust-*tier* hierarchy of actors (Human/Governance → Arena
  Supervisor → Arena Agent), entirely orthogonal to §11's concern (which
  is about authority/capability *values* attenuating through derivation,
  not which actor tier issued an authorization) -- confirming R1 and R7
  are genuinely independent gaps, not one gap wearing two numbers.

  Implemented exactly as reconciled, tests-first: 4 new tests added to
  `tests/test_scope_disclosures.py` (`test_package_docstring_discloses_
  no_authority_contract_enforcement`,
  `test_work_item_docstring_points_to_the_authority_contract_scope_
  disclosure`,
  `test_knowledge_unit_docstring_points_to_the_authority_contract_scope_
  disclosure`,
  `test_decision_record_docstring_points_to_the_authority_contract_scope_
  disclosure`), confirmed to fail for the correct reason (`AssertionError:
  assert '§11' in ...`) before any docstring text existed. Then,
  documentation-only: the package docstring (`arena_agent/__init__.py`)
  gained a "Scope: no Authority Contract enforcement (v2 §11)" section
  mirroring the existing §13 section's structure and naming R7 and the
  rejected `capabilities`/subset-inclusion alternative explicitly; the
  `WorkItem` docstring's existing R8/§13 paragraph gained a follow-on
  sentence pointing to the new §11 disclosure; `KnowledgeUnit` and
  `DecisionRecord` docstrings (previously one-line) were each extended
  with a paragraph pointing to the same disclosure for their own
  authority-related field. Every disclosure explicitly states that §11
  **remains normative** for a system that actually performs derivation --
  matching the requested safeguard. No change to `AuthorizationState`,
  any model field, `validation.py`, `cli.py`, or lifecycle/execution
  logic. Full suite after implementation: **449/449 passing** (445 prior
  + 4 new disclosure tests), zero regressions.

  Row 1.25 moves NON-CONFORMANT → **NOT-APPLICABLE-by-disclosed-scope**
  (not PARTIAL -- no behavior changed, matching R8's own row 1.27
  disposition exactly). Fresh recount, parsed directly from this
  document's own table rows: **44 CONFORMANT / 15 PARTIAL / 2
  NON-CONFORMANT / 1 UNVERIFIED / 10 NOT-APPLICABLE = 72 rows, 0
  unparsed**. The two remaining NON-CONFORMANT rows are 1.5 (R1's own
  target) and 4.2 (an unrelated, already-disclosed out-of-scope item) --
  confirming R1 is the only unactioned Phase 6 item left, per the locked
  order.

- **Phase 6, R1 (§3/§26.2 Trust Tier, row 1.5) — investigated,
  reconciled, implemented, tested, and closed. This completes Phase 6.**
  Extracted §26.2's literal override-authorization text: "the authorizing
  party AND their role in the trust hierarchy (§3)" is one of four
  mandatory elements an override must record, alongside condition number,
  scope, and residual risk. `decided_by` (free text) already covered the
  party half (`OVERRIDE_WITHOUT_ATTRIBUTION`, pre-R1); the role half --
  which trust-hierarchy tier issued the override -- had no representation
  anywhere in `models.py`. Unlike R7's §11 (no worked example anywhere in
  the pack), §26.2 gives §3's three-tier hierarchy explicitly
  (Human/Governance → Arena Supervisor → Arena Agent) and states in plain
  language that "a Stop Condition MUST NOT be lifted by the agent's own
  initiative" -- a concrete, machine-checkable rule, not an algebra that
  would need inventing. The stop-and-reconcile check run during R7 (see
  that changelog entry) had already confirmed §3 and §11 are genuinely
  independent gaps: §3 is a trust-*tier* hierarchy of actors, §11 is an
  authority-*value* attenuation algebra: fixing one is not a proxy for
  fixing the other, and this fix does not touch §11 at all.

  Design locked before implementation (stop-and-reconcile): (1) new
  closed-set `TrustTier` enum (`HUMAN_GOVERNANCE` / `ARENA_SUPERVISOR` /
  `ARENA_AGENT`, values `"HUMAN-GOVERNANCE"` / `"ARENA-SUPERVISOR"` /
  `"ARENA-AGENT"`) in `arena_agent/vocab.py`, following the existing
  `_StrEnum` pattern used by every other closed-set vocabulary in this
  module -- implementation-only, since Appendix A has no `TRUST-TIER`
  entry (same disclosed-vocabulary-gap pattern as `ClaimStatus`/R22).
  (2) New `DecisionRecord.decided_by_trust_tier: Optional[TrustTier] =
  None` field in `models.py`, positioned directly after `decided_by` --
  data-shape-only, no new cross-record logic, consistent with the
  five-role invariant (`models.py` may hold shape, `validation.py` alone
  holds meaning). (3) Attached narrowly to `DecisionRecord` only -- NOT
  to `raised_by`, `Ownership.owner`, or `WorkItem`'s `--by`/
  `authorized_by` option, since §3/§26.2 make no attribution claim about
  those; extending `TrustTier` onto them would add scope the pack does
  not ask for, an explicit governance violation ("do not redesign
  semantics merely to increase the conformance score"). (4) Two new
  ERROR-severity findings in `validate_decision_record`'s override
  block, ordered directly after the pre-existing
  `OVERRIDE_WITHOUT_ATTRIBUTION` check (both are halves of the same
  §26.2 bullet, so same severity, adjacent placement):
  `OVERRIDE_WITHOUT_TRUST_TIER` (fires whenever `overrides_stop_condition`
  is set and `decided_by_trust_tier` is `None`) and
  `OVERRIDE_BY_AGENT_SELF` (fires whenever `decided_by_trust_tier ==
  TrustTier.ARENA_AGENT` on an override, regardless of what `decided_by`
  itself says -- checking the *declared* tier, not string-matching free
  text, since free text is not a reliable place to detect
  self-authorization). (5) A non-override decision has no trust-tier
  obligation either way -- the field may be set or omitted freely with
  zero validation consequence, avoiding an invented restriction §3/§26.2
  never state. (6) Standing safeguard: `TrustTier` must never be
  conflated with, or ordered against, §11's `derive(A, C) ⪯ A`
  attenuation algebra (deliberately left unimplemented per R7) --
  enforced via a dedicated AST-based test scanning `validation.py`'s
  source for any `<`/`>`/`<=`/`>=` comparison involving a `TrustTier`
  value, confirming none exists (the `_StrEnum(str, Enum)` base class
  does inherit `str`'s lexicographic ordering as an unavoidable artifact,
  but nothing in this codebase exercises it).

  CLI wiring: `decision resolve` gained `--decided-by-trust-tier`
  (`click.Choice` over the three `TrustTier` values, default `None`,
  help text citing §3/§26.2 and the "MUST NOT be lifted by the agent's
  own initiative" language). `decision create` deliberately left
  unchanged -- an override cannot be resolved at creation time in this
  CLI's design, so `create` never needed the option (matches the
  "minimal/additive, no parallel concepts" governance rule). Confirmed
  via `grep`/`sed` inspection that `decision resolve`, like `decision
  create`, never calls `_exit_if_errors` -- both always persist and
  report-only, gating exit code is reserved for `decision validate`/
  `show`-family commands; this is a pre-existing invariant, not a new
  decision.

  Tests: 8 new functions in `tests/test_validation.py` (one
  parametrized ×2, 9 test items total) covering missing-trust-tier
  (ERROR), valid `HUMAN_GOVERNANCE`/`ARENA_SUPERVISOR` tiers (clean,
  parametrized), agent-self-override (ERROR), non-override decisions
  with/without a trust tier (never flagged either way), both override
  findings firing independently and simultaneously, the AST-based
  no-ordering-comparison guard, and a fully-valid clean override. A
  pre-existing fixture, `_resolved_override_decision`, was also fixed
  during this work (added `decided_by_trust_tier=TrustTier.
  HUMAN_GOVERNANCE` to its defaults) for fixture honesty, since its own
  docstring already claimed "zero findings on its own" -- a claim no
  test had directly asserted against `validate_decision_record`, so this
  was a fixture correctness fix, not a new test, and did not change the
  passing count in `test_validation.py` (215/215 before and after). Two
  new tests in `tests/test_cli.py`
  (`test_decision_override_requires_trust_tier`,
  `test_decision_override_authorized_by_the_agent_tier_itself_is_
  rejected`) exercise real CLI/storage round-trips: the second required
  moving its exit-code assertion from `decision resolve` (which never
  gates exit code) to a follow-up `decision validate` call, after an
  initial wrong assumption failed (see this session's Errors & Dead
  Ends). `tests/test_cli.py`: 40/40. Full project suite: **460/460
  passing** (458 after the validation-layer additions + these 2 CLI
  tests), zero regressions anywhere else in the suite.

  A real end-to-end manual CLI smoke test was additionally run against a
  fresh scratch workspace (not part of the persisted test suite, but
  independent confirmation the automated tests reflect real behavior
  through actual CLI/storage, not just in-process fixtures): an override
  created with no attribution showed both `OVERRIDE_WITHOUT_ATTRIBUTION`
  and `OVERRIDE_WITHOUT_TRUST_TIER` as ERROR; resolving it with
  `--decided-by` but no `--decided-by-trust-tier` cleared the
  attribution error but left the trust-tier error; resolving with
  `--decided-by-trust-tier ARENA-AGENT` produced `OVERRIDE_BY_AGENT_SELF`
  (ERROR) and a subsequent `decision validate` call exited 1; a second,
  fully-attributed override (with a linked unit, scope, and residual
  risk) resolved with `--decided-by-trust-tier HUMAN-GOVERNANCE` produced
  zero findings and `decision validate` exited 0.

  Row 1.5 moves NON-CONFORMANT → **PARTIAL** (not CONFORMANT -- §3's
  broader hierarchy outside the override-attribution context, e.g.
  `raised_by`/general actor attribution, remains free text by design;
  §3/§26.2 do not themselves require trust-tier classification anywhere
  outside the override protocol). Fresh recount, parsed directly from
  this document's own table rows: **44 CONFORMANT / 16 PARTIAL / 1
  NON-CONFORMANT / 1 UNVERIFIED / 10 NOT-APPLICABLE = 72 rows, 0
  unparsed**. The sole remaining NON-CONFORMANT row is 4.2 (an unrelated,
  already-disclosed out-of-scope item). **Phase 6 is now complete**: all
  five locked-order items (R14, R10, R16, R7, R1) are DONE. The roadmap
  proceeds to the Final Pack Conformance Review.

- **Final Pack Conformance Review -- two documentation-only defects found
  and corrected; zero behavioral drift found anywhere else.** This review
  independently re-verified, from live source and fresh CLI/pytest runs
  (not carried-forward prose), every prior phase's frozen claims, then
  found and fixed two genuine defects, both documentation-only (no code,
  test, or validation-rule change):
  - **Defect 1 -- stale "## Summary tally" section.** *Original claim:*
    the tally table in that section, and its trailing history prose,
    stated 42 CONFORMANT / 13 PARTIAL / 8 NON-CONFORMANT / 1 UNVERIFIED /
    8 NOT-APPLICABLE (the Post-Phase-5B-R21 figure), while the Baseline
    record header above it and this Changelog already correctly reflected
    the Phase-6-complete figure. *Correction:* freshly re-parsing this
    file's own 72 numbered rows (machine script, 0 unparsed) gives **44
    CONFORMANT / 16 PARTIAL / 1 NON-CONFORMANT / 1 UNVERIFIED / 10
    NOT-APPLICABLE = 72**, matching the Baseline header and this
    Changelog exactly -- the Summary-tally section simply had not been
    updated since Phase 5B while Phases 5C and 6 progressed underneath
    it. *Resolution:* the table and trailing prose were corrected in
    place to the current figure, with the now-superseded 42/13/8/1/8
    figure kept legible as explicitly-marked history rather than silently
    overwritten. No row's individual status changed -- this was a
    transcription/staleness fix only.
  - **Defect 2 -- row 1.3 cited a nonexistent finding code.** *Original
    claim:* row 1.3 (Core Contract, status-masquerading) listed
    `VERIFIED_WITHOUT_VALIDATED_EVIDENCE_STATE` as an implementing finding
    code. *Correction:* no such code exists in `validation.py`; the
    actual, tested code (confirmed live at `validation.py` line ~437,
    exercised by `test_verified_without_validated_evidence_state_is_an_error`
    in `tests/test_validation.py`, which itself asserts the correct
    string) is `VERIFIED_WITHOUT_SUFFICIENT_EVIDENCE_STATE`. This was a
    prose-only citation-name drift at audit-authoring time; the cited
    test was always correct and always passing. *Resolution:* row 1.3's
    finding-code cell was corrected; the row's CONFORMANT disposition and
    cited tests are unchanged, since the underlying behavior was never in
    question -- only the code name written in the matrix's prose was
    wrong.

  Both fixes are additive prose corrections to this matrix file only; no
  file under `arena_agent/` or `tests/` was touched, and the full suite
  remains **460/460 passing**, freshly re-run after these edits. Row
  count after the fix, re-verified once more by the same machine script:
  44/16/1/1/10 = 72, 0 unparsed -- unchanged from before the fix, as
  expected, since no row's disposition moved.

  Separately, three pack-internal citation errors were found in the v2
  instructions pack itself (not in this matrix, and not fixable in the
  codebase): a Change-Impact-Analysis cross-reference pointing at the
  wrong section number, two References to a Work Item's State block /
  "Lifecycle Log" pointing at the wrong section number, and a Knowledge
  Graph cross-reference pointing at the wrong section number. These join
  the pack's own already-disclosed drift elsewhere as observations about
  the source pack text, out of scope for a codebase fix, and are recorded
  here for completeness rather than as matrix defects -- no row in this
  matrix relies on or repeats any of these mis-citations.

  Also noted, informationally: `arena_agent_py/README.md`'s "Tests"
  section still states "241 tests" and describes only Phases 1-4; it was
  never updated across Phases 5A-6 and now undercounts the suite by 219
  tests (460 actual). This is a real documentation staleness item, but it
  sits in `README.md`, not in this conformance matrix, and is recorded
  here as a disclosed observation for the user to decide on, not
  corrected as part of this review to avoid an unrequested scope
  expansion mid-review.

## How to read this matrix

Each row is one normative requirement traced through:


```
Pack requirement → Pack section → Implementation location → Test(s) → Evidence → Status
```

Status values, used strictly:

| Status | Meaning |
|---|---|
| `CONFORMANT` | Requirement is implemented **and** a test asserts the specific behavior, not just that the code runs. |
| `PARTIAL` | Implemented for some but not all of the requirement's stated scope, or implemented without machine enforcement (e.g. documented convention only). |
| `NON-CONFORMANT` | Implementation contradicts, weakens, or omits something the pack states as MUST/MUST NOT. |
| `UNVERIFIED` | Code appears to implement the requirement but no test specifically demonstrates it — cannot be claimed CONFORMANT without evidence, per this pack's own Core Contract (§2: no claim without provenance). |
| `NOT-APPLICABLE` | The pack section is a prompt/summary/non-normative text with no independent implementation obligation beyond what's already covered by the normative sections it summarizes. |

**No `CONFORMANT` row below is asserted without a named test.** Where a
requirement is real but untested, it is marked `UNVERIFIED`, never
`CONFORMANT` — this matrix applies the pack's own standard to itself
(§2 Core Contract: "Execution ≠ Evidence").

---

## Part 1 — Normative core (§§1–14)

| # | Requirement (paraphrased) | Pack §  | Implementation | Test(s) | Status |
|---|---|---|---|---|---|
| 1.1 | Preserve WHAT IS SAID / PROPOSED / EXISTS / EXECUTED / OBSERVED / VERIFIED / UNKNOWN as distinct categories | §1 | `vocab.EvidenceClass`, `vocab.LifecycleState`, `vocab.ExecutionState` as separate closed enums; `models.KnowledgeUnit`/`WorkItem` carry independent fields for each axis | `test_vocab.py`, `test_validation.py::test_authorized_lifecycle_state_without_granted_authorization_state_is_an_error` (proves axes are independently checked, not collapsed) | CONFORMANT |
| 1.2 | Distinguish macro Pipeline (§1/§42) from micro Lifecycle (§9) | §1, §9.4 | `vocab.LIFECYCLE_HAPPY_PATH`/`LIFECYCLE_FAILURE_BRANCHES` implement only the per-item Lifecycle; the macro Pipeline (§42) has **no dedicated implementation module** — it is a narrative description of the overall Knowledge Unit → Work Item → Verification flow, not a discrete state a record holds | — | PARTIAL — the distinction is respected (nothing conflates the two), but §42's Pipeline itself is not something the code tracks as data; there is no `PipelineStage` enum or field anywhere. This is defensible (the Pipeline is an emergent property of which records exist at what stage, not itself a piece of state) but it means §9.4's mapping table is not machine-checkable, only true by construction. |
| 1.3 | Agent must not promote a weaker category into a stronger one (Core Contract) | §2 | `validation.derive_overall_status_ceiling` + `STATUS_MASQUERADING` finding; `validate_knowledge_unit`'s `CONFIDENCE_TOO_LOW_FOR_CLASS`; `validate_work_item`'s `PASS_WITHOUT_EVIDENCE`/`VERIFIED_WITHOUT_SUFFICIENT_EVIDENCE_STATE` | `test_validation.py::test_status_masquerading_negative_path_matrix` (parametrized, 8 combinations, frozen Phase 1 test), `test_pass_without_evidence_is_an_error`, `test_verified_without_validated_evidence_state_is_an_error` | CONFORMANT |
| 1.4 | "Architecture says X should exist ≠ X exists" (repository reality example) | §2, §6 | `validate_knowledge_unit`'s `IMPLEMENTED_WITHOUT_REPO_EVIDENCE`; `RepoAudit.repository_modified` invariant | `test_validation.py::test_implemented_status_without_repo_evidence_is_an_error`, `test_cli.py::test_repo_audit_scan_fs_does_not_modify_repo` | CONFORMANT |
| 1.5 | Trust hierarchy: Human/Governance → Supervisor → Agent (§3) | §3 | **Implemented for the concrete case v2 §26.2 actually specifies: Stop Condition override attribution.** New closed-set `TrustTier` enum (`HUMAN-GOVERNANCE` / `ARENA-SUPERVISOR` / `ARENA-AGENT`, `arena_agent/vocab.py`, implementation-only vocabulary mirroring the `ClaimStatus`/R22 precedent -- no `TRUST-TIER` entry exists in Appendix A) plus new optional `DecisionRecord.decided_by_trust_tier: Optional[TrustTier]` field. `validate_decision_record` requires it (`OVERRIDE_WITHOUT_TRUST_TIER`, ERROR) whenever `overrides_stop_condition` is set, and rejects `ARENA-AGENT` as the declared tier (`OVERRIDE_BY_AGENT_SELF`, ERROR) -- directly enforcing §26.2's literal "MUST NOT be lifted by the agent's own initiative." Deliberately narrow, matching R1's own recommendation text: only `DecisionRecord`'s override attribution is covered; `raised_by`, `Ownership.owner`, and `WorkItem`'s authorization CLI option remain untouched free text, since §3/§26.2 make no attribution claim about those. `TrustTier` is a closed-set actor-identity classification only -- it carries no ordering/magnitude/`⪯` relation and is never conflated with the v2 §11 Authority Contract's attenuation algebra (Recommendation R7). | `tests/test_validation.py::test_override_without_trust_tier_is_an_error`, `::test_override_with_human_governance_or_supervisor_trust_tier_is_not_flagged` (parametrized, both tiers), `::test_override_authorized_by_the_agent_tier_itself_is_an_error`, `::test_decision_without_an_override_is_never_flagged_for_missing_trust_tier`, `::test_non_override_decision_with_a_trust_tier_set_is_not_flagged_either_way`, `::test_override_without_attribution_and_without_trust_tier_reports_both_independently`, `::test_trust_tier_ordering_is_never_used_anywhere_in_validation_source` (AST-based, confirms no `<`/`>`/`<=`/`>=` comparison involving TrustTier exists in validation.py), `::test_fully_valid_override_with_trust_tier_is_clean`; `tests/test_cli.py::test_decision_override_requires_trust_tier`, `::test_decision_override_authorized_by_the_agent_tier_itself_is_rejected` (both exercise real CLI/storage round-trips) | PARTIAL (Recommendation R1, closed) — the concrete, machine-checkable half of §3 that §26.2 actually operationalizes (override attribution's trust-tier requirement, and the literal agent-self-override exclusion) is now implemented and enforced; deliberately not CONFORMANT, since §3's broader hierarchy (e.g. `raised_by`, general actor/ownership attribution outside the override context) remains free text by design -- §3/§26.2 do not themselves require trust-tier classification anywhere outside the override protocol, so extending `TrustTier` further would add scope the pack does not ask for, not close a real gap. |
| 1.6 | §3.1: trust hierarchy exists to allow overrides | §3.1 | See §26.2 row (2.12) — override mechanism exists; its *authorization-tier* check is the gap noted in 1.5 | — | PARTIAL (mechanism present, authority-tier verification absent) |
| 1.7 | §4 Fundamental Separations table (14 named separations) | §4 | Each separation maps to a later, more specific section already covered elsewhere in this matrix (Authority/§11, Validation/execution not applicable to a static implementation, Agent state/repository state via `Workspace`, etc.) | — | NOT-APPLICABLE as its own row — §4 is a summary table; see the rows for its constituent sections (§11, §14, §16, §23) for actual conformance. |
| 1.8 | §4.1 Ingested Content Contract: classify, never obey, ingested text | §4.1 | `content_scan.py` (`ANTI_PATTERN_PHRASES`, `DIRECTIVE_PATTERNS`, `scan_text`); `FinalReport.content_scan_anomalies: list[dict[str, str]]` (new, additive field: `kind`/`matched_text`/`context` per entry, deliberately excluding `start`/`end` -- source-position offsets are not required by §4.1 or the existing report contract, and would need their own explicit decision to add); `cli.py scan-content` gained `--attach-to-report <report-id>` (explicit-only: running `scan-content` with no option never touches any report; the option loads the named `FinalReport`, converts each `ContentFlag` to a dict, appends, and persists; a nonexistent report ID fails via the pre-existing `RecordNotFound` path, not a new §4.1 rule); `validation.py` gained one shape-only check, `MALFORMED_CONTENT_SCAN_ANOMALY` (WARNING if an entry lacks `kind`) mirroring `PRESENT_WITHOUT_EVIDENCE`'s style -- deliberately does not assert or imply coverage completeness, since no field links a `FinalReport` to which source content it claims to have scanned; `reporting.py` gained a "## Content Scan Anomalies" section (table, or "_none flagged_" when empty), captioned with §4.1's own "evidence about the source, not license to act on it" language so it is never mistaken for a verification conclusion. | `test_content_scan.py` (4 pre-existing), `test_cli.py::test_scan_content_json_mode` (pre-existing), `tests/test_content_scan_final_report.py` (14 new tests: pre-implementation negative-path proof the field didn't exist; field exists and defaults to `[]`; zero-flags scans yield `[]`, never a manufactured entry; structured shape preserved (not flattened to prose); populating anomalies never mutates `failures`/`overall_status`; JSON round-trip through real `Workspace` storage; `scan-content` alone never mutates any report; `--attach-to-report` appends structured flags; attaching to a nonexistent report fails cleanly; attaching a clean scan leaves the list empty; missing-`kind` entry is flagged; well-formed entry is not flagged; empty list is never flagged; an anomaly's mere presence never produces an ERROR) | CONFORMANT (Recommendation R2, closed) — **Original claim**: the detection mechanism is real and tested, but nothing wires `scan_text` output into `FinalReport`, and §4.1's own "(§27)"/"(§37)" cross-references for "logged as an anomaly"/"reported in the Final Report" are themselves stale (§27 is the Work Item template, with no anomaly concept anywhere in it; §37 is the Counterexample Minimizer prompt, not the Final Report, which is actually §39/§40). **Correction: both true**, but neither the missing wiring nor the stale cross-references are new ambiguities: the §37 drift matches an already-established codebase convention (`models.py`'s `# v2 §26.2/§39/§40` comment from R17) of reading the pack's "§37 → Final Report" self-references as meaning §39/§40, and §4.1's own sentence already resolves the observation-vs-verification question in its own text ("it is evidence about the source, not license to act on it"), so a scan flag is never treated as, or allowed to influence, a verification conclusion. **Resolution**: added the minimal additive wiring the missing-link claim actually calls for -- a structured field, an explicit-only CLI attach path, and a shape-only validation check -- without resolving the pack's own pre-existing, unrelated citation drift (acknowledged, not fixed, since fixing pack prose is out of scope for this codebase). Per explicit user direction, no check asserting or implying scan *coverage* was added, since no model in this codebase establishes which source content a `FinalReport` claims to cover -- such a check could only assert shape, not real coverage, and would manufacture false confidence. |
| 1.9 | §5 every extracted statement gets exactly one `EVIDENCE-CLASS` | §5 | `KnowledgeUnit.evidence_class: EvidenceClass` (required, non-optional, no default) | `test_vocab.py`, `test_validation.py` (throughout) | CONFORMANT |
| 1.10 | §5.1 Confidence scale + `VERIFIED` must not carry `LOW`/`NONE` | §5.1 | `vocab.MIN_CONFIDENCE_FOR_CLASS`, `validation.validate_knowledge_unit`'s `CONFIDENCE_TOO_LOW_FOR_CLASS` | `test_validation.py::test_verified_with_low_confidence_is_an_error`, `test_verified_with_high_confidence_is_clean` | CONFORMANT |
| 1.11 | §5.1 constraint applies only to `VERIFIED`, but pack's table also implies expectations for `TESTED`/`IMPLEMENTED`/`OBSERVED` (MEDIUM) and `DERIVED`/`ARCHITECTURAL-PROPOSAL` (LOW) | §5.1 | `MIN_CONFIDENCE_FOR_CLASS` now sets floors for all seven classes named in the table: `VERIFIED, EXECUTED, TESTED, IMPLEMENTED, OBSERVED` → `MEDIUM`; `DERIVED, ARCHITECTURAL_PROPOSAL` → `LOW` (new, R3). `UNKNOWN`/`EXAMPLE` deliberately have no entry — `NONE` is their documented, correct confidence per the same table, not a gap. | `test_validation.py::test_derived_or_architectural_proposal_with_none_confidence_is_an_error` (parametrized, both classes), `test_derived_or_architectural_proposal_with_low_confidence_is_clean` (parametrized, both classes, proves `LOW` itself is not flagged), `test_unknown_or_example_with_none_confidence_is_never_flagged` (parametrized, proves the *absence* of a floor for these two classes is intentional, not an oversight) | CONFORMANT (Recommendation R3, closed) — **Original audit claim**: this row was PARTIAL because `DERIVED`/`ARCHITECTURAL-PROPOSAL` had no confidence floor and could carry `NONE` silently. **Correction: True** (unlike rows 2.5/4.9, this audit claim held up under R3's investigation — there was no alternate/equivalent representation elsewhere in the schema; the floors were genuinely absent). **Resolution**: `MIN_CONFIDENCE_FOR_CLASS` extended with `DERIVED: LOW` and `ARCHITECTURAL_PROPOSAL: LOW`; the existing generic `CONFIDENCE_TOO_LOW_FOR_CLASS` check in `validate_knowledge_unit` required no code change to enforce the new floors, since it already reads from this dict. **Scope note (disclosed, not resolved by R3)**: §5.1's table names `VERIFIED`/`EXECUTED` under the `HIGH` row, but the pack's own explicit constraint sentence for `VERIFIED` only forbids `LOW`/`NONE` (i.e. permits `MEDIUM`). The current code's `MEDIUM` floor for `VERIFIED`/`EXECUTED` was left unchanged — this table-vs-sentence tension is a separate, narrower textual ambiguity than the one R3 was scoped to fix (the *complete absence* of a `DERIVED`/`ARCHITECTURAL-PROPOSAL` floor), and per the governing "do not redesign semantics merely to increase score" rule it was not silently resolved either way. See `vocab.py`'s `MIN_CONFIDENCE_FOR_CLASS` comment block for the full disclosure. If a future recommendation is opened to resolve the `VERIFIED`/`EXECUTED` table-vs-sentence tension specifically, it is not R3 and not yet numbered. |
| 1.12 | §6 Repository Reality Rule: never infer PRESENT from README/roadmap/etc. | §6 | `PresenceClass` enum; `validate_knowledge_unit`'s `IMPLEMENTED_WITHOUT_REPO_EVIDENCE`; `validate_repo_audit`'s `PRESENT_WITHOUT_EVIDENCE` | `test_present_without_evidence_is_an_error`, `test_implemented_status_without_repo_evidence_is_an_error` | CONFORMANT (as a *shape* check — see 1.13 for a caveat) |
| 1.13 | ...but the check is "has *some* provenance.commit / some evidence string", not "the evidence is actually a real, current repository fact" | §6 | Same as above | none beyond 1.12 | PARTIAL — this is an inherent limitation of any static validator over free-text evidence fields (the pack itself cannot be machine-verified beyond shape without executing an actual repo scan), but it should be stated explicitly rather than implied: `commit` being non-empty and `evidence` being non-empty are necessary, not sufficient, conditions. Not a defect, but worth naming so nobody later assumes stronger guarantees exist. |
| 1.14 | §6.1 Coverage tagging (`EXHAUSTIVE`/`SAMPLED`) + "sampled must not justify PRESENT for uninspected items" | §6.1 | `vocab.Coverage`; `InventoryItem.coverage`/`coverage_method`; `validate_repo_audit`'s `PRESENT_WITHOUT_EVIDENCE`/`SAMPLED_WITHOUT_METHOD`. What changed (R4): `InventoryItem`'s docstring now explicitly discloses that the "must not justify PRESENT for uninspected items" half of §6.1 is a permanent verification boundary, not a closeable gap -- it is a real-world-inspection fact ("was this specific item actually inspected?") that no validator over persisted strings can independently establish, the same "necessary, not sufficient" category as row 1.13. Two mechanical proxies (flagging duplicate `evidence` strings across items; flagging `evidence` that merely repeats `coverage_method`) were investigated and deliberately rejected: both would create false confidence that §6.1's actual-inspection requirement was verified when only string distinctness was, since two SAMPLED items can legitimately share identical true evidence, and two items can have superficially distinct evidence that is equally uninspected. `validate_repo_audit` gained a comment pointing to the same disclosure; no new check was added. | `test_sampled_without_method_is_a_warning` (pre-existing, unchanged); `tests/test_scope_disclosures.py::test_inventory_item_docstring_discloses_the_sampling_inspection_limit` (new, asserts the disclosure text is present, mirroring the R22/R8 disclosure-test pattern; sensitivity-checked against a mutated docstring) | PARTIAL (Recommendation R4, closed as a documentation-only disposition -- explicitly NOT reclassified to NOT-APPLICABLE, since §6.1 remains a live, applicable requirement that is genuinely partially enforced, unlike R8's §13 which has no applicable code path at all) — **Original claim**: the "must not justify PRESENT for uninspected items" half of §6.1 is not separately enforced. **Correction: True, and remains true** — investigation confirmed no mechanical check can fully close this half of §6.1 without manufacturing a heuristic that produces false confidence rather than real verification (see the two rejected proxies above). **Resolution**: the boundary is now explicitly disclosed in code (`InventoryItem`'s docstring, `validate_repo_audit`'s comment) rather than left implicit, matching row 1.13's existing disclosure pattern and the governing "do not manufacture scope merely to increase the conformance score" rule. |
| 1.15 | §6.2 Repository Identity Failure Fallback (`commit: UNKNOWN`, no guessing) | §6.2 | `RepoAudit.commit_identity_known`, `identity_failure_reason`; `validate_repo_audit`'s `UNKNOWN_IDENTITY_NO_REASON` | `test_unknown_identity_no_reason_is_a_warning`, `test_unknown_identity_with_reason_recorded_is_not_flagged` (both in `tests/test_validation.py`, added Phase 5A/R5) | CONFORMANT — R5 closed. No implementation change; the code path was already correct, only the missing executable evidence was added, plus a companion negative-of-the-negative test confirming the check doesn't fire once a reason *is* recorded (i.e. it targets the missing explanation, not the fallback path itself). |
| 1.16 | §7 Knowledge Transformation Pipeline detail (9-stage refinement) | §7 | Referenced only in `ids.py`/`models.py` docstrings; not separately modeled — same reasoning as row 1.2 | — | NOT-APPLICABLE as separate data; folded into KnowledgeUnit's field set |
| 1.17 | §8 Stable IDs: `ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>` shape; never reused for different obligations | §8 | `ids.py`: `validate_generic_id`, `new_generic_id`, `validate_dated_seq_id`, `new_dated_seq_id` (collision-checked) | `test_ids.py` (6 tests) | CONFORMANT for shape + non-collision. "Never reused for materially different obligations" (a semantic constraint) is explicitly and correctly documented in `ids.py`'s own docstring as **not machine-checkable** — this is an honest `NOT-APPLICABLE`-by-necessity rather than a silently skipped rule. |
| 1.18 | §9.1 Canonical Lifecycle: 8 happy-path states + 7 failure branches, 6 independent axes | §9.1 | `vocab.LifecycleState`, `LIFECYCLE_HAPPY_PATH`, `LIFECYCLE_FAILURE_BRANCHES`; 6 axes as 6 separate typed fields on `WorkItem` | `test_forward_one_step_is_legal`, `test_legal_failure_branch_is_accepted`, `test_illegal_failure_branch_is_rejected`, plus the cross-axis tests in row 1.3 | CONFORMANT |
| 1.19 | §9.1 gap: `NORMALIZED` has no defined failure branch (a real gap in the pack, not the implementation); every *other* documented failure-branch transition must actually be accepted, and only from its one correct source state | §9.1 | `vocab.py` docstring above `LIFECYCLE_FAILURE_BRANCHES`; `validate_lifecycle_transition`'s failure-branch check | `test_lifecycle_failure_branches_match_pack_text_exactly` (`test_vocab.py`, pre-existing — confirms the branch *table* matches the pack's 7-of-8 text); **as of Phase 5A/R6**, `test_every_documented_failure_branch_transition_is_individually_legal` (7 parametrized cases — every documented `(happy_state, failure_state)` pair is individually confirmed legal by the validator, not just one representative sample) and `test_failure_branch_from_wrong_source_state_is_illegal` (49 parametrized cases — every *wrong*-source-state pairing is confirmed rejected) in `tests/test_validation.py` | CONFORMANT — R6 closed. Previously only one of the 7 branches (`EXECUTING`→`CRASHED`) was exercised by `test_legal_failure_branch_is_accepted`/`test_illegal_failure_branch_is_rejected`; the other 6 legal pairings and all 49 wrong-source combinations are now exhaustively checked. No implementation change. |
| 1.20 | §9.2 Refinement Rule: sub-states must map to canonical state, may not skip | §9.2 | `validate_lifecycle_transition`'s `LIFECYCLE_SKIPPED_STATE` | `test_skipping_states_is_illegal_run_task_done_antipattern` | CONFORMANT for the *skip* half. The "sub-state must declare its mapping" half (e.g. `WorkItem`'s own `### State` block in the template) has **no machine-checked equivalent** — `WorkItem` has no sub-state field at all, only the canonical `lifecycle_state` directly, so there is nothing to check a mapping *of*. This sidesteps rather than satisfies §9.2's refinement-declaration requirement, because this implementation chose not to support refined sub-states. PARTIAL. |
| 1.21 | §9.3 Compound Transition: no `RUN_TASK → DONE`-style skip | §9.3 | Same as 1.20 (`LIFECYCLE_SKIPPED_STATE`) | `test_skipping_states_is_illegal_run_task_done_antipattern` | CONFORMANT |
| 1.22 | §9.4 Pipeline-to-Lifecycle mapping table | §9.4 | Documented in `vocab.py`/`validation.py` comments; not enforced as data (see 1.2) | — | NOT-APPLICABLE as enforceable rule (descriptive table, no MUST attached) |
| 1.23 | §10 Resource Contract: identify resource dimensions explicitly | §10 | `WorkItem.resource_budget: dict[str, Any]` — free-form, no required keys, no enum of "dimensions" | none | PARTIAL — nothing *requires* a work item that consumes resources to actually populate `resource_budget`; the pack says "MUST identify them explicitly" but this implementation only checks conservation *if* the dict happens to contain the right keys (see 1.24). A work item that consumes real resources but never populates `resource_budget` is currently invisible to validation. |
| 1.24 | §10.1 Conservation snapshot invariant: `initial_total = available + reserved + consumed` | §10.1 | `validation._validate_resource_budget`'s `RESOURCE_CONSERVATION_VIOLATED` | `test_resource_conservation_violation_detected`, `test_resource_conservation_respected_passes` | CONFORMANT for the arithmetic check itself, given the dict is populated. See 1.23 for the caveat that population isn't required. |
| 1.25 | §11 Authority Contract: `derive(A, C) ⪯ A`, no ambient authority/amplification | §11 | **Documentation-only scope disclosure, no behavior change.** `authority_implications`/`required_authority`/`forbidden_authority` remain free-text strings with no structure, no partial order, no derivation check -- this package never derives a capability from an authority or exercises one (it is a record-keeping/validation/reporting system, per R8's already-established §13 precedent), so implementing `derive(A, C) ⪯ A` would require inventing an authority-value representation and attenuation relation that §11 itself never defines (no worked example exists in the pack for this section, unlike §26.2's SC#2 example). The package docstring now carries an explicit "Scope: no Authority Contract enforcement (v2 §11)" section naming R7, and `WorkItem`/`KnowledgeUnit`/`DecisionRecord` docstrings each point to it from their respective authority-related field. The disclosure explicitly states §11 **remains normative** for any system that actually performs derivation -- this is a boundary disclosure, not a claim that §11 is non-normative. | `tests/test_scope_disclosures.py::test_package_docstring_discloses_no_authority_contract_enforcement`, `::test_work_item_docstring_points_to_the_authority_contract_scope_disclosure`, `::test_knowledge_unit_docstring_points_to_the_authority_contract_scope_disclosure`, `::test_decision_record_docstring_points_to_the_authority_contract_scope_disclosure` (each asserts the disclosure text, including §11 and R7, is actually present; mirrors the R8/R4 disclosure-test pattern) | NOT-APPLICABLE-by-disclosed-scope (Recommendation R7, closed) — previously the single largest unimplemented normative section in the pack's core (§§1–14); investigation found no worked example and no existing authority-value representation/partial order anywhere in this codebase to attach a real check to, and the R7 recommendation's own worked example ("a work item's authority must not be broader than its claimed source unit's `authority_implications`") does not work as stated because both fields are unstructured free text with no defined ordering. Building a new `capabilities`/subset-based algebra was explicitly considered and rejected (see R7's Recommendations-table entry) as inventing semantics §11 itself never specifies. |
| 1.26 | §12 Action Contract: 12 required fields per action; "not complete merely because the tool returned successfully" | §12 | The "not complete merely because tool returned" half is implemented via `VERIFIED_WITHOUT_LIFECYCLE_LOG`/`VERIFIED_WITHOUT_POSTCONDITIONS`. The literal 12-field Action Contract (ACTION-ID, Purpose, Inputs, Preconditions, Authority required, Resources required, Side effects, Persistence requirements, Outputs, Postconditions, Failure states, Recovery behavior, Evidence generated) has **no dedicated `Action` dataclass** — `WorkItem` covers most of the same ground (id, inputs, outputs, preconditions, postconditions, failure_modes) but not all (no explicit `Side effects` or `Recovery behavior` field; `resource_budget` stands in for "Resources required" loosely). | `test_verified_without_lifecycle_log_is_an_error`, `test_verified_without_postconditions...` (WARNING variant) | PARTIAL — the *behavioral* rule (no completion without evidence) is conformant; the *structural* Action Contract shape is folded into `WorkItem` incompletely rather than modeled as its own object. |
| 1.27 | §13 External Effect Contract pipeline (Proposal→...→Verification) as specialization of §14 | §13 | Still not modeled as data — no "effect" object, no durability-boundary check, no `HostInvoked(E) ⇒ DurableIssued(E)` invariant. What changed (R8): `arena_agent`'s package docstring now carries an explicit "Scope: no External Effect Contract (v2 §13)" section stating why (this package never invokes an external effect on the agent's behalf), and `WorkItem`'s docstring (the record type closest to §13's authority concept, via `required_authority`/`forbidden_authority`) points a reader at that disclosure. `README.md`'s "Design choices worth knowing about" section carries the same disclosure for a reader who never opens the source. | `tests/test_scope_disclosures.py::test_package_docstring_discloses_no_external_effect_contract`, `::test_work_item_docstring_points_to_the_external_effect_scope_disclosure` (both assert the disclosure text is actually present, mirroring R22's docstring-disclosure test pattern; sensitivity-checked by temporarily mutating a scratch copy of the docstring and confirming the assertions fail) | NOT-APPLICABLE-by-disclosed-scope (Recommendation R8, closed) — **Original claim**: NON-CONFORMANT because this scope decision was undocumented anywhere in the code. **Correction: True** (confirmed: before this fix, no docstring, comment, or README section anywhere in this package mentioned §13 or an External Effect Contract at all — the only place the scope decision existed was this matrix). **Resolution**: this remains deliberately a documentation-only fix, per R8's own definition ("documentation, not necessarily implementation") and the governing "do not manufacture scope merely to increase the conformance score" rule — no `Effect` object, pipeline, or durability-boundary check was added, since nothing in this package crosses an effect boundary for such a check to guard. The scope decision is now disclosed in three places (package docstring, `WorkItem` docstring, README) instead of only in this audit artifact, and two tests exist so the disclosure can't silently regress. |
| 1.28 | §14 Dependency Direction (Domain→...→Verification, forbidden reversals) | §14 | The **module import graph itself** — verified via static AST inspection in this audit (see "Structural check" below) — never reverses: `models` never imports `validation`; `validation` never imports `storage`/`cli`; `storage` never imports `cli`; `export`/`html` never import backward into `cli`. This is a genuinely strong, load-bearing conformance point. | `tests/test_architecture.py::test_project_wide_import_direction_matches_v2_section_14` (project-wide AST-only import-direction check against an explicit per-module allow-list), `::test_no_module_imports_cli` (no module inverts into the presentation layer), `::test_no_circular_imports_among_local_modules` (independent DAG check derived from source text alone, not from the allow-list, so a mistake in the allow-list can't simultaneously hide a real cycle), `::test_allowed_imports_table_covers_every_module` (guards the allow-list itself against silently going stale as modules are added) | CONFORMANT — R9 closed (Phase 5A). All 4 tests pass against the current tree; the AST audit found **zero actual violations** (no production code changed). The test's sensitivity was self-verified during authoring by temporarily injecting a forbidden edge (`models.py` importing `validation`) into a scratch copy and confirming the test failed with a message naming the importing module, the forbidden imported module, and the violated rule — then reverting before committing. |
| 1.28-check | (evidence sub-row) Test-detection sensitivity check for row 1.28 | §14 (verification-of-verification) | n/a — this is a check of the checker itself | Manually run during authoring (not a persisted test, since it must inject then revert a real violation): `models.py` was temporarily mutated to `from .validation import Finding`, `test_project_wide_import_direction_matches_v2_section_14` failed with `"models.py imports 'validation', which is not in its allowed set..."`, the file was reverted, and the full suite was re-confirmed green before this row was written. | CONFORMANT (as a one-time authoring-time proof; not itself a standing regression test, since a standing test cannot safely inject-and-revert production code on every run — the standing protection is rows 1.28's four listed tests, which would have caught this exact case). |

### Structural check performed for row 1.28 (evidence)

**Status: superseded by an executable test as of Phase 5A/R9.** The
one-time manual AST scan below is preserved for audit-trail purposes, but
the load-bearing evidence for row 1.28 is now
`tests/test_architecture.py`, not this transcript.

```
$ python -c "ast-based import scan of arena_agent/*.py"
models.py     imports: __init__, vocab                          (no violation)
validation.py imports: graph, ids, models, vocab                (no violation)
storage.py    imports: __init__, graph, ids, models, vocab      (no violation)
reporting.py  imports: graph, models, validation, vocab         (no violation)
export.py     imports: __init__, models, reporting, storage,
                        validation, vocab                        (no violation)
html.py       imports: export, validation, vocab                (no violation:
                                                                  does NOT import storage)
output.py     imports: validation                                (no violation)
cli.py        imports: __init__, content_scan, graph, ids,
                        models, output, reporting, export,
                        html, storage, validation, vocab         (no violation — cli is
                                                                  the only module allowed
                                                                  to sit at the top)
```

No module earlier in the pack's stated dependency chain
(Domain→Representation→Validation→...→Verification) imports a module later
in that chain. This confirmed §14 by construction for the tree at audit
time; as of Phase 5A/R9 this is now also protected going forward by
`tests/test_architecture.py` (4 tests), closing the "not currently
protected by a test" gap this section originally flagged.

---

## Part 2 — Contracts built on the core (§§15–24)

| # | Requirement | Pack § | Implementation | Test(s) | Status |
|---|---|---|---|---|---|
| 2.1 | §15 `EXECUTION-STATE` 7-value vocabulary | §15 | `vocab.ExecutionState` (all 7 values) | `test_vocab.py` | CONFORMANT (vocabulary only) |
| 2.2 | §15 `Issued + no completion → INDETERMINATE → reconciliation → resolved` state machine | §15 | **Implemented (Phase 6 / R10): a closed ExecutionState transition graph is now enforced.** `vocab.EXECUTION_TRANSITIONS` encodes the legal graph directly from §15's own diagram: `PLANNED -> STARTED -> ISSUED`, then `ISSUED -> COMPLETED` / `FAILED` / `INDETERMINATE -> RECONCILED` (unlike `LifecycleState`'s single linear happy path, `ISSUED` genuinely branches three ways). `validation.validate_execution_transition(from_state, to_state) -> list[Finding]` checks a proposed transition against that graph and returns `EXECUTION_STATE_SKIPPED_INDETERMINATE` specifically for `ISSUED -> RECONCILED` (the exact rule §15 states), or `EXECUTION_STATE_ILLEGAL_TRANSITION` for any other undefined jump. `cli.py`'s `work set-execution-state` now calls this check BEFORE mutating and refuses the command (non-zero exit, unchanged on-disk state) on any ERROR finding -- a blocking gate mirroring `work set-state`'s existing check-then-mutate pattern for `lifecycle_state` (an explicit, reconciled design decision: blocking ERROR, not a warning-only advisory via `work validate`). Confirmed via AST-guard tests that the check never reads `.lifecycle_state`/`LifecycleState` and never references `datetime`/`timedelta` as executable code -- it is a pure transition-legality check only, with no smuggled staleness inference. **Deliberately NOT implemented, and disclosed rather than silently decided**: detecting a *stalled* `ISSUED` item that never reaches any terminal/`INDETERMINATE` follow-up at all. §15 states "missing completion evidence does not automatically mean 'not executed'" but defines no staleness threshold or policy ("unless the governing specification explicitly defines another semantics" -- it doesn't here). Using `lifecycle_state` progression (e.g. reaching `OBSERVED`/`VERIFIED`) as a staleness proxy was explicitly considered and rejected: it would assume those lifecycle states necessarily imply sufficient execution evidence, a semantic claim the pack does not itself make. No timestamp-based expiry policy is implemented either, since no governing policy for it exists in the pack (distinct from R14's claim-expiry policy, which the pack explicitly defers to the caller -- §15 offers no equivalent deferral clause for `ISSUED` staleness). | `vocab.py` (`EXECUTION_TRANSITIONS`), `validation.py` (`validate_execution_transition`), `cli.py` (`work_set_execution_state`); tests: `tests/test_execution_transition.py` (19: legal transitions, `ISSUED -> RECONCILED` skip-detection, all-terminal-state rejections, backward-transition rejection, AST guards for no lifecycle_state/no time-based logic, pure-function signature check) + `tests/test_work_set_execution_state_cli.py` (7: illegal-jump rejection, rejected-transition-does-not-mutate, skip-INDETERMINATE rejection at the CLI, full legal path to RECONCILED, legal path to FAILED, terminal-state-exit rejection, `--json` mode reports the rejection) + 1 pre-existing test in `tests/test_cli.py` amended to route through the now-enforced legal path (`PLANNED -> STARTED -> ISSUED -> COMPLETED`) instead of the previously-permitted direct jump. | PARTIAL — deliberately not CONFORMANT: the objectively-checkable transition-legality rule is fully implemented, tested, and enforced as a blocking CLI gate; the policy-dependent "stalled ISSUED" staleness detection remains a genuinely unimplemented, disclosed gap (no governing policy exists in the pack to check it against). See Recommendation R10 and the Changelog. |
| 2.3 | §15 "MUST NOT silently rewrite history to make recovery convenient" | §15 | `WorkItem.log()` only appends (never a `remove`/`clear` method on `lifecycle_log`); `WikiChangeHistoryEntry` likewise append-only via `wiki update` | `test_wiki.py::test_wiki_update_appends_change_history_and_adds_reference` (confirms append, not replace) | CONFORMANT for Wiki/WorkItem. Not separately tested for `DecisionRecord`/`CounterexampleRecord`, which also have no "history" list to rewrite in the first place (their state is a single current value, e.g. `DecisionRecord.status`) — so no rewrite-history risk exists for those types by construction. |
| 2.4 | §15.1 Supersession: `HISTORICAL` reclassification + `supersedes` edge + re-verification, never delete | §15.1 | `EvidenceClass.HISTORICAL` exists; `GraphEdgeType.SUPERSEDES` exists; `DecisionRecord.supersedes_decision_id` exists and is checked (`SUPERSEDED_WITHOUT_FORWARD_LINK`) | **As of Phase 5A/R11:** `test_superseded_decision_without_forward_link_is_a_warning`, `test_superseded_decision_with_forward_link_is_clean_on_that_axis`, `test_non_superseded_decision_is_never_flagged_for_missing_forward_link` (all in `tests/test_validation.py`) | PARTIAL (upgraded from UNVERIFIED, R11 closed for the narrower claim) for the `DecisionRecord.status == SUPERSEDED` mechanism specifically — now test-confirmed correct, including that it's scoped only to the `SUPERSEDED` status axis. **Still NON-CONFORMANT for the general case** — §15.1 is fundamentally about a *Work Item* (or Knowledge Unit) whose classification changes to `HISTORICAL` when a governing spec changes, with re-verification required, and `validate_knowledge_unit`/`validate_work_item` still have **no check at all** that transitioning to `HISTORICAL` also triggers a `supersedes` graph edge or forces `verification_state` reset. R11's scope (per explicit reconciliation with the user) was the narrower `DecisionRecord` mechanism only; the general-case gap is a distinct, larger item not covered by R11 and not yet separately numbered. |
| 2.5 | §16 Provenance Contract: minimum provenance fields on every knowledge item | §16 | `models._default_provenance()` — **as of Phase 5A/R12**, all 13 named fields (`source, source_type, repository, branch, commit, path, location, extraction_method, timestamp, classification, confidence, related_items`) plus `pack_version` | `test_default_provenance_matches_pack_section_16_field_list_exactly` (exact 13-key shape), `test_provenance_is_attached_by_default_to_every_provenance_bearing_record` (wired to every call site: `KnowledgeUnit`/`WorkItem`/`CounterexampleRecord`), `test_provenance_classification_defaults_to_none_like_its_pack_neighbor_confidence` (semantic: the `None` default is justified by an established precedent in the same dict, not merely convenient), `test_provenance_classification_can_hold_a_real_evidence_class_value` (semantic: confirms the field can actually carry a §5 `EVIDENCE-CLASS` value distinct from the record's own `evidence_class`, not just an inert always-`None` key) — all 4 in `tests/test_validation.py` | CONFORMANT — R12 closed, **with an explicit audit self-correction recorded below rather than a silent status change**. |

**R12 audit-correction record (v2 §16, per explicit process requirement — investigate before changing code or the matrix, then record the correction distinctly from the fix):**

```
Original audit claim (this document's first version):
  "_default_provenance() ... all 11 named fields ... matches §16 verbatim"

Correction: False. §16's literal text lists 13 fields --
  source, source_type, repository, branch, commit, path, location,
  extraction_method, timestamp, classification, confidence,
  related_items, pack_version
-- and the implementation contained only 12. "classification" was
absent entirely, and was not represented under another name:
KnowledgeUnit/WorkItem's top-level `evidence_class` field is a
record-level classification (always populated, non-optional), a
different concept from a provenance-*block*-level classification
(relevant to artifacts with no `evidence_class` at all, e.g. a graph
node/edge's provenance string) -- so it does not stand in for the
missing key.

Investigation performed before choosing a fix (targeted §16/schema
reconciliation, no code changes made until this step completed):
  1. §16's exact wording -- confirmed `classification` is a flat,
     undifferentiated required key in the provenance mapping, with no
     textual license to represent it via an existing field instead.
  2. KnowledgeUnit/WorkItem's actual schema -- confirmed evidence_class
     is a distinct, always-required top-level field; no established
     alias/equivalence convention exists anywhere in the codebase
     mapping one concept to the other.
  3. Every provenance construction/consumption path (_default_provenance,
     validators, renderers, export.py, html.py, templates) -- confirmed
     `classification`'s pack-adjacent sibling field `confidence` was
     ALSO never auto-populated anywhere; it already defaulted to `None`
     and stayed `None` until a caller supplied a real value. This is the
     established, working precedent `classification`'s default follows.

Resolution: this is a real §16 gap, not a representation-equivalence
question -- so the smallest compliant fix was applied, not a
documentation-only disposition:
  - Added "classification": None to _default_provenance() in models.py
    (additive; default None matches the precedent set by `confidence`,
    not merely convenient -- see the investigation above and
    test_provenance_classification_defaults_to_none_like_its_pack_neighbor_confidence).
  - Did NOT derive classification from evidence_class, move
    evidence_class, or redesign KnowledgeUnit/WorkItem.
  - Added 4 tests (2 shape, 2 semantic -- see the Test(s) column above),
    including one proving the field can actually hold a real
    EVIDENCE-CLASS value distinct from the record's own evidence_class,
    not just an inert always-None placeholder.
  - Confirmed backward-compatible: full suite (312/312) passes,
    including every export/html/wiki test that serializes provenance
    dicts, since export.py/html.py never reference `provenance` at all.
```
| 2.6 | §16 execution-evidence provenance (command, environment, seed, stdout/stderr, exit_status, artifacts) | §16 | **Not modeled.** No dataclass carries these fields; `CounterexampleRecord` comes closest (`execution_trace`, `environment`) but as a single opaque `Any`/string, not the itemized set §16 specifies. | none | PARTIAL — the closest analog (`CounterexampleRecord`) covers this loosely for failure records only; there is no general "execution evidence" record for a *successful* action's provenance (a `WorkItem`'s own `lifecycle_log` entries carry `details: dict[str, Any]` which is free-form, not the named §16 field set). |
| 2.7 | §17 Decomposition Contract: 15-field unit shape | §17 | Loosely satisfied — `KnowledgeUnit` has an analogous but not identical field set (no explicit "Verification obligations" separate from `verification_obligation: str`, which does exist; no "Evidence" field distinct from `evidence_class`/`provenance`) | none dedicated | PARTIAL |
| 2.8 | §18 Cleaning Contract (preserve list, forbidden-weaken list) | §18 | **Not implemented at all** — there is no "clean an artifact" operation anywhere in this codebase; this pack section describes an *agent behavior* (how an LLM agent should edit text), which this Python implementation, being a record/validation/reporting tool rather than a text-editing agent, does not perform. | none | NOT-APPLICABLE — correctly out of scope for what this implementation is (confirmed: the project's own stated scope, per session memory, is "data models + validation + CLI/report rendering," explicitly not an automated repo-inspection/editing engine). Listed here for completeness, not as a defect. |
| 2.9 | §19 Wiki Extraction Contract: `EXTRACTION-CLASS` + 13-field extraction shape | §19 | `vocab.ExtractionClass` (14 values, matches Appendix A.2 exactly); `KnowledgeUnit.extraction_class` optional field; `validate_knowledge_unit`'s `MISSING_EXTRACTION_CLASS` | `test_missing_extraction_class_is_a_warning`, `test_extraction_class_set_clears_the_warning`, `test_extraction_class_is_a_real_enum_not_a_bare_string` | CONFORMANT |
| 2.10 | §20 Verification Model layering (Syntax≠Schema≠Semantic≠...≠Conformance) | §20 | Implicit in the storage/validation split (`RecordCorrupted` = schema-level failure, distinct from a `Finding` = semantic-level failure) but **no explicit `VerificationLayer` concept** ties these together as the pack's 7-layer model | `test_storage.py::test_corrupted_json_record_produces_clean_error...` (schema layer); `test_validation.py` (semantic layer) — but nothing that names "layering" itself | PARTIAL — the *practice* respects the distinction (schema errors and semantic findings are genuinely different code paths with different exception types), but the pack's specific 7-layer vocabulary (Syntax/Schema/Semantic/Transition/Execution/Evidence/Conformance) is not named or exposed anywhere; a reader cannot point to "the Transition validity layer" in this code. |
| 2.11 | §21 Independent Reference Principle: production transitions must not be reused by reference transitions | §21 | **Not applicable in a direct sense** — this implementation has no "reference model" vs. "production model" pair (e.g. no differential-testing harness); §21 governs a scenario (an independent oracle for differential verification) this tool does not itself construct. `CounterexampleRecord`'s `production_trace`/`reference_trace` fields exist to *record* the results of such a comparison performed elsewhere, but this codebase does not implement the comparison itself. | none | NOT-APPLICABLE — correctly out of scope (data capture only, not a verification harness), but this should be stated explicitly somewhere in the code/docs rather than left implicit. Minor doc gap. |
| 2.12 | §22 Unified Counterexample Object — 4 cumulative stages, one object | §22 | `vocab.CounterexampleStage`, `models.CounterexampleRecord` (single class, superset fields per stage), `validation.validate_counterexample_promotion`/`validate_counterexample_record`/`promote_counterexample` | `test_promote_to_observed_failure_requires_behavior_fields`, `test_promote_to_reproducible_defect_requires_confirmation`, `test_backward_promotion_rejected`, `test_minimization_requires_full_checklist`, + 4 more | CONFORMANT — this is one of the strongest-covered sections in the whole implementation. |
| 2.13 | §22.4 Minimization safety checklist (7 items) | §22.4 | `models.MinimizationRecord.checklist` (exactly 7 keys matching the pack's list) + `all_preserved()` | `test_minimization_requires_full_checklist`, `test_minimization_succeeds_with_full_checklist` | CONFORMANT |
| 2.14 | §23 Ambiguity Contract: never guess/silently normalize; create Decision Record instead | §23 | `models.DecisionRecord` (Question/Conflicting statements/Sources/Affected components/Possible interpretations/Consequences/Required authority/Current decision/Decision provenance — all present as fields); `validate_knowledge_unit`'s `CONFLICTING_WITHOUT_DECISION_RECORD` | `test_conflicting_without_decision_record_is_an_error`, `test_resolved_without_attribution_is_an_error` | CONFORMANT for the "must create a Decision Record when conflicting" trigger. The *positive* obligation — "the agent must never silently normalize ambiguous input in the first place" — is a behavioral rule about an LLM agent's own reasoning process, which a data-validation library cannot enforce (it can only check that ambiguity, once flagged, is tracked). Correctly scoped as PARTIAL: the trackable half is conformant, the un-trackable half is inherently NOT-APPLICABLE to this kind of tool. |
| 2.15 | §24.1 Ownership/Claiming: EXECUTING requires owner; second agent MUST NOT claim an active item | §24.1 | `models.Ownership`/`ClaimStatus`; `validation.validate_work_item`'s `EXECUTING_WITHOUT_OWNER`; `cli.py work_claim`'s explicit rejection when `status == ACTIVE and owner != requested_owner` | `test_executing_without_owner_is_an_error` (validation layer) **and, as of Phase 5A, `test_work_claim_rejects_second_owner_while_active` (tests/test_cli.py)** — asserts: (a) the second claim is rejected with exit code 1 and the current owner named in both the human-readable and `--json` output; (b) the `Ownership` record (`owner`/`status`/`claimed_at`) is byte-for-byte unchanged by the rejected attempt; (c) the original owner can still act afterward, proving no partial/silent state corruption occurred underneath the observable rejection | CONFORMANT — R13 closed. Implementation (`cli.py` lines ~389–397) confirmed correct by a dedicated negative-path test; this was the single highest-priority test gap identified by the audit and is resolved as of the first item in the Phase 5A hardening batch. |
| 2.16 | §24.1 claim expiry reverts to `PLANNED`, preserving partial evidence | §24.1 | `validation.check_claim_expiry(item, max_age: timedelta, now: Optional[datetime] = None) -> list[Finding]` (pure detection hook: reports `CLAIM_EXPIRED` for an `ACTIVE` claim whose age exceeds the caller-supplied `max_age` policy, `CLAIM_ACTIVE_WITHOUT_TIMESTAMP`/`CLAIM_TIMESTAMP_UNPARSEABLE` for malformed data, and nothing for `RELEASED`/`EXPIRED`/unclaimed items; never mutates `item` and never calls `validate_lifecycle_transition`); `cli.py`'s `work expire-claim <work_id> --max-age-hours <N>` (explicit mutation command: re-runs `check_claim_expiry` itself rather than trusting the caller, then on a genuine expiry sets `ClaimStatus.ACTIVE -> EXPIRED` while preserving `owner`/`claimed_at` verbatim as historical evidence per §24.1's "MUST record the original agent's partial evidence" clause, and appends an auditable lifecycle-log entry). **Genuine pack-level normative tension found and deliberately left unresolved, not silently decided** (see the Changelog's full investigation note): §24.1's "reverts the item to `PLANNED`" clause names a transition (`EXECUTING -> PLANNED`) that `validate_lifecycle_transition` already treats as an ERROR-severity `LIFECYCLE_BACKWARD_TRANSITION` under §9.1's own canonical model (confirmed live) -- the pack itself never reconciles this. Per explicit, binding user direction, `work expire-claim` mutates `Ownership` ONLY and never touches `lifecycle_state`; a caller wanting a lifecycle change must use the pre-existing `work set-state` command, which continues to visibly enforce/reject that transition exactly as before -- no new exception, special case, or bypass was added anywhere. | 15 new tests: `tests/test_claim_expiry.py` (15: unexpired-ACTIVE -> no finding, expired-ACTIVE -> `CLAIM_EXPIRED` finding, exact-boundary age == max_age -> not expired, one-unit-past-boundary -> expired, `RELEASED` -> never flagged, already-`EXPIRED` -> no duplicate finding, unclaimed item -> no finding, missing `claimed_at` -> distinct `CLAIM_ACTIVE_WITHOUT_TIMESTAMP` finding [never an invented expiry], unparseable `claimed_at` -> distinct `CLAIM_TIMESTAMP_UNPARSEABLE` finding, `now` defaults to real current time when omitted, the hook never mutates the item byte-for-byte, an AST guard proving the hook's executable body [docstring excluded] never calls `validate_lifecycle_transition`, a guard proving `EXECUTING -> PLANNED` is still an ERROR after this change [no silent exception introduced], an AST guard proving the hook's body never references `ExecutionState.INDETERMINATE`/`RECONCILED` [keeping R10's territory untouched], and a signature guard confirming the pure `list[Finding]`-returning shape); `tests/test_work_expire_claim_cli.py` (9: command is registered, rejects a claim that has not actually exceeded the policy [re-checks itself rather than trusting the caller], succeeds on a genuinely expired claim, preserves `owner`/`claimed_at` verbatim, leaves `lifecycle_state` completely untouched, records a new auditable lifecycle-log entry, fails cleanly on an unclaimed item, fails cleanly on an already-`EXPIRED` claim without a duplicate mutation, and confirms `--json` mode reports the transition) | PARTIAL (Recommendation R14, closed as a *detection-plus-ownership-mutation* disposition, deliberately NOT CONFORMANT) — **Original claim**: `ClaimStatus.EXPIRED` exists but nothing ever sets it, and no hook exists for a caller to supply an expiry policy at all. **Correction: true, and now half-closed by design, not by omission**: the *detection* half of §24.1 (recognizing an expired claim under a caller policy) and the *evidence-preservation* half ("MUST record the original agent's partial evidence rather than discarding it") are now both fully implemented and tested; the *lifecycle-transition* half ("reverts the item to `PLANNED`") is deliberately left unimplemented because the pack itself contradicts its own §9.1 model on this point, and this codebase does not silently pick a winner inside application code. **Resolution**: PARTIAL, not CONFORMANT, is the honest disposition -- §24.1 is genuinely partially enforced (ownership expiry, real, tested, evidence-preserving) with one specific, disclosed, pack-level gap remaining open (the `PLANNED` transition), exactly the same "necessary, not sufficient" honesty already established at rows 1.13/1.14 for a different kind of unclosable gap. If the pack is ever amended to explicitly permit an `EXECUTING → PLANNED` exception for claim-expiry, that would be a new, separate, explicit decision -- not something this recommendation silently baked in. |
| 2.17 | §24.2 Resuming another agent's work — must log as new entry, not merge | §24.2 | `WorkItem.log()` always appends a fresh `LifecycleLogEntry` with its own `actor`; nothing prevents two different actors' entries in the same log, which is the mechanism §24.2 needs | none dedicated (no test constructs a resume-by-different-actor scenario and asserts both entries are visible/distinguishable) | UNVERIFIED |
| 2.18 | §24.3 Concurrent/conflicting decompositions → `CONFLICTING`, not auto-merged | §24.3 | `EvidenceClass.CONFLICTING` + `CONFLICTING_WITHOUT_DECISION_RECORD` (same mechanism as 2.14); no dedicated "two decompositions of the same source" concept, but the underlying enforcement (conflicting classification requires a decision record) is the same code path | `test_conflicting_without_decision_record_is_an_error` (same test as 2.14, not scenario-specific to §24.3) | PARTIAL — mechanically the same enforcement point serves both §23 and §24.3, which is defensible reuse, but no test scenario specifically frames it as "two agents produced different results for one unit," so the §24.3-specific angle is UNVERIFIED even though the underlying code is CONFORMANT for §23. |
| 2.19 | §24.4 No silent overwrites; corrections are new dated entries | §24.4 | Same append-only mechanism as 2.3/2.17 | `test_wiki.py::test_wiki_update_appends_change_history_and_adds_reference` | CONFORMANT for Wiki pages specifically; PARTIAL/UNVERIFIED generally (no test for WorkItem/DecisionRecord "correction" scenarios) |

---

## Part 3 — Anti-patterns, stop conditions, work item template (§§25–27)

| # | Requirement | Pack § | Implementation | Test(s) | Status |
|---|---|---|---|---|---|
| 3.1 | §25 16 named anti-pattern phrases, rejected regardless of source | §25 | `content_scan.ANTI_PATTERN_PHRASES` — **verified verbatim, all 16 phrases present and in the same order as the pack text** | `test_content_scan.py` | CONFORMANT |
| 3.2 | §26.1 13 numbered Stop Conditions — use BLOCKED rather than manufacturing an answer | §26.1 | `vocab.STOP_CONDITIONS: dict[int, str]` (new, R15) — the closed 13-entry lookup table, pack-literal text keyed by condition number, mirroring `MIN_CONFIDENCE_FOR_CLASS`'s dict style. `DecisionRecord.overrides_stop_condition: Optional[int]` range-checked 1–13 (`validate_decision_record`'s `INVALID_STOP_CONDITION_NUMBER`, pre-existing). `FinalReport.stop_conditions_triggered` entries now validated in `validate_final_report` (new check, runs unconditionally, not gated on `overall_status == BLOCKED`): each entry's `"condition"` key must be a key of `STOP_CONDITIONS`, else `INVALID_STOP_CONDITION_NUMBER` fires — same finding code as the pre-existing override check, since both are the same normative requirement (§26.1's closed set) applied at two different call sites. | `test_invalid_stop_condition_number_rejected` (pre-existing, override field), `test_stop_conditions_triggered_with_a_real_condition_number_is_not_flagged` (parametrized 1 and 13, boundary check), `test_stop_conditions_triggered_with_an_invalid_condition_number_is_rejected` (parametrized 0, 14, 99, `"3"` string, `None` — negative path per the governing rule), `test_stop_conditions_triggered_invalid_number_is_flagged_even_when_not_blocked` (proves the check isn't accidentally gated on BLOCKED status) | CONFORMANT (Recommendation R15, closed) — **Original audit claim**: the 13 conditions are not individually modeled, and `stop_conditions_triggered`'s free-form dicts let an operator record a nonexistent condition number with nothing to stop it. **Correction: True** (confirmed by direct inspection of `validation.py`'s BLOCKED-substantiation logic before any fix was written — no alternate/equivalent check existed anywhere else in the schema). **Resolution**: added `vocab.STOP_CONDITIONS` as the closed, shared lookup table (kept as a plain `dict[int, str]`, not a `_StrEnum`, since the 13 conditions are pack-numbered, not pack-named — matching the existing `overrides_stop_condition: int` field's own shape rather than introducing a parallel named-constant scheme); added one new validation check in `validate_final_report` reusing the existing `INVALID_STOP_CONDITION_NUMBER` finding code. No changes to `models.py` (data shape of `stop_conditions_triggered` is unchanged — still a free-form `list[dict[str, Any]]`, since the only genuine gap was the *values* going unchecked, not the *shape*), no changes to `cli.py`/`export.py`/`html.py`, per the standing architectural constraint that new cross-record validation belongs in `validation.py` only. |
| 3.3 | §26.2 Authorized Override Protocol — 4 mandatory elements (condition #, authorizing party, scope, residual risk) | §26.2 | `DecisionRecord.overrides_stop_condition/decided_by/override_scope/override_residual_risk`; `validate_decision_record`'s `OVERRIDE_WITHOUT_ATTRIBUTION`/`OVERRIDE_WITHOUT_SCOPE`/`OVERRIDE_WITHOUT_RESIDUAL_RISK` | `test_override_without_attribution_is_an_error`, `test_override_without_residual_risk_is_a_warning`, `test_valid_override_with_attribution_and_scope_is_clean` | CONFORMANT — all 4 elements are checked, though note the severity split: attribution is ERROR, scope/residual-risk are WARNING (a defensible reading of "MUST specify" vs. practical usability, but worth flagging: the pack's text treats all four as equally mandatory ("additionally specifies"), while the implementation treats only attribution as blocking). PARTIAL on severity-fidelity, CONFORMANT on presence-checking. |
| 3.4 | §26.2 "override never retroactively changes a classification" (component stays ABSENT/PLANNED even after override) | §26.2 | **Partially implemented (Phase 6 / R16): affected-unit linkage is now checked; causal classification-strengthening detection is a disclosed, genuinely unimplemented gap.** Investigation corrected an inaccuracy in this recommendation's original premise: `DecisionRecord.related_unit_ids`/`related_work_item_ids` already existed (from earlier Phase 5B work) and were already CLI-wired via `decision create --related-unit`/`--related-work-item` -- the earlier claim that "a way to name the affected unit... doesn't exist yet" was incorrect. What was genuinely missing: `validate_decision_record` never validated these fields at all. Now, when `overrides_stop_condition` is set, `OVERRIDE_WITHOUT_LINKED_UNIT` (WARNING) fires if neither `related_unit_ids` nor `related_work_item_ids` names anything -- an unlinked override is not auditable against any specific affected record, matching `OVERRIDE_WITHOUT_SCOPE`/`OVERRIDE_WITHOUT_RESIDUAL_RISK`'s existing severity tier for adjacent §26.2 completeness gaps. Separately, and unconditionally on whether the decision is an override at all (these are general-purpose fields), a dangling `related_unit_ids`/`related_work_item_ids` entry is now `RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND` (ERROR, only when the caller supplies the corresponding `{id: record}` mapping), mirroring `validate_final_report`'s existing `RELATED_DECISION_NOT_FOUND` pattern exactly. **Deliberately NOT implemented, and disclosed rather than silently decided**: detecting that a related unit's/work item's `implementation_status`/`evidence_class` was *strengthened because of* the override (§26.2's own worked example: overriding Stop Condition #2 does not make a component `IMPLEMENTED`). Neither `KnowledgeUnit.implementation_status`/`evidence_class` nor `WorkItem.evidence_class` carry any history/snapshot to compare a "before the override" value against (unlike `lifecycle_state`, which has `lifecycle_log`) -- inferring strengthening from the *current* value alone (e.g. flagging `overrides_stop_condition == 2` alongside a related unit currently `PRESENT`) was explicitly considered and rejected as an invented causal claim the data cannot support, the same class of shortcut already disclosed and rejected in `InventoryItem`'s docstring (Recommendation R4, row 1.14). | `validation.py` (`validate_decision_record`'s new `units`/`work_items` optional-mapping parameters, `OVERRIDE_WITHOUT_LINKED_UNIT`/`RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND`), `cli.py` (`_related_units`/`_related_work_items_for_decision` helpers wired into all four `decision create`/`resolve`/`show`/`validate` call sites); tests: 11 in `tests/test_validation.py` (unlinked-override warning, linked-via-unit clean, linked-via-work-item clean, non-override decision never flagged, dangling-unit-id skipped without mapping, dangling-unit-id flagged with empty mapping, resolving-unit-id clean, dangling-work-item-id skipped without mapping, dangling-work-item-id flagged with empty mapping, resolving-work-item-id clean, and a dedicated boundary test confirming a currently-`PRESENT`-classified related unit alongside an SC#2 override produces no strengthening finding of any kind) + 5 CLI round-trip tests in `tests/test_cli.py` (unlinked override flagged, linked-via-unit clean, dangling related-unit ID flagged end-to-end through `decision create` and `decision validate`, dangling related-work-item ID flagged, resolving related-work-item ID clean). Manual end-to-end smoke test additionally confirmed all three real-CLI paths (unlinked WARNING, linked-and-clean, dangling-ID ERROR) through real storage. | PARTIAL — deliberately not CONFORMANT: the affected-unit linkage/visibility requirement is fully implemented, tested, and enforced; the causal "strengthened beyond what the override substantiates" half of §26.2 remains a genuinely unimplemented, disclosed gap, since no classification history is persisted anywhere in this schema to make that comparison honestly. See Recommendation R16 and the Changelog. |
| 3.5 | §26.2 override must still appear in Final Report, never made invisible | §26.2 | `FinalReport.related_decision_ids` (new, additive field) names the Decision Records a report is accounting for; `validate_final_report`'s optional `decisions` parameter is a `{id: DecisionRecord}` mapping (mirrors `validate_wiki_references`' dict shape exactly, so the check can distinguish "not supplied" from "supplied but dangling") that cross-checks each related decision two ways: (1) the ID must resolve in the mapping (`RELATED_DECISION_NOT_FOUND`, ERROR, if not — the same rule already applied to WikiPage references), and (2) for every resolved decision whose `overrides_stop_condition` is set, that condition number must appear in `stop_conditions_triggered` (`OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT`, ERROR, if not — §26.2 states this with "MUST"). `cli.py`'s `report create` gained `--related-decision`; `report finalize/show/validate` all load and supply the related-decisions mapping via the new `_related_decisions` helper (mirrors `_load_blocking_decision`/`_impact_target_work_item_map`, but returns a dict, not a list, specifically so a dangling ID is detectable rather than silently dropped). `reporting.py` gained one display line for `related_decision_ids` alongside the existing `related_audit_ids`/`related_work_item_ids` lines (presentation only, no new logic). | 8 tests in `test_validation.py`: `test_final_report_omitting_a_related_overridden_stop_condition_is_flagged` (positive, asserts ERROR severity), `test_final_report_that_lists_the_overridden_condition_is_not_flagged` (boundary-negative: correctly-reported override is clean), `test_final_report_override_check_is_skipped_without_a_decisions_mapping` (no mapping supplied -> both checks skip, not a manufactured pass), `test_final_report_decision_without_an_override_is_not_flagged` (a related decision with no override never fires the override-visibility check), `test_final_report_flags_each_missing_override_independently` (two related overrides, only one omitted -> exactly one finding, naming the omitted condition number), `test_final_report_with_dangling_related_decision_id_is_flagged` (dangling ID -> `RELATED_DECISION_NOT_FOUND`, ERROR), `test_final_report_unrelated_decision_alongside_a_reflected_override_is_clean` (an unrelated, non-overriding related decision introduces no finding of its own), `test_final_report_unrelated_status_strengthening_alongside_override_remains_valid` (an overridden condition coexisting with an otherwise-valid, unrelated completion claim is not suppressed or masked); 3 tests in `test_cli.py`: `test_report_validate_flags_a_related_override_missing_from_stop_conditions` (full CLI round-trip: `decision create` -> `decision resolve` -> `report create --related-decision` -> `report validate`), `test_report_validate_flags_a_dangling_related_decision_id` (CLI round-trip for the dangling-ID case), `test_report_show_records_related_decision_ids` (field round-trip). Manual CLI smoke tests additionally confirmed both ERROR cases fire with exit code 1 and the positive path clears with exit code 0, through real storage end-to-end. | CONFORMANT — resolved by Recommendation R17. Investigation surfaced a genuine object-model gap (no existing `FinalReport` field could represent "the decisions, including resolved overrides, this report is accounting for" -- `open_decision_ids` means something different (still-OPEN, caps status) and `blocking_decision_id` is singular/BLOCKED-only) -- confirmed with the user before adding the new field, per the R3/R12 stop-and-reconcile precedent, rather than silently overloading an existing field. Both new checks are ERROR severity (not WARNING, as an earlier draft of this implementation had it): §26.2 states the visibility requirement with "MUST", and a dangling reference is the same class of defect `WIKI_REFERENCE_NOT_FOUND` already treats as ERROR elsewhere in this module — the user caught and corrected this severity mismatch, along with the list-vs-dict API gap that made the dangling-reference case undetectable in the first draft. Both checks only run when the caller supplies the `decisions` mapping explicitly -- consistent with every other optional cross-record check added in Phase 5B (R15/R19/R21), never fabricating a pass or fail when the information is simply not supplied. |
| 3.6 | §27 Standard Work Item — full template shape (Responsibility, Evidence Classification, Inputs/Outputs tables, Authority, Resources, Dependencies, State, Ownership, Pre/Postconditions, Invariants, Failure Modes, Persistence, Verification (14-gate table), Open Decisions, Provenance) | §27 | `models.WorkItem` now covers every named §27 template section; `reporting.render_work_item` renders it in the template's shape, including the new "### Persistence" section. What changed (R18): `WorkItem` gained four additive, free-text fields -- `durable_state`, `journal`, `recovery_behavior`, `indeterminate_states_reconciliation_path` -- matching §27's own four Persistence sub-fields (§27's literal labels: "Durable state:", "Journal:", "Recovery:", "Indeterminate states (EXECUTION-STATE, §14/§15):" -- Phase 5C re-audit correction: the implementation's field names/rendering labels are `recovery_behavior` / "Recovery behavior" and `indeterminate_states_reconciliation_path` / "Indeterminate states and reconciliation path", which are readable expansions of those two labels, not literal quotes -- the original "verbatim" claim overstated the match; see the re-audit Changelog entry), and mirroring the existing `required_authority`/`forbidden_authority`/`resource_budget` precedent exactly (plain `str`, no dedicated completeness check, no CLI wiring, since none of those free-text §27 sections have any either). `reporting.render_work_item` gained a matching "### Persistence" section. | `tests/test_work_item_persistence_fields.py` (6 tests: all four fields exist with correct type/default; plain-`str` type confirmed via dataclass introspection; round-trip through a real `Workspace` JSON save/load; `to_dict()` serialization; explicit negative-path guard proving no new `PERSISTENCE`/`JOURNAL`/`RECOVERY` validation finding was introduced; explicit static-source guard proving `validate_work_item` contains no reference to `INDETERMINATE`/`RECONCILED`, keeping R10's reconciliation-behavior scope untouched); `tests/test_reporting.py::test_render_work_item_includes_persistence_section` (new, confirms the section actually renders, not just exists as unrendered fields) | CONFORMANT (Recommendation R18, closed), with one adjacent, already-tracked gap intentionally left untouched — **Original claim**: two template sections had no field-level equivalent. Re-checking this claim during R18's investigation found the original text named only one of the two ("Persistence") explicitly; the second is row 1.20's already-disclosed §9.2 gap ("`WorkItem` has no sub-state field at all, only the canonical `lifecycle_state` directly, so there is nothing to check a mapping *of*" -- i.e. the template's own `### State` block, which asks a refined sub-state to declare its canonical mapping). **Correction: True** for the Persistence half (confirmed: before this fix, no `WorkItem` field corresponded to any of §27's four Persistence sub-fields); the State/refinement-mapping half remains correctly tracked at row 1.20 and is explicitly out of R18's scope (R18 addresses only the Persistence sub-fields named in its own recommendation text; the sub-state-refinement gap is a distinct, larger design question about whether to support refined sub-states at all, not a small additive field). **Resolution, with an explicit scope boundary preserved**: these are documentation-only narrative fields -- a field describing the journal/recovery situation is not itself a journal or recovery implementation. No `ExecutionState.INDETERMINATE`/`RECONCILED` reconciliation logic was added (that remains Recommendation R10's scope, Phase 6, deliberately untouched — verified by a dedicated static-source test), no append-only journal machinery was added (the template's own Journal sub-field is one narrative line, unlike the genuinely different, pre-existing, already-append-only `lifecycle_log`), and no new validation check was added (matching the pre-existing Authority/Resources precedent, confirmed by a dedicated negative-path test). |

---

## Part 4 — Verification model, prompts, coordination (§§28–38)

| # | Requirement | Pack § | Implementation | Test(s) | Status |
|---|---|---|---|---|---|
| 4.1 | §28 Repo Reality Audit prompt: `PRESENCE-CLASS`, never modify repo | §28 | `vocab.PresenceClass`; `RepoAudit.repository_modified` + `AUDIT_MODIFIED_REPOSITORY`; `audit scan-fs` CLI command performs a genuine read-only filesystem walk | `test_modified_repository_is_an_error`, `test_cli.py::test_repo_audit_scan_fs_does_not_modify_repo` (asserts, via filesystem hash/mtime comparison per session memory, that a real scan doesn't touch the repo) | CONFORMANT — this is the one "prompt" section (§§28–38 are literally titled "Prompt: ...", i.e. instructions for an *LLM agent*, not code) that has a genuine, tested, executable implementation (`scan-fs`) rather than just data modeling. |
| 4.2 | §29 Source Decomposition prompt — dependency graph + loss-detection report | §29 | `KnowledgeUnit.dependencies`/`forbidden_dependencies` fields exist; **no "loss-detection report"** (a check that every source requirement mapped to at least one output unit) exists anywhere | none | NON-CONFORMANT (gap) as a distinct feature, though defensible as out-of-scope: this pack section describes an LLM decomposition *behavior*, and this implementation only provides the data model the LLM would populate, not the decomposition process itself. Should be documented as intentionally out of scope rather than silently absent. |
| 4.3 | §30 Cleaning prompt | §30 | Not implemented — see 2.8 (§18), same reasoning | none | NOT-APPLICABLE (out of scope, same as §18) |
| 4.4 | §31 Work Planner prompt (PLAN/AUTHORIZATION/EXECUTION/OBSERVATION/VERIFICATION separation) | §31 | `vocab.WorkItemStage` (new, R19) — closed 5-value `_StrEnum` (`plan, authorization, execution, observation, verification`), disclosed as implementation-only vocabulary (§31's prompt text states these 5 names but they have no Appendix A entry, same disclosure category as `ClaimStatus`/`DecisionStatus`). `LifecycleLogEntry.stage: WorkItemStage` (type annotation updated; the field's existing lowercase spelling and every existing on-disk/call-site value preserved unchanged — no rename). `cli.py`'s five `item.log(...)` call sites now pass `WorkItemStage` members instead of bare literal strings. New `validate_work_item` check: every `lifecycle_log` entry's `stage` must be a member of `WorkItemStage`, else `INVALID_LIFECYCLE_LOG_STAGE` fires — mirrors the pattern already used for `WikiPage.page_number` (`validate_wiki_page_local`'s defensive `WikiPageNumber(...)` re-check). | `test_lifecycle_log_entry_with_a_real_stage_is_not_flagged` (parametrized, all 5 values, boundary-complete), `test_lifecycle_log_entry_with_an_invalid_stage_is_rejected` (parametrized: typo `"excecution"`, wrong-case `"Execution"`/`"EXECUTION"`, unrelated word `"cleanup"`, empty string, digit string, `None`), `test_lifecycle_log_entry_stage_accepts_the_enum_member_directly` (semantic: proves a `WorkItemStage` member itself — not just its string value — round-trips and validates cleanly), plus the pre-existing `test_verified_without_lifecycle_log_is_an_error`/`test_fully_valid_verified_work_item_has_no_errors` (unmodified, still pass — proves no regression to the literal-string membership check, since `WorkItemStage` is a `str` subclass and compares equal to its plain value) | CONFORMANT (Recommendation R19, closed) — **Original audit claim**: `LifecycleLogEntry.stage` being a bare `str` is a typo-safety gap; a capitalized or misspelled stage value would silently pass. **Correction: True** (confirmed directly: `WorkItem(...).lifecycle_log.append(LifecycleLogEntry(stage="Execution"))` produced zero findings before this fix). **Resolution**: added the closed `WorkItemStage` enum and one new `validation.py` check reusing the `WikiPageNumber`-style defensive-coercion pattern; kept the pre-existing lowercase spelling (the pack's own §31 prompt text is uppercase, but this vocabulary has no Appendix A entry to mandate a spelling, so there was no normative reason to rename every existing value) and left `storage.py`'s JSON-boundary loading of `lifecycle_log` entries unchanged (out of R19's stated scope — `models.py`/`validation.py`/`cli.py` only — and unnecessary regardless, since `WorkItemStage` values are plain strings that the new `validation.py` check catches at validation time however they arrived). |
| 4.5 | §32 Execution Observer prompt (EXPECTED/OBSERVED/INFERRED/UNKNOWN separation) | §32 | Not modeled as its own vocabulary — `CounterexampleRecord.expected_behavior`/`actual_behavior` covers the EXPECTED/OBSERVED half for failures only; there is no general-purpose "observation record" type for successful executions distinguishing EXPECTED from OBSERVED from INFERRED from UNKNOWN. | none | PARTIAL — again, this is an LLM-agent behavioral prompt; this implementation's closest analog is scoped narrowly to counterexamples. |
| 4.6 | §33 Verification Agent prompt — `VERIFICATION-RESULT` 8-value vocabulary; PASS requires evidence | §33 | `vocab.VerificationResult` (8 values, matches Appendix A.8 exactly including the `NOT-APPLICABLE`/`INAPPLICABLE` alias); `validate_work_item`'s `PASS_WITHOUT_EVIDENCE` | `test_pass_without_evidence_is_an_error` | CONFORMANT |
| 4.7 | §34 Knowledge Graph Builder — node/edge types, mandatory provenance, DERIVED marking, planned/observed subgraphs, `supersedes` on supersession | §34 | `graph.py` — `GraphNode`/`GraphEdge` require provenance at `add_node`/`add_edge` time (raises `GraphIntegrityError`, not silently accepted); `planned_subgraph()`/`observed_subgraph()`; `GraphEdgeType.SUPERSEDES`; `validate_knowledge_graph`'s `DERIVED_EDGE_WITHOUT_EXPLANATION`/`GRAPH_HAS_CONTRADICTIONS`/`GRAPH_HAS_PLANNED_NOT_OBSERVED` | `test_graph.py` (8 tests) + `test_validation.py::test_graph_*` (4 tests) | CONFORMANT — one of the best-covered sections. Minor gap: nothing actually *creates* a `supersedes` edge automatically when a node's underlying record transitions to `HISTORICAL` (same root gap as row 2.4) — the edge type exists and can be manually added, but there is no automatic linkage. |
| 4.8 | §35.1/§35.2/§35.3 Gates/Methods/Result as two orthogonal axes; every gate MUST get a result | §35 | `vocab.VerificationGate` (14 values, exact match to Appendix A.9), `VerificationMethod` (8 values, exact match to A.10), `VerificationResult` (8 values); `WorkItem.missing_gates()`; `validate_work_item`'s `VERIFICATION_GATES_INCOMPLETE` | `test_missing_gates_is_a_warning` | CONFORMANT. Note: `VERIFICATION_GATES_INCOMPLETE` is `WARNING`, not `ERROR` — the pack says a gate "MUST be assigned a result... MUST NOT be silently omitted," which reads as a hard requirement; treating omission as WARNING rather than ERROR is a defensible practical choice (an in-progress work item legitimately has ungated stages) but is a real severity-fidelity gap worth naming, not hiding. PARTIAL on severity; CONFORMANT on detection. |
| 4.9 | §35.3 `INAPPLICABLE`→`NOT-APPLICABLE` spelling unification (v1→v2 changelog item #4) | §35.3, Appendix C #4 | `vocab.INAPPLICABLE = VerificationResult.NOT_APPLICABLE` — alias, not a separate value | `test_v1_inapplicable_alias_matches_v2_not_applicable` (`tests/test_vocab.py`) | CONFORMANT. **Correction (Phase 5A/R20):** while preparing R20's supposedly-missing test, this test was found to already exist, predating this audit — the original row 4.9 was itself a false-negative audit finding (a grep that missed the right file/name, not an actual gap). No test was added; the row's status is corrected here rather than an unnecessary duplicate test being written. This is recorded as a caught self-error, consistent with the audit's discipline of re-verifying every claim rather than assuming a prior "no test found" grep was exhaustive. |
| 4.10 | §36 Change-Impact Analysis — 12 categories, all must be assessed, approval gate on unmitigated high risk | §36 | `models.CHANGE_IMPACT_CATEGORIES` (12, exact match to pack list); `validate_change_impact_analysis`'s `IMPACT_CATEGORIES_UNASSESSED`/`APPROVED_WITH_UNMITIGATED_RISK` | `test_unassessed_categories_is_an_error`, `test_approved_with_unmitigated_high_risk_is_an_error` | CONFORMANT |
| 4.11 | §36 "flag conflict before proceeding" when changed unit has open claims from other agents | §36 | `validate_change_impact_analysis` (new, R21) takes an optional `work_items: dict[str, WorkItem] | None` mapping, mirroring `validate_wiki_references`'s optional-mapping cross-record pattern — this function still never touches storage itself. When supplied and `target_unit_id` resolves to a `WorkItem` with `ownership.status == ACTIVE` and a different `ownership.owner` than `analysis.proposed_by`, `CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM` (WARNING) fires. `cli.py`'s `impact set/approve/show/validate` commands now load the target via a new `_impact_target_work_item_map` helper (same "load if present, tolerate absence" pattern as `_wiki_referenced_records`) and pass it through, so the check actually runs in real CLI usage, not just as a dormant library function. | `test_change_impact_target_with_active_claim_by_another_agent_is_flagged` (positive), `test_change_impact_target_claimed_by_the_same_proposer_is_not_a_conflict` (same agent continuing its own work is not a conflict), `test_change_impact_target_with_released_claim_is_not_a_conflict` (only `ACTIVE` counts as an open claim, not `RELEASED`/`EXPIRED`), `test_change_impact_conflict_check_is_skipped_without_a_work_items_mapping` and `test_change_impact_conflict_check_is_skipped_when_target_is_not_in_the_mapping` (both negative: absence of a mapping, or an unresolved target within a supplied mapping, must not silently assert "no conflict" as if checked) | CONFORMANT (Recommendation R21, closed) — **Original audit claim**: `ChangeImpactAnalysis` has zero enforcement of §36's flag-the-conflict rule. **Correction: True** (confirmed directly: `validate_change_impact_analysis` had no `work_items` parameter or ownership-aware logic of any kind before this fix). **Resolution, with a disclosed scope limit**: §24.1 ("Ownership / Claiming") defines open claims only via `WorkItem.ownership` — `KnowledgeUnit` has no ownership field at all in this implementation — so this check can only ever fire when `target_unit_id` resolves to a `WorkItem`. A Change-Impact Analysis targeting a Knowledge Unit has no ownership state to conflict with in this schema; this is recorded here as a real, disclosed scope limit (same shape as R11's `DecisionRecord`-only narrowing), not silently treated as full §36 coverage for every possible target type. Implementation kept to `validation.py` (the new parameter and check) plus a small, additive `cli.py` wiring helper — no changes to `models.py`, `export.py`, or `html.py`. |
| 4.12 | §37 Counterexample Minimizer prompt | §37 | Same as §22.4 (row 2.13) — the minimizer prompt's substance is the minimization checklist, already implemented | `test_minimization_requires_full_checklist` | CONFORMANT (via §22.4's implementation) |
| 4.13 | §38 Wiki Generator — 18-page closed index; never allow planned to appear as implemented | §38 | `vocab.WikiPageNumber` (18-value closed enum); `models.WikiPage` with **no** classification/implementation-status/evidence-status fields (architecturally prevents the anti-pattern by construction, not just by check); `validation.derive_wiki_header` computes these live at render/export time | `test_wiki.py` (48 tests — the single most thoroughly tested pack section in the whole codebase), `test_export.py::test_export_plan_header_is_derived_live_not_cached` | CONFORMANT — this is the strongest section in the entire audit: the anti-pattern is prevented structurally (there is no field to go stale), not merely detected after the fact. |

---

## Part 5 — Completion, master prompt, principle (§§39–43)

| # | Requirement | Pack § | Implementation | Test(s) | Status |
|---|---|---|---|---|---|
| 5.1 | §39 Completion Contract — 9-item AND chain; no claim/action/effect/verification/decision without its precondition | §39 | `FinalReport.completion_checklist` (10 keys — see note below); `validate_final_report`'s `INCOMPLETE_COMPLETION_CHECKLIST`; `derive_overall_status_ceiling` | `test_complete_without_full_checklist_is_an_error`, `test_complete_with_full_checklist_is_clean`, plus the full ceiling-derivation matrix (`test_ceiling_is_*`, 6 tests) | CONFORMANT. Note: the pack's §39 prose lists 9 AND-conditions but this implementation's `completion_checklist` has exactly the same 9 plus none extra — confirmed by direct comparison: `scope_known, source_identified, repository_state_identified, work_performed, observed_result_captured, invariants_checked, evidence_recorded, failures_classified, open_ambiguities_recorded, final_status_assigned` — **that's 10, not 9.** The pack's §39 list is: "Scope known AND Source identified AND Repository state identified AND Work performed AND Observed result captured AND Required invariants checked AND Evidence recorded AND Failures classified AND Open ambiguities recorded AND Final status assigned" — counting conjuncts: that actually is 10 items (Scope, Source, Repository state, Work performed, Observed result, Invariants checked, Evidence recorded, Failures classified, Open ambiguities, Final status). Recount: **10 conjuncts in the pack text itself**, matching the implementation exactly. (This audit's own initial count of "9" was wrong on first read — corrected here per this pack's own discipline of verifying rather than asserting from memory.) |
| 5.2 | §39 "No evidence → no claim; no execution → no execution claim; no verification → no conformance claim; no decision → no resolved-status claim" | §39 | `STATUS_MASQUERADING` (claim-vs-ceiling check); `UNJUSTIFIED_BLOCKED_STATUS` (BLOCKED claim needs substantiation); `RESOLVED_WITHOUT_ATTRIBUTION`/`RESOLVED_WITHOUT_CHOICE` (decision claim needs substantiation) | Full negative-path matrix: `test_status_masquerading_negative_path_matrix`, `test_blocked_negative_path_matrix` | CONFORMANT — this is the pack's central discipline and it is the most heavily tested behavior in the codebase (82 tests in `test_validation.py` alone touch this family). |
| 5.3 | §40 Final Report Format — exact section list, `COMPLETE/PARTIAL/BLOCKED` literal vocabulary | §40 | `reporting.render_final_report` renders all named sections; `vocab.to_pack_overall_status_label` collapses the internal 4-value model back to the pack's literal 3 values for the rendered artifact | `test_to_pack_overall_status_label_collapses_to_three_pack_values` | CONFORMANT — and the internal/external vocabulary split (4 values reasoned with, 3 values rendered) is explicitly documented as a deliberate, disclosed deviation, not a silent one; this is exactly the kind of decision the pack's own §18 Cleaning Contract would want surfaced ("every semantic change requires a change record") — and it is, in the `OverallStatus` docstring itself. |
| 5.4 | §41 Master Arena Agent Prompt (non-normative summary) | §41 | N/A — this is a prompt for an LLM agent's own behavior, not a data contract; §0.4 explicitly says detailed sections govern over this summary | — | NOT-APPLICABLE by the pack's own declared precedence rule |
| 5.5 | §42 Knowledge Lifecycle Pipeline View (diagram) | §42 | See row 1.2 — not separately modeled as data | — | NOT-APPLICABLE as enforceable rule |
| 5.6 | §43 Core Arena Principle — 10 "NO X WITHOUT Y" checks, explicitly non-normative/advisory | §43 | `models.CORE_ARENA_PRINCIPLE_CHECKS` (exactly 10, matches pack text including the 2 new-in-v2 items); `FinalReport.core_principle_checklist`; explicitly documented as advisory, does not gate `overall_status` | `test_core_arena_principle_checklist_defaults_to_all_false_and_is_advisory` | CONFORMANT — correctly implements the checklist as real per-item data while correctly *not* using it as a blocking gate, matching the pack's own explicit statement that §43 is non-normative. This is a case where "implementing it as advisory" is itself the correct, conformant behavior, not a shortfall. |

---

## Part 6 — Appendix A vocabularies (exhaustive cross-check)

Every one of the pack's 17 Appendix A vocabularies was compared value-by-value
against its `vocab.py` counterpart. All 17 exist and all 17 match exactly
(including ordering, spelling, and hyphen-vs-underscore conventions
translated consistently):

| Vocabulary | Appendix | `vocab.py` class | Value count match | Status |
|---|---|---|---|---|
| `EVIDENCE-CLASS` | A.1 | `EvidenceClass` | 12/12 | CONFORMANT |
| `EXTRACTION-CLASS` | A.2 | `ExtractionClass` | 14/14 | CONFORMANT |
| `EXECUTION-STATE` | A.3 | `ExecutionState` | 7/7 | CONFORMANT |
| `EVIDENCE-STATE` | A.4 | `EvidenceState` | 4/4 | CONFORMANT |
| `AUTHORIZATION-STATE` | A.5 | `AuthorizationState` | 7/7 | CONFORMANT |
| `DIVERGENCE-CLASS` | A.6 | `DivergenceClass` | 7/7 | CONFORMANT |
| `LIFECYCLE-STATE` | A.7 | `LifecycleState` | 8 happy + 7 failure = 15/15 | CONFORMANT |
| `VERIFICATION-RESULT` | A.8 | `VerificationResult` | 8/8 (+ `INAPPLICABLE` alias) | CONFORMANT |
| `VERIFICATION-GATE` | A.9 | `VerificationGate` | 14/14 | CONFORMANT |
| `VERIFICATION-METHOD` | A.10 | `VerificationMethod` | 8/8 | CONFORMANT |
| `PRESENCE-CLASS` | A.11 | `PresenceClass` | 5/5 | CONFORMANT |
| `IMPACT-CLASS` | A.12 | `ImpactClass` | 8/8 | CONFORMANT |
| `CONFIDENCE` | A.13 | `Confidence` | 4/4 | CONFORMANT |
| `COVERAGE` | A.14 | `Coverage` | 2/2 (`SAMPLED(<method>)` modeled as `Coverage.SAMPLED` + free-text `coverage_method`, a reasonable structural translation) | CONFORMANT |
| Counterexample stages | A.15 | `CounterexampleStage` | 4/4 | CONFORMANT |
| Knowledge Graph node types | A.16 | `GraphNodeType` | 17/17 | CONFORMANT |
| Knowledge Graph edge types | A.17 | `GraphEdgeType` | 17/17 | CONFORMANT |

All 17 are backed by `test_vocab.py`'s enumeration tests (5 tests covering
value-set completeness) plus per-vocabulary usage tests scattered through
`test_validation.py`/`test_wiki.py`/`test_graph.py`. **This is the strongest
category in the whole audit: zero vocabulary drift found.**

---

## Part 7 — Implementation-only vocabulary (not in Appendix A) — checked for honest disclosure

The pack's Appendix A is described as consolidating "every enum used
anywhere in this pack." Three vocabularies exist in `vocab.py` that are
**not** in Appendix A. Per this pack's own §18 Cleaning Contract
("every semantic change requires a change record") and §2 Core Contract
("never collapse categories"), the question is not whether these exist —
they're a reasonable implementation choice — but whether their
non-pack-status is honestly disclosed:

| Vocabulary | Disclosed as non-pack? | Where | Status |
|---|---|---|---|
| `ResolutionStatus` (OPEN/FIXED/WONT-FIX/DUPLICATE/SPECIFICATION-CLARIFIED) | Yes | Docstring explicitly states "NOT part of the pack's own controlled vocabulary... appears only in arena-counterexample-template.md... as free labels" | CONFORMANT (honest disclosure) |
| `OverallStatus` (4-value COMPLETE/COMPLETE-WITH-WARNINGS/BLOCKED/INCOMPLETE vs. pack's literal 3-value COMPLETE/PARTIAL/BLOCKED) | Yes | Docstring explicitly explains the collapse-avoidance rationale and points to `to_pack_overall_status_label` for pack-literal rendering | CONFORMANT (honest disclosure) — this is the single most load-bearing "intentional deviation" in the codebase and it is also the most carefully documented one. |
| `ClaimStatus` (ACTIVE/EXPIRED/RELEASED) | **Yes, as of Phase 5A/R22** | Docstring rewritten to explicitly state: "Implementation-only vocabulary... there is no `CLAIM-STATUS` entry in Appendix A... referenced informally... to mean 'introduced to satisfy behavior new in v2 §24.1', not 'defined by v2 §24.1 as a vocabulary.'" Confirmed by `test_claim_status_and_decision_status_disclose_non_pack_provenance` (`tests/test_vocab.py`). | CONFORMANT (upgraded from PARTIAL) — R22 closed. Previously the docstring said "v2 §24.1 (new in v2)" in a way that implied pack provenance it didn't fully have; now explicitly disclosed as this implementation's own narrow encoding of §24.1's prose, not a pack-defined enum. |
| `DecisionStatus` (OPEN/RESOLVED/SUPERSEDED) | **Yes, as of Phase 5A/R22** | Docstring rewritten analogously: "Implementation-only vocabulary... §23/§25 (v1 §24) imply this status set through usage... rather than stating it as an enumerated vocabulary, and there is no `DECISION-STATUS` entry in Appendix A." Confirmed by the same `test_claim_status_and_decision_status_disclose_non_pack_provenance` test. | CONFORMANT (upgraded from PARTIAL) — R22 closed, same disposition as `ClaimStatus`. |

---

## Part 8 — Cross-cutting checks requested by the user (mapped to this matrix)

| User's audit question | Answer | Evidence (this matrix's rows) |
|---|---|---|
| 1. Does every normative requirement have an implementation home? | **Mostly no, with two closed by Phase 5B and one reclassified by Phase 5C.** §11 (Authority Contract derivation/attenuation) and most of §15's INDETERMINATE→RECONCILED state machine still have no implementation home at all. §36's cross-record claim-conflict check (R21) and §26.2's override-visibility-in-Final-Report check (R17) are now implemented, closing two of the four items originally listed here. §13 (External Effect pipeline) still has no pipeline/invariant implementation -- deliberately, since this package never invokes an external effect -- but that scope decision is now disclosed in code rather than silently undocumented (R8), moving it from NON-CONFORMANT-by-omission to NOT-APPLICABLE-by-disclosed-scope. | Rows 1.25, 2.2, 4.11 (closed), 3.5 (closed), 1.27 (reclassified) |
| 2. Is every implementation behavior actually supported by the pack? | **Yes, with disclosed exceptions.** No behavior was found asserting pack conformance it doesn't have; the 4 implementation-only vocabularies (Part 7) are disclosed as such (2 fully, 2 partially). | Part 7 |
| 3. Are there vocabulary mismatches? | **No exact mismatches found** — all 17 Appendix A vocabularies match exactly (Part 6). Minor *provenance-labeling* looseness on 2 non-pack vocabularies (R22). | Part 6, Part 7 |
| 4. Are there places where implementation semantics accidentally exceed the specification? | **One clear case:** `OverallStatus`'s 4-value model exceeds the pack's literal 3-value §40 vocabulary — but this is disclosed, deliberate, and reversible at render time (`to_pack_overall_status_label`), not an accidental drift. No *accidental* over-specification was found elsewhere. | 5.3, Part 7 |
| 5. Are any planned/derived/presentational concepts being represented as authoritative state? | **No** — this was checked specifically for `WikiPage` (header fields deliberately absent, always derived — row 4.13), `ExportPlan`/`html.py` (frozen Phase 3/4 invariants, re-confirmed structurally sound in this audit's import-graph check), and found clean throughout. This is the codebase's strongest property. | 1.28 (structural check), 4.13 |
| 6. Are lifecycle, evidence, provenance, validation, blocking, and completion semantics consistently enforced? | **Mostly yes, with named gaps:** lifecycle (strong), evidence (strong), provenance (shape-checked but not content-checked — 1.13), validation (strong — never duplicated outside `validation.py`, confirmed by import-graph check), blocking (strong), completion (strong). The weakest link is **execution-state's INDETERMINATE/RECONCILED machinery (2.2)**, which is vocabulary-only. | Rows throughout; weakest: 2.2 |
| 7. Do CLI, JSON, Markdown, export, and HTML projections preserve the same source of truth? | **Yes — this was the specific subject of Phases 3–4 and is the most rigorously tested property in the whole codebase** (`ExportPlan`'s no-semantic-authority contract, `write_export_plan`/`write_html_export`'s pure-materialization tests, the plan-mutation tests in both `test_export.py` and `test_html.py`). No divergence found. | 1.28, Phase 3/4 (see session history) |
| 8. Are all closed vocabularies and schemas actually closed? | **Yes for enums** (Python `Enum` subclassing raises `ValueError` on an invalid value by construction — confirmed for all 17 Appendix A vocabularies). **Mostly yes for the structural "closures" too, as of Phase 5B (now complete)**: `FinalReport.stop_conditions_triggered` remains a free `list[dict[str, Any]]` in shape, but its condition numbers are now validated against the closed 13-entry `vocab.STOP_CONDITIONS` table (row 3.2, CONFORMANT); `LifecycleLogEntry.stage` is now typed `WorkItemStage` and validated against that closed 5-value set (row 4.4, CONFORMANT). Still open: `WorkItem.resource_budget` (free dict, 1.23), `DecisionRecord`'s `conflicting_statements`/`options` (free dicts/lists). | Rows 1.23, 3.2 (closed), 4.4 (closed) |
| 9. Are negative paths machine-checkable? | **Yes, extensively** — `test_status_masquerading_negative_path_matrix` (8 combinations) and `test_blocked_negative_path_matrix` are explicitly parametrized negative-path matrices; most `validate_*` functions have at least one dedicated "this should fail" test. §24.1's conflicting-claim rejection (2.15) was the one significant exception at original-audit time; it was closed in Phase 5A by `test_work_claim_rejects_second_owner_while_active` (see row 2.15, now CONFORMANT). §36's change-impact/claim-conflict check (4.11, R21) and §26.2's override-visibility check (3.5, R17) were both closed in Phase 5B with dedicated positive/negative/boundary test coverage. Remaining weak spot: §24.1 claim *expiry* (2.16, R14, deferred to Phase 6). | 2.15, 4.11, 3.5 closed; 2.16 remains open |
| 10. Are there remaining silent ambiguity / status masquerading / semantic drift / information-loss paths? | **Three of the original four are now closed; one remains open, deferred to Phase 6.** (a) §26.2 override not preventing a simultaneous, uncorrelated `implementation_status` change on the same unit (3.4) remains open — this is Recommendation R16, Class 3 (new semantic subsystem), deliberately out of Phase 5B's scope. (b) A Final Report omitting a real, triggered-and-overridden Stop Condition with no finding (3.5) — **closed by R17** (`OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT`). (c) `LifecycleLogEntry.stage` being a bare string (4.4) — **closed by R19**. (d) `resource_budget`'s conservation check only firing when the dict happens to be populated with the right keys (1.23) remains open, deferred to Phase 6 planning. | 3.4 and 1.23 remain open; 3.5 and 4.4 closed in Phase 5B |

---

## Summary tally

| Status | Count |
|---|---|
| CONFORMANT | 44 |
| PARTIAL | 16 |
| NON-CONFORMANT | 1 |
| UNVERIFIED | 1 |
| NOT-APPLICABLE | 10 |
| **Total rows** | **72** |

(Counts are machine-recounted directly from Parts 1–5's individually
numbered rows by parsing this document's own tables — not hand-tallied —
to avoid this audit repeating the exact "claim without verification"
failure mode it exists to check for. Parts 6–8 are cross-check/summary
tables layered on top of the same evidence rather than independent new
rows, and are excluded from this count to avoid double-counting. This
table reflects the state **after Phase 5A, Phase 5B (R3 + R15 + R19 +
R21 + R17), Phase 5C (R8 + R4 + R18 + R2), and Phase 6 (R14 + R10 + R16
+ R7 + R1)** — the full roadmap through Phase 6's close — and the test
suite is 460/460. This section previously went stale after Phase 5B
(still showing 42/13/8/1/8, the pre-Phase-5C/6 figures) while the
Baseline record header and Changelog below it were correctly updated;
that staleness was found and corrected during the Final Pack Conformance
Review as a documentation-consistency defect, not a re-count of any row's
actual status — no row's disposition changed as part of this fix.
History, each figure independently re-derived from the file rather than
carried forward as prose: pre-Phase-5A baseline 33/16/9/6/8; post-R13
34/15/9/6/8 (the "34/16/9/5/8" stated in an earlier turn's prose was a
transcription error, corrected in the Baseline record's Self-correction
note above); post-R9 35/14/9/6/8; post-Phase-5A-batch (final)
39/15/9/1/8. The batch moved rows 1.15 (R5), 1.19 (R6), 2.5 (R12), and 4.9
(R20, corrected rather than newly tested) to CONFORMANT, and row 2.4 (R11)
from UNVERIFIED to PARTIAL — R11's narrower `DecisionRecord`-only scope is
now test-confirmed, but the row's separately-flagged general-case
NON-CONFORMANT-adjacent gap (§15.1 for Work Items/Knowledge Units) remains
open, which is why 2.4 landed on PARTIAL rather than CONFORMANT.
Post-Phase-5B-R3+R15 40/14/9/1/8 — R3 moved row 1.11 to CONFORMANT and R15
moved row 3.2 to CONFORMANT. Post-Phase-5B-R3+R15+R19 41/13/9/1/8 — R19
additionally moved row 4.4 to CONFORMANT. Post-Phase-5B-R3+R15+R19+R21
42/13/8/1/8 — R21 additionally moved row 4.11 to CONFORMANT
(NON-CONFORMANT count therefore dropped from 9 to 8), each independently
re-verified by the machine recount above (0 unparsed rows each time).
This was the state at the close of Phase 5B; it is **not current**. The
roadmap continued through Phase 5C (R8, R4, R18, R2) and Phase 6 (R14,
R10, R16, R7, R1), each independently moving further rows to CONFORMANT
or PARTIAL and each re-verified by the same machine-recount method at the
time — see the Changelog entries for R8/R4/R18/R2/R14/R10/R16/R7/R1 below
for the row-by-row detail. The **current** figure, matching the Baseline
record header above and freshly re-derived from this file's own 72 rows
during the Final Pack Conformance Review, is **44/16/1/1/10 = 72**
(460/460 tests). This paragraph's history up to Post-Phase-5B-R3+R15+R19+R21
is preserved verbatim as a historical record and must not be read as the
current tally — the table and header above are authoritative.)


**Headline finding:** the implementation is strongest exactly where the
prior four phases focused deliberate effort — Wiki/export/HTML
(structural anti-staleness), the Counterexample object, the Completion
Contract / status-masquerading machinery, and the closed-vocabulary
layer — all CONFORMANT with real negative-path tests. It is weakest in
the sections that received the least direct phase-level attention because
they were never the subject of a dedicated phase: the Authority Contract
(§11, essentially unimplemented), the External Effect Contract (§13,
out of scope but undocumented as such), the INDETERMINATE/RECONCILED
execution-state machine (§15, vocabulary-only), and several
cross-record consistency checks implied but not enforced (§24.1's
actual claim-conflict rejection untested; §26.2's override/classification
independence unenforced; §36's claim-conflict check absent).

None of the NON-CONFORMANT findings are **regressions** — nothing here
contradicts a previously-frozen phase's tested invariants (Phases 1–4 are
re-confirmed intact by this audit, see rows 1.28/4.13/Q7). They are
**gaps**: pack requirements that were never brought into scope by any
prior phase, now named explicitly for the first time.

---

## Recommendations — triaged into three work classes, sequenced as a controlled roadmap

Per adopted direction, these 22 items are **not** to be implemented
wholesale. They are triaged into three classes that must not be mixed
within a single change: (1) evidence/test hardening — no semantic change;
(2) small normative enforcement gaps — preserves the existing
architecture; (3) new semantic subsystems — deserve their own explicit
design phase. See the roadmap and Changelog above for execution order and
status. Sizes are rough, and "Status" tracks whether the item has been
acted on (only R13 has, so far).

### Class 1 — Evidence/test hardening (Phase 5A; safest, no semantic change)

| ID | Recommendation | Addresses row(s) | Rough size | Status |
|---|---|---|---|---|
| R13 | Add a CLI-level test: a second `work claim` on an already-`ACTIVE` item is rejected with the current owner named in the error. | 2.15 | Tiny (test-only) | **DONE** — see Changelog. `test_work_claim_rejects_second_owner_while_active` added to `tests/test_cli.py`; row 2.15 now CONFORMANT; 242/242 passing. |
| R9 | Add a project-wide static import-direction test (generalize `test_html.py`'s AST-import-scan approach to all of `arena_agent/*.py`) asserting §14's dependency direction holds, so a future change can't silently reverse it. | 1.28 | Small (test-only, pattern already exists) | **DONE** — see Changelog. `tests/test_architecture.py` (4 tests) added; row 1.28 now CONFORMANT; 246/246 passing. |
| R5 | Add a dedicated test for the `UNKNOWN_IDENTITY_NO_REASON` finding (§6.2 repository-identity fallback). | 1.15 | Tiny | **DONE** — see Changelog. 2 tests added to `tests/test_validation.py`; row 1.15 now CONFORMANT. |
| R6 | Add a dedicated test asserting `test_lifecycle_failure_branches_match_pack_text_exactly`-style coverage extends to every documented failure-branch *transition* (not just the branch set). | 1.19 | Tiny | **DONE** — see Changelog. 56 parametrized cases added to `tests/test_validation.py` (7 legal-pairing + 49 wrong-source-rejected); row 1.19 now CONFORMANT. |
| R11 | Add a dedicated supersession test (`HISTORICAL` evidence class not silently treated as current). | 2.4 | Tiny | **DONE** (narrow `DecisionRecord.status==SUPERSEDED` scope only, per explicit reconciliation with the user — see Changelog). 3 tests added; row 2.4 upgraded UNVERIFIED→PARTIAL. The broader general-case (§15.1 Work-Item/Knowledge-Unit `HISTORICAL` transition) gap remains open and unnumbered. |
| R12 | Add a test asserting `Provenance`'s exact field shape matches §16's literal 11-field list (not just "has some fields"). | 2.5 | Tiny | **DONE, but scope changed** — see Changelog. The premise was wrong: §16 actually lists 13 fields, and `_default_provenance()` was genuinely missing `classification` (a real gap, not just an untested claim). Added the field (additive, default `None`) plus 2 tests; row 2.5 now CONFORMANT. Confirmed with user before implementing. |
| R20 | Add a test asserting the v1 `INAPPLICABLE` alias round-trips to v2 `NOT-APPLICABLE` correctly wherever it's accepted. | 4.9 | Tiny | **MOOT — already existed.** `test_v1_inapplicable_alias_matches_v2_not_applicable` in `tests/test_vocab.py` predates this audit; the original row 4.9 "no test found" claim was itself a false negative. No new test written; row 4.9 corrected to CONFORMANT. |
| R22 | Document (in code comments/docstrings, not necessarily a new test) that `ResolutionStatus`/`OverallStatus`/`ClaimStatus`/`DecisionStatus` are implementation-only vocabularies, tightening the 2 partially-mislabeled cases (`ClaimStatus`/`DecisionStatus`) found in Part 7. | Part 7 | Tiny | **DONE** — see Changelog. `ClaimStatus`/`DecisionStatus` docstrings rewritten in `vocab.py`; 1 test added asserting the disclosure text is present. Part 7's two PARTIAL rows now CONFORMANT. |

### Class 2 — Small normative enforcement gaps (Phase 5B; preserves existing architecture)

| ID | Recommendation | Addresses row(s) | Rough size | Status |
|---|---|---|---|---|
| R3 | Extend `MIN_CONFIDENCE_FOR_CLASS` to cover `DERIVED`/`ARCHITECTURAL-PROPOSAL` → minimum `LOW` (reject `NONE`), matching §5.1's table exactly. | 1.11 | Tiny | **Done** — `vocab.py` dict extended, 6 new tests (`test_derived_or_architectural_proposal_with_none_confidence_is_an_error`, `test_derived_or_architectural_proposal_with_low_confidence_is_clean`, `test_unknown_or_example_with_none_confidence_is_never_flagged`), row 1.11 now CONFORMANT |
| R15 | Model the 13 Stop Conditions as a closed enum/lookup table (number → pack description) and validate `stop_conditions_triggered` entries' condition numbers against it, mirroring what `overrides_stop_condition` already does. | 3.2 | Medium | **Done** — `vocab.STOP_CONDITIONS` dict added, new check in `validate_final_report` (reuses `INVALID_STOP_CONDITION_NUMBER`), 3 new test functions / 8 parametrized cases (2 boundary-positive, 5 negative, 1 not-gated-on-BLOCKED), row 3.2 now CONFORMANT |
| R17 | Add a check (ERROR-level finding, per §26.2's "MUST") when a `FinalReport`'s related decisions include an `overrides_stop_condition` but that condition number is absent from `stop_conditions_triggered`, plus a dangling-reference check on `related_decision_ids` itself. | 3.5 | Small (grew to Medium once the `related_decision_ids` model gap was found) | **Done** — new additive `FinalReport.related_decision_ids` field (confirmed with user before adding, per R3/R12 stop-and-reconcile precedent); `validate_final_report` gained an optional `decisions: dict[str, DecisionRecord]` parameter and two new checks, `RELATED_DECISION_NOT_FOUND` and `OVERRIDE_NOT_REFLECTED_IN_FINAL_REPORT` (both ERROR — corrected from an initial WARNING-severity, list-typed draft after user review caught both the severity mismatch and the dangling-reference blind spot); `cli.py`'s `report create/finalize/show/validate` wired to actually supply it; `reporting.py` gained one display line; 11 new tests (8 validation + 3 CLI); row 3.5 now CONFORMANT |
| R19 | Change `LifecycleLogEntry.stage` from `str` to a closed enum (`plan/authorization/execution/observation/verification`). | 4.4 | Small (touches `models.py`, `validation.py`, `cli.py` call sites) | **Done** — `vocab.WorkItemStage` enum added, `LifecycleLogEntry.stage` type annotation updated (values unchanged), `cli.py` call sites now pass enum members, new `INVALID_LIFECYCLE_LOG_STAGE` check in `validate_work_item`, 13 new tests (5 positive parametrized, 7 negative parametrized, 1 semantic), row 4.4 now CONFORMANT |
| R21 | Add a check in `validate_change_impact_analysis`: if `target_unit_id` resolves (when the caller supplies a work-item map, mirroring `validate_wiki_references`'s optional-mapping pattern) to a `WorkItem` with `ownership.status == ACTIVE` and a different owner than `proposed_by`, flag it. | 4.11 | Medium | **Done** — `validate_change_impact_analysis` gained an optional `work_items` mapping and a new `CHANGE_IMPACT_TARGET_HAS_OPEN_CLAIM` check; `cli.py`'s `impact set/approve/show/validate` wired to actually supply it; 5 new tests (1 positive, 4 negative/boundary); row 4.11 now CONFORMANT (with a disclosed WorkItem-only scope limit — no ownership concept exists on KnowledgeUnit) |

### Class 2, continued — small never-sequenced items (Phase 5C; locked order R8 → R4 → R18 → R2)

These four were always Class 2 in size and character (small, additive,
preserves existing architecture) but were left unsequenced after the
original audit. Per explicit user direction, they now form their own
short phase, run in this locked order, immediately after Phase 5B's
freeze and before Phase 6's larger semantic-subsystem work begins.

| ID | Recommendation | Addresses row(s) | Rough size | Status |
|---|---|---|---|---|
| R8 | Document §13 out-of-scope rather than build an unneeded External Effect subsystem. | 1.27 | Tiny (documentation only) | **Done** — `arena_agent`'s package docstring gained a "Scope: no External Effect Contract (v2 §13)" section; `WorkItem`'s docstring now points to it; `README.md`'s "Design choices worth knowing about" carries the same disclosure. No behavior/data-shape change — nothing in this package invokes an external effect, so there is no pipeline object or durability-boundary check to add. 2 new tests in `tests/test_scope_disclosures.py` assert the disclosure text is present (mirrors R22's pattern), sensitivity-checked by confirming they fail against a mutated docstring missing the disclosure. Row 1.27 now NOT-APPLICABLE-by-disclosed-scope. |
| R4 | Add an evidence-quality check: a `SAMPLED` inventory item's `PRESENT` classification must be backed by item-specific evidence, not a generic/blanket sampling note. | 1.14 | Small | **Done, but scope changed** — see Changelog. Investigation found the premise unimplementable without manufacturing a false-confidence heuristic: whether an item was "actually inspected" is a real-world fact no validator over persisted strings can establish, the same "necessary, not sufficient" boundary as row 1.13. Confirmed with the user before implementing (per the R3/R12/R17 stop-and-reconcile precedent). Resolution: documented the permanent verification boundary in `InventoryItem`'s docstring and a `validate_repo_audit` comment, rather than adding a proxy check; 1 new test asserts the disclosure. Row 1.14 remains PARTIAL (deliberately not reclassified to NOT-APPLICABLE, since §6.1 is a live, partially-enforced requirement, unlike R8's §13). |
| R18 | Add explicit Persistence/Journal/Recovery fields to `WorkItem`, matching §27's template sub-fields under "Persistence." | 3.6 | Small | **Done** — see Changelog. Four additive free-text fields (`durable_state`, `journal`, `recovery_behavior`, `indeterminate_states_reconciliation_path`), matching §27's own sub-fields verbatim and the existing Authority/Resources precedent (no completeness check, no CLI wiring); `reporting.render_work_item` gained a matching "### Persistence" section; 6 new tests in `tests/test_work_item_persistence_fields.py` plus 1 in `test_reporting.py`, including explicit negative-path guards proving no new validation check was added and no `ExecutionState.INDETERMINATE`/`RECONCILED` reconciliation logic leaked in from R10's scope. Row 3.6 stays CONFORMANT, now with every §27 template section field-mapped. |
| R2 | Wire `scan_text` (Ingested Content Contract, §4.1) output into `FinalReport` so a flagged anomaly is actually reported, not left to manual operator attachment. | 1.8 | Small | **Done** — see Changelog. Additive `FinalReport.content_scan_anomalies: list[dict[str, str]]` field (`kind`/`matched_text`/`context`, no `start`/`end`); explicit-only `cli.py scan-content --attach-to-report <report-id>` wiring (plain `scan-content` never mutates a report); one shape-only `validation.py` check (`MALFORMED_CONTENT_SCAN_ANOMALY`, WARNING) with no coverage claim; "## Content Scan Anomalies" rendering section. 14 new tests in `tests/test_content_scan_final_report.py`. Row 1.8 moves PARTIAL → CONFORMANT. |

### Class 3 — New semantic subsystems (Phase 6; each deserves its own design phase)

| ID | Recommendation | Addresses row(s) | Rough size | Status |
|---|---|---|---|---|
| R10 | Add a closed ExecutionState transition graph (`vocab.EXECUTION_TRANSITIONS`) and a `validate_execution_transition(from_state, to_state) -> list[Finding]` check (mirroring `validate_lifecycle_transition`'s pattern, but as a branching graph rather than a single linear happy path, since `ISSUED` has three legal successors): `PLANNED -> STARTED -> ISSUED`, then `ISSUED -> COMPLETED` / `FAILED` / `INDETERMINATE -> RECONCILED`. Wire it into `work set-execution-state` as a blocking ERROR gate (check-then-mutate, mirroring `work set-state`'s existing pattern) -- an explicit, reconciled design decision, not a warning-only advisory. Deliberately does NOT attempt to detect a *stalled* `ISSUED` item with no terminal follow-up at all: §15 defines no staleness threshold/policy for that, and no lifecycle_state-progression proxy (e.g. reaching `OBSERVED`/`VERIFIED`) was used, since that would invent a semantic assumption the pack does not itself establish. | 2.2 | Medium | **Done** — see Changelog. `vocab.EXECUTION_TRANSITIONS` + `validation.validate_execution_transition` (19 tests, `tests/test_execution_transition.py`) + `cli.py`'s `work set-execution-state` gate (7 tests, `tests/test_work_set_execution_state_cli.py`; 1 pre-existing test in `test_cli.py` amended to route through the now-enforced legal path). Row 2.2 moves NON-CONFORMANT → PARTIAL (deliberately not CONFORMANT: transition-legality is fully enforced and tested, but the ISSUED-staleness half of §15's intent is a disclosed, genuinely unimplemented gap -- no policy exists in the pack to check it against). |
| R14 | Add a pure `check_claim_expiry(item: WorkItem, max_age: timedelta, now: Optional[datetime] = None) -> list[Finding]` hook that detects an expired `ACTIVE` claim under a caller-supplied `max_age` policy and reports it as a `CLAIM_EXPIRED` `Finding`, without mutating anything itself; plus a separate, explicit `work expire-claim <id> --max-age-hours <N>` CLI command that re-checks expiry and, on a genuine expiry, mutates `Ownership` only (`ClaimStatus.ACTIVE -> EXPIRED`, preserving `owner`/`claimed_at`) while leaving `lifecycle_state` untouched, per the user's explicit, binding decision not to silently resolve the §9.1↔§24.1 `EXECUTING -> PLANNED` tension inside application code. | 2.16 | Medium (new pure function + explicit CLI mutation command) | **Done** — see Changelog. `validation.check_claim_expiry` (pure, 15 tests) + `cli.py work expire-claim` (ownership-only mutation, 9 tests). Row 2.16 moves NON-CONFORMANT → PARTIAL (deliberately not CONFORMANT: the `PLANNED`-transition half of §24.1 remains disclosed-open due to the unresolved §9.1 tension, not silently decided). |
| R16 | **Original claim corrected during Phase 6 investigation** (see row 3.4 and the Changelog for the full note): the recommendation as originally written assumed no mechanism existed to name "the affected unit" on an override -- investigation found `DecisionRecord.related_unit_ids`/`related_work_item_ids` already existed and were already CLI-wired, from earlier Phase 5B work; that premise was simply wrong. **Revised recommendation, implemented**: add `OVERRIDE_WITHOUT_LINKED_UNIT` (WARNING) when an override names neither field, plus unconditional `RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND` (ERROR, mapping-gated) dangling-reference checks for both fields, mirroring `validate_final_report`'s existing `RELATED_DECISION_NOT_FOUND` pattern. The "strengthened beyond what the override substantiates" half is deliberately NOT implemented: no classification history/snapshot exists anywhere in this schema (`implementation_status`/`evidence_class` have no equivalent of `lifecycle_log`), so no honest causal check can be built without inventing new state -- disclosed as a genuine, permanent verification boundary, not silently decided or proxied. | 3.4 | Medium (revised down after investigation: the "name the affected unit" mechanism already existed; only the missing validation logic on top of it needed building) | **Done** — see Changelog. `validation.py`'s `validate_decision_record` (11 tests) + `cli.py`'s `_related_units`/`_related_work_items_for_decision` helpers wired into `decision create`/`resolve`/`show`/`validate` (5 tests). Row 3.4 moves NON-CONFORMANT → PARTIAL (deliberately not CONFORMANT: the classification-strengthening half remains a disclosed, unimplemented gap). |
| R7 | ~~Model a minimal Authority Contract: an `Authority` value type with an explicit attenuation relation~~ -- investigation found §11 supplies no worked example and no authority-value representation/partial order for `derive(A, C) ⪯ A` to be checked against (unlike §26.2's SC#2 example that grounded R16); the recommendation's own worked example doesn't work as stated because `WorkItem.required_authority`/`forbidden_authority`/`KnowledgeUnit.authority_implications` are unstructured free text with no defined ordering. A `capabilities: list[str]` field with subset-inclusion as `⪯` was considered and rejected: it would silently invent that capability tags are the authority value, that subset means "at most as powerful," and that a work item's capabilities derive from its source unit's -- none of which §11 specifies. Resolved instead as a documentation-only scope disclosure, mirroring R8's §13 resolution: package docstring gained a "Scope: no Authority Contract enforcement (v2 §11)" section, and `WorkItem`/`KnowledgeUnit`/`DecisionRecord` docstrings each point to it. The disclosure is explicit that §11 **remains normative** for a system that actually performs derivation -- this package simply never crosses that boundary. | 1.25 | Large (new concept) → resolved Tiny (documentation only) | **Done** -- 4 new tests in `tests/test_scope_disclosures.py` assert the §11/R7 disclosure text is present in the package docstring and in `WorkItem`/`KnowledgeUnit`/`DecisionRecord` docstrings (confirmed red before the docstrings were written, green after). No model/schema/validation/CLI change. Row 1.25 now NOT-APPLICABLE-by-disclosed-scope. Full suite: 449/449 passing (445 + 4). |
| R1 | Add a `TrustTier` (HUMAN_GOVERNANCE / ARENA_SUPERVISOR / ARENA_AGENT) to `decided_by`/override-attribution fields, or at minimum document explicitly that this implementation trusts the *string identity* of an authorizer without independently verifying trust tier -- as a disclosed, not silent, scope limitation. | 1.5 | Large (new concept) → resolved Medium (one enum, one field, two validation checks, narrowly scoped to §26.2's override attribution -- not a generalized actor-identity model) | **Done** -- unlike R7 (§11 gave no worked example anywhere in the pack), §26.2 gives an explicit, itemized four-bullet override-attribution requirement, and "the authorizing party and their role in the trust hierarchy" is one of those four bullets, half of which (the party) was already implemented (`OVERRIDE_WITHOUT_ATTRIBUTION`). Investigation found this was a materially different, genuinely concrete gap, not a candidate for R7-style disclosure. New `TrustTier` enum + `DecisionRecord.decided_by_trust_tier` field; `OVERRIDE_WITHOUT_TRUST_TIER` (ERROR, required whenever `overrides_stop_condition` is set) + `OVERRIDE_BY_AGENT_SELF` (ERROR, direct enforcement of §26.2's "MUST NOT be lifted by the agent's own initiative"). Scope locked narrow before implementation (stop-and-reconcile): only `DecisionRecord`'s override attribution, not `raised_by`/`Ownership.owner`/`WorkItem`'s authorization option -- those carry no §3/§26.2 attribution obligation. A non-override decision has no trust-tier obligation either way (no invented restriction beyond what §3/§26.2 actually require). 9 new tests in `tests/test_validation.py` (including a dedicated AST-based test proving no ordering/comparison semantics were introduced onto `TrustTier`, keeping it categorically separate from R7's disclosed, deliberately-unimplemented §11 authority-value algebra) + 2 new CLI round-trip tests in `tests/test_cli.py`, plus a real end-to-end manual smoke test through actual CLI/storage (unlinked/no-tier override → `OVERRIDE_WITHOUT_TRUST_TIER` ERROR; `ARENA-AGENT` tier → `OVERRIDE_BY_AGENT_SELF` ERROR + non-zero exit via `decision validate`; `HUMAN-GOVERNANCE`/`ARENA-SUPERVISOR` tier + full attribution → clean, exit 0). Full suite: 460/460 passing (458 + 2). Row 1.5 now PARTIAL. |

**Status as of this update:** Class 1 (Phase 5A: R13, R9, R5, R6, R11,
R12, R20, R22) is fully done. **Phase 5B (locked order R3 → R15 → R19 →
R21 → R17) is fully done and FROZEN** — all five recommendations are DONE
and independently re-audited with zero downgrades (see Changelog and rows
1.11/3.2/4.4/4.11/3.5). **Phase 5C (locked order R8 → R4 → R18 → R2) is
now fully done and FROZEN** — R8 is DONE (row 1.27 reclassified to
NOT-APPLICABLE-by-disclosed-scope); R4 is DONE (row 1.14 remains PARTIAL,
now with its permanent verification boundary explicitly disclosed in
code); R18 is DONE (row 3.6 stays CONFORMANT, now covering every §27
template section with a field-level home); R2 is DONE (row 1.8 moves
PARTIAL → CONFORMANT, via an additive `content_scan_anomalies` field, an
explicit-only CLI attach path, and one shape-only validation check with
no coverage claim). All four were independently re-audited directly
against live source and the pack's own literal text, with **zero
downgrades**; one prose-only drift was found and corrected (row 3.6's
evidence cell had overstated an implementation-label match as
"verbatim" — corrected to quote §27's actual literal labels; see the
Phase 5C re-audit Changelog entry). **Phase 6 is now IN PROGRESS**
(locked order R14 → R10 → R16 → R7 → R1): **R14 is DONE** (row 2.16
moves NON-CONFORMANT → PARTIAL, via a pure `check_claim_expiry` detection
hook plus an explicit, ownership-only `work expire-claim` CLI mutation
command; deliberately not CONFORMANT, since the pack's own §24.1
"reverts to PLANNED" clause conflicts with §9.1's already-enforced
`LIFECYCLE_BACKWARD_TRANSITION` rule, a tension this implementation
disclosed and left open rather than silently resolving). **R10 is DONE**
(row 2.2 moves NON-CONFORMANT → PARTIAL, via a closed
`EXECUTION_TRANSITIONS` graph plus `validate_execution_transition`, wired
into `work set-execution-state` as a blocking CLI gate; deliberately not
CONFORMANT, since detecting a *stalled* `ISSUED` item with no terminal
follow-up remains a disclosed, genuinely unimplemented gap -- §15 defines
no staleness threshold/policy for it, and no lifecycle_state-progression
proxy was substituted for one). **R16 is DONE** (row 3.4 moves
NON-CONFORMANT → PARTIAL, via `OVERRIDE_WITHOUT_LINKED_UNIT` -- an
override naming neither `related_unit_ids` nor `related_work_item_ids` is
not auditable against any specific affected record -- plus unconditional
`RELATED_UNIT_NOT_FOUND`/`RELATED_WORK_ITEM_NOT_FOUND` dangling-reference
checks, mirroring `validate_final_report`'s existing
`RELATED_DECISION_NOT_FOUND` pattern; investigation also corrected the
recommendation's original premise -- the "name the affected unit"
mechanism already existed from earlier Phase 5B work, only the validation
logic on top of it was missing; deliberately not CONFORMANT, since
detecting that a classification was *causally strengthened by* an
override remains a disclosed, genuinely unimplemented gap -- no
classification history/snapshot is persisted anywhere in this schema to
make that comparison honestly, and inferring it from the current value
alone was explicitly considered and rejected as an invented proxy). **R7
is DONE** (row 1.25 moves NON-CONFORMANT → NOT-APPLICABLE-by-disclosed-scope,
mirroring R8's own §13 resolution exactly: investigation found §11 gives
no worked example anywhere in the pack — unlike §26.2's SC#2 example that
grounded R16 — and no authority-value representation, partial order, or
attenuation relation exists anywhere in this codebase for
`derive(A, C) ⪯ A` to be checked against for even one concrete case; the
recommendation's own worked example does not work as stated, since
`WorkItem.required_authority`/`forbidden_authority` and
`KnowledgeUnit.authority_implications` are unstructured free text with no
defined ordering. A `capabilities: list[str]` field with subset-inclusion
as `⪯` was explicitly considered and rejected as inventing semantics §11
never specifies — that capability tags are the authority value, that
subset means "at most as powerful," and that a work item's capabilities
derive from its source unit's. Resolved as a documentation-only scope
disclosure instead: the package docstring gained a "Scope: no Authority
Contract enforcement (v2 §11)" section, and `WorkItem`/`KnowledgeUnit`/
`DecisionRecord` docstrings each point to it; the disclosure explicitly
states §11 **remains normative** for any system that actually performs
derivation — this is a boundary disclosure, not a claim that §11 is
non-normative). **R1 is DONE** (row 1.5 moves NON-CONFORMANT → PARTIAL):
unlike R7, §26.2 gives an explicit, itemized four-bullet override-
attribution requirement, and "the authorizing party and their role in
the trust hierarchy" is one of those four bullets, half of which (the
party) was already implemented (`OVERRIDE_WITHOUT_ATTRIBUTION`) -- a
materially different, genuinely concrete gap from R7's, not a candidate
for the same disclosure-only disposition. New `TrustTier` enum
(`HUMAN-GOVERNANCE`/`ARENA-SUPERVISOR`/`ARENA-AGENT`, implementation-only
vocabulary mirroring the `ClaimStatus`/R22 precedent) plus new optional
`DecisionRecord.decided_by_trust_tier` field; `OVERRIDE_WITHOUT_TRUST_TIER`
(ERROR, required whenever `overrides_stop_condition` is set) plus
`OVERRIDE_BY_AGENT_SELF` (ERROR, direct enforcement of §26.2's "MUST NOT
be lifted by the agent's own initiative"). Scope locked narrow before
implementation (stop-and-reconcile): only `DecisionRecord`'s override
attribution, not `raised_by`/`Ownership.owner`/`WorkItem`'s authorization
option, since §3/§26.2 make no attribution claim about those; a
non-override decision has no trust-tier obligation either way, avoiding
an invented restriction beyond what the pack actually requires.
`TrustTier` carries no ordering/magnitude/`⪯` relation and is never
conflated with R7's disclosed, deliberately-unimplemented v2 §11
authority-value algebra -- confirmed by a dedicated AST-based test
proving no ordering comparison involving `TrustTier` exists anywhere in
`validation.py`. **This closes Phase 6**: all five items (R14, R10, R16,
R7, R1) are now DONE, in the locked order.


---

## What this audit did **not** do

- The original audit (baseline form of this document) did not modify any
  implementation or test file — pure verification. All Class-1
  (evidence/test hardening) items in Phase 5A are now complete (R13, R9,
  R5, R6, R11, R12, R20, R22 — see the Changelog above for the full
  per-item breakdown). Across all of Phase 5A, exactly two implementation
  files were touched, both narrow and additive: `models.py` (added a
  missing `classification` key to `_default_provenance()`'s dict, R12 —
  driven by a genuine spec-vs-implementation gap found while writing the
  test, confirmed with the user before implementing) and `vocab.py`
  (rewrote two docstrings to disclose non-pack vocabulary provenance, R22
  — a documentation change, not a behavior change). No other
  implementation file was touched.
  **Phase 5B (locked order R3 → R15 → R19 → R21 → R17) is now complete:**
  R3 (row 1.11, extended `vocab.MIN_CONFIDENCE_FOR_CLASS`), R15 (row 3.2,
  added `vocab.STOP_CONDITIONS` plus one new `validation.py` check), R19
  (row 4.4, added `vocab.WorkItemStage` plus one new `validation.py`
  check, plus a type-annotation-only change in `models.py` and 5
  literal-string-to-enum-member call-site updates in `cli.py`), R21 (row
  4.11, added an optional `work_items` parameter plus one new
  `validation.py` check on `ChangeImpactAnalysis`, plus one new additive
  `cli.py` helper wired into 4 existing `impact` commands), and R17 (row
  3.5, added a new additive `FinalReport.related_decision_ids` field —
  confirmed with the user first, per the R3/R12 stop-and-reconcile
  precedent, since no existing field could represent it — plus an
  optional `decisions` parameter and one new `validation.py` check, plus
  one new CLI option/helper wired into 3 `report` commands, plus one
  presentation-only line in `reporting.py`) — see the Changelog above.
  R19, R21, and R17 are the three Phase 5B items to touch `models.py`/
  `cli.py` at all, and every touch across all three was the smallest
  possible additive change (a type annotation; passing an existing enum
  member instead of an existing literal string; a new optional keyword
  parameter defaulting to `None`; a small helper function; one new list
  field mirroring an existing field's shape) rather than any reshaping of
  the affected records or commands. `export.py` and `html.py` remain
  fully untouched by all of Phase 5B — `reporting.py` gained exactly one
  presentation-only display line (R17), no new logic. Per the roadmap, a
  full Phase 5B re-audit is the next step before Phase 6 begins.
- Did not re-litigate any Phase 1–4 frozen decision — all four phases were
  spot-checked for continued structural integrity (import direction,
  no-semantic-authority in export/html) and found intact.
- Did not assess the two Markdown template packs (`templates/`,
  `arena-agent-instructions-pack.md` v1) for internal consistency — the
  user's standing instruction is that v1 and v2 remain independently
  frozen references; this audit only checked the Python implementation
  against v2, the declared canonical basis.
