# arena-agent (Python)

A working Python implementation of the **Arena Agent Prompt Instructions
Pack** — the vocabulary, record types, and rules from
[`arena-agent-instructions-pack.md`](../arena-agent-instructions-pack.md)
(v1) and [`arena-agent-instructions-pack-v2.md`](../arena-agent-instructions-pack-v2.md)
(v2, canonical here), turned into enums, dataclasses, validators, a JSON
workspace store, Markdown reporting, and a CLI.

This is not a thin data-model shim: the point of the pack is that certain
things must never be silently claimed (implementation from architecture,
verification from test existence, completion from a returned exit code),
and this package actually **enforces** that — `arena_agent.validation`
returns concrete `Finding`s (errors/warnings, each tagged with the pack
section it comes from) rather than just holding fields.

v2 is treated as canonical (unified lifecycle model, consolidated
counterexample object, reconciled verification vocabulary, etc.). Where v1
used a different spelling for the same concept — e.g. `INAPPLICABLE` vs.
`NOT-APPLICABLE` — the v1 spelling is kept as an alias so code/data written
against either pack version resolves the same way.

## Install

```bash
cd arena_agent_py
pip install -e .
```

This installs the `arena` CLI and the `arena_agent` library.

## Output modes: Rich tables vs. `--json`

By default the CLI renders human-friendly output through
[Rich](https://github.com/Textualize/rich): `list` commands print colored
tables (severity/status columns are color-coded, e.g. lifecycle `VERIFIED`
in green, `BLOCKED`/`FAILED` in red), `show` commands print a summary panel
plus the same Markdown rendering used elsewhere, and validation findings
print as a table with ERROR rows in bold red and WARNING rows in yellow.

Pass the global `--json` flag (before the subcommand, e.g.
`arena --json unit list`) to switch every command to machine-readable
output instead: exactly one JSON document on stdout per invocation, no
color codes, no box-drawing characters, no decorative text — safe to pipe
into `jq` or parse in a script. `list` commands emit a JSON array of
records; `create`/`show`/`validate`/lifecycle-transition commands emit an
object that always includes `findings` (each with `severity`, `code`,
`message`, `ref`), `has_errors`, `error_count`, and `warning_count`, so a
script can check for problems without re-implementing the pack's severity
rules. Exit codes are identical between the two modes — `--json` only
changes the *representation* of a result, never whether a command
succeeded; commands that enforce a hard rule (illegal lifecycle skip,
unattributed Stop Condition override, promoting a Counterexample without
confirmation, etc.) still exit non-zero either way.

```bash
arena --workspace .arena --json unit list | jq '.[] | select(.evidence_class == "CONFLICTING")'
arena --workspace .arena --json work validate ARENA-WORK-1 | jq '.has_errors'
```

Use `--no-color` (also global) to keep Rich's table/panel layout but drop
ANSI color, e.g. for log files that don't support it; it's ignored in
`--json` mode since that mode never emits color to begin with.

## Quick tour (CLI)

```bash
arena --workspace .arena init

# Repository Reality Audit (v2 §6/§28) — read-only filesystem scan
arena --workspace .arena audit create --repository /path/to/repo
arena --workspace .arena audit scan-fs ARENA-AUDIT-... --path /path/to/repo --max-depth 2
arena --workspace .arena audit show ARENA-AUDIT-...

# Knowledge Units (v2 §5/§7)
arena --workspace .arena unit create --domain repo --subject core --property status \
    --meaning "core crate is proposed" --evidence-class ARCHITECTURAL-PROPOSAL --confidence LOW

# Work Items with lifecycle, ownership, and verification gates (v2 §9/§24/§27/§35)
arena --workspace .arena work create --id ARENA-WORK-1 --title "Build core" --responsibility "..."
arena --workspace .arena work claim ARENA-WORK-1 --owner agent-1
arena --workspace .arena work set-state ARENA-WORK-1 CLASSIFIED   # ... stepwise, no skipping
arena --workspace .arena work gate ARENA-WORK-1 --gate Identity --method MANUAL-REVIEW --result PASS --evidence "..."
arena --workspace .arena work validate ARENA-WORK-1

# Decision Records, including Stop Condition overrides (v2 §23/§26.2)
arena --workspace .arena decision create --question "..." --raised-by agent-1 --override-stop-condition 2
arena --workspace .arena decision resolve <id> --choice A --decided-by supervisor-1 --scope "this work item"

# Unified Counterexample staging (v2 §22)
arena --workspace .arena ce create --first-divergence "..." --expected "..." --actual "..."
arena --workspace .arena ce promote <id> OBSERVED-FAILURE
arena --workspace .arena ce promote <id> REPRODUCIBLE-DEFECT --reproduction-command "..." --confirmed

# Change-Impact Analysis (v2 §36) and Knowledge Graph (v2 §34)
arena --workspace .arena impact create --target-unit ARENA-... --description "..."
arena --workspace .arena graph create

# Ingested Content Contract scan (v2 §4.1) — flags anti-pattern / directive
# phrasing found in repository text; never treats it as an instruction
arena scan-content README.md

# Final Report / Completion Contract (v2 §39/§40)
arena --workspace .arena report create --id ARENA-REPORT-1 --objective "..." \
    --scope "..." --related-audit ARENA-AUDIT-1 --related-work-item ARENA-WORK-1
arena --workspace .arena report check ARENA-REPORT-1 --item work_performed
arena --workspace .arena report finalize ARENA-REPORT-1 --status COMPLETE

# Arena Wiki pages (v2 §19/§38) — fixed 18-page index (00 Status .. 17 Runbooks)
arena --workspace .arena wiki create --page 00 --content "..." --scope "..." --updated-by agent-1
arena --workspace .arena wiki update ARENA-WIKI-00 --add-knowledge-unit ARENA-... --change "linked evidence" --updated-by agent-1
arena --workspace .arena wiki show ARENA-WIKI-00
arena --workspace .arena wiki render ARENA-WIKI-00 --to wiki/00-status.md

# Workspace export (v2 §37/§38 companion templates) — assembles existing
# renderers into a Markdown artifact tree; never a second source of truth
arena --workspace .arena export validate     # pipeline dry-run, writes nothing
arena --workspace .arena export --to export  # writes export/index.md, export/wiki/*.md, ...

# HTML presentation — a browsable rendering of the *same* export plan
# `arena export` builds; introduces no new facts, no new validation
arena --workspace .arena html --to export-html
```

### Wiki pages: header metadata is always derived, never stored

`WikiPage` persists only what is genuinely *authored*: `content`, the
records it references (`knowledge_unit_ids`/`decision_ids`/`audit_ids`/
`work_item_ids`), `dependencies` on other pages, and `change_history`. Its
`page_number` is a closed 18-value enum (`WikiPageNumber`, `00`..`17`) and
`title` is a read-only property derived from it — `wiki create` requires
`--page` to be one of those 18 values and rejects anything else before the
record is ever written; there is no independent title field to drift out
of sync with the canonical §38 index.

Deliberately absent from `WikiPage` are `classification`,
`implementation_status`, `evidence_status`, and `open_decisions` — the
exact fields the arena-wiki-page-template.md "Required Header Block"
displays. `validation.derive_wiki_header` computes those fresh, every
time, from whatever KnowledgeUnit/DecisionRecord/RepoAudit/WorkItem
records the page currently references (`wiki show`/`wiki render` do this
automatically), so a page can never assert an IMPLEMENTED classification
that survives after the underlying Knowledge Unit reverts to PLANNED. This
mirrors the Final Report's `derive_overall_status_ceiling` pattern
("ceiling from evidence, not from claim") and is the direct enforcement
point for §38's rule against letting planned architecture appear as
implemented behavior.

`wiki create`/`wiki update` follow the same always-persist semantics as
every other `create`/lifecycle command in this CLI: a dangling reference
(`WIKI_REFERENCE_NOT_FOUND`) is reported as an ERROR-severity finding
alongside the write, not used to reject it; only `wiki validate` gates its
exit code on ERROR severity.

Wiki validation is split into two explicit, independently callable layers
in `validation.py`, mirroring the pack's own separation of concerns:

- **`validate_wiki_page(page)`** — local/structural checks using only the
  page's own fields (its signature has no parameter through which another
  record could even be passed in): the page number is one of the closed
  00-17 set, content/title/timestamps are present, every referenced ID and
  every dependency ID is syntactically a well-formed `ARENA-...` id (not
  whether it *resolves* — that's layer 2), and a page doesn't list itself
  as its own dependency.
- **`validate_wiki_references(page, knowledge_units=..., decisions=...,
  audits=..., work_items=...)`** — cross-record checks: whether each
  referenced ID actually resolves against the (caller-loaded) records
  supplied, never touching storage itself.

`wiki create`/`update`/`validate`/`show`/`render` all run both layers
together, so a malformed ID (e.g. `not-an-id`) and a well-formed-but-
nonexistent one (e.g. `ARENA-UNIT-GHOST`) are each caught by the layer
responsible for that specific failure mode, rather than one function
silently doing both jobs.

### Workspace export: an artifact assembly, not a second source of truth

`arena_agent.export` and the `arena export`/`arena export validate` CLI
commands assemble the same per-record `render_*` output every `show`/
`render` command already produces into a directory tree — they contain no
export-only rules and no export-only rendering logic:

```
export/
├── index.md
├── audits/<id>.md              (RepoAudit,      render_repo_audit)
├── knowledge-units/<id>.md     (KnowledgeUnit,   render_knowledge_unit)
├── work-items/<id>.md          (WorkItem,        render_work_item)
├── decisions/<id>.md           (DecisionRecord,  render_decision_record)
├── counterexamples/<id>.md     (CounterexampleRecord, render_counterexample)
├── impacts/<id>.md             (ChangeImpactAnalysis, render_change_impact)
├── reports/<id>.md             (FinalReport,     render_final_report)
├── graph/<id>.md                (KnowledgeGraph,  render_knowledge_graph)
└── wiki/<NN>-<slug>.md          (WikiPage,        render_wiki_page)
```

The pipeline is exactly: **load → validate records → resolve references →
validate cross-record invariants → derive projections → render → write**.
`arena export validate` runs everything through "derive projections" and
reports findings without writing anything; `arena export` runs the same
pipeline and then writes the tree (always writing, consistent with this
CLI's create/finalize semantics — findings, including ERROR severity, are
reported alongside the write rather than blocking it).

Two invariants are enforced end-to-end, both directly inherited from
Phase 1/2 rather than reinvented here:

- **Missing ≠ invalid ≠ blocked ≠ not applicable.** A canonical Wiki page
  (00–17) that was never created shows up in `index.md` and in
  `export validate`'s findings as `WIKI_PAGE_MISSING` (INFO severity) —
  export never manufactures a placeholder file to make the directory
  look complete. A page that *was* created but has ERROR-severity
  findings (e.g. a dangling reference) is still written, with those
  findings rendered inline in its own file, so "exists but is invalid" is
  never confused with "doesn't exist."
- **No stale cached headers.** Every exported Wiki page's header
  (classification/implementation-status/evidence-status/open-decisions)
  is computed by the same `derive_wiki_header` call `wiki render` uses,
  from whatever the referenced records' *current* state is at export
  time — not a value read off any stored field. If a referenced
  Knowledge Unit's `implementation_status` changes between two exports,
  the second export's rendered header changes with it, with no
  intervening step that could leave the old value behind.

`ExportPlan` (the return value of `build_export_plan`) is the artifact
manifest for one export operation, and is treated as a frozen contract:

```
ExportPlan
├── generated_at        # ISO timestamp, set once, at build time
├── workspace_root       # which workspace this snapshot came from
├── pack_version
├── items[]              # one ExportItem per record
│   ├── kind / record_id       # identity
│   ├── relative_path          # None if the item is `missing`
│   ├── markdown                # already-rendered; None if `missing`
│   ├── findings                # already computed; never recomputed downstream
│   └── missing                 # True only for a canonical slot with no record
└── index_markdown       # already-rendered export/index.md content
```

`write_export_plan` has **no semantic authority** over any of this: it
does not validate, does not render, does not decide what's missing — it
only materializes whatever the plan already says onto disk. That
separation keeps three concepts distinct rather than collapsed into one
`export` verb:

- **validate** — is this record legitimate? (`validation.py`, unchanged
  from Phase 1/2)
- **export** (`build_export_plan`) — assemble a snapshot/projection of
  currently-valid state, as Markdown, with findings attached
- **write** (`write_export_plan`) — persist that already-built projection
  to a directory; a pure filesystem step with no judgment calls left to
  make

The practical payoff: a presentation layer (a future HTML exporter, or
any other target) can consume an already-built `ExportPlan` — its
already-rendered Markdown per item, its already-computed findings, its
already-resolved missing-page list — without ever re-opening the
workspace or re-running validation itself. That keeps a second
presentation format from becoming a second implementation of the pack's
semantics: `ExportPlan → HTML projection → HTML files`, not
`HTML exporter → workspace → models → validation → more business logic`.

Because `export` can write an artifact containing ERROR-severity findings
(consistent with this project's iterative-record model — export doesn't
reject a write just because a record isn't currently valid),
`export/index.md` makes that fact conspicuous rather than incidental: it
carries a `⚠` warning banner immediately after the manifest metadata (not
buried in a tail-end summary) whenever any item has ERROR findings, and
marks every offending item's own list entry with `⚠ has ERROR findings`,
in both the per-kind sections and the 18-page Wiki index.

### HTML presentation: a projection of `ExportPlan`, not a second export pipeline

`arena_agent.html` and the `arena html` CLI command are exactly the
"future HTML exporter" described above, built to the letter of that
contract. The module exposes exactly three functions:

```
render_html_document(item: ExportItem) -> str
render_html_index(plan: ExportPlan) -> str
write_html_export(plan: ExportPlan, html_root: Path) -> list[Path]
```

and imports nothing from this project except `ExportPlan`/`ExportItem`
and the naming constants `EXPORT_SUBDIRS`/`KIND_TITLES` from
`arena_agent.export` — no `Workspace`, no `validate_*`, no `derive_*`,
no record-ID resolution, no status computation. Everything it renders —
per-item Markdown, findings, the missing flag, and the manifest metadata
(`generated_at`/`workspace_root`/`pack_version`) — is read directly off
the `ExportPlan`/`ExportItem` it's given:

```
ExportPlan
├── item.markdown ───────► HTML document body (via the `markdown` library)
├── item.findings ───────► HTML findings table + ERROR banner
├── item.missing ────────► missing-page HTML stub (never markdown.markdown(None))
└── plan metadata ───────► HTML index header + navigation
```

Markdown → HTML conversion is delegated to the `markdown` PyPI package
(`markdown.markdown(text, extensions=["tables", "fenced_code",
"sane_lists"])`) rather than a hand-rolled parser — this module only adds
a presentation shell (metadata header, findings block, navigation, CSS)
around that conversion. `render_html_index` builds its navigation purely
from `plan.items`/`plan.missing_items()`/`plan.all_findings()`/
`plan.generated_at`/`plan.workspace_root`/`plan.pack_version`; it never
scans the filesystem, so HTML output is fully deterministic with respect
to the plan object it was given. Output paths mirror the Markdown
export's layout exactly, with a `.md` → `.html` suffix swap
(`knowledge-units/ARENA-X.md` → `knowledge-units/ARENA-X.html`).

`write_html_export` has the same "no semantic authority" property as
`write_export_plan`: it writes whatever `render_html_document`/
`render_html_index` already produced, and skips a `missing` item's
per-record file for the same reason the Markdown writer does — writing
one would fabricate a page nobody authored.

`tests/test_html.py` proves the projection property directly, including
the single most important case: build a plan, render it once, then
**mutate the `ExportPlan` object itself** (change an item's `markdown`,
add an ERROR finding, change `generated_at`/`workspace_root`) and render
again — the second render reflects the mutation exactly, with no
Workspace reopened and no validation rerun in between
(`test_html_reflects_plan_mutated_after_being_built_not_a_fresh_recompute`).
Other tests confirm (via AST inspection of `html.py`'s own imports, not
just behavior) that the module never imports `storage`/`Workspace` or any
`validate_*`/`derive_*` function, and that its public surface is exactly
the three contracted functions.

`arena html [--to DIR]` (default `./export-html`) builds the export plan
the same way `arena export` does (via `build_export_plan`) and always
writes (same create/finalize always-persist semantics as bare
`arena export`); use `arena export validate` first for a pre-flight
check, since its findings are exactly what an HTML export of the same
workspace would also report.

### Final Report status: claimed vs. demonstrated

`overall_status` is not just a label the caller sets — `report finalize`
runs `validate_final_report`, which computes the *highest status the
report's own evidence actually supports* (`derive_overall_status_ceiling`)
and rejects any claim above it as `STATUS_MASQUERADING`:

| Evidence condition | Ceiling |
|---|---|
| Completion checklist (v2 §39) incomplete | `INCOMPLETE` |
| Checklist complete, but ERROR findings exist | `INCOMPLETE` |
| Checklist complete, no ERROR, but WARNINGs / evidence gaps / open decisions remain | `COMPLETE-WITH-WARNINGS` |
| Checklist complete, nothing outstanding | `COMPLETE` |

`BLOCKED` is handled separately — it's a claim about an active blocker, not
a lower point on that scale, so it requires its own substantiation, and a
loosely-worded reference doesn't count as one:

- **an actually-`OPEN` Decision Record** (`--decision-id` via
  `report set-blocking-reason`) — the CLI loads the referenced record and
  `validate_final_report` checks its `status`; a stale ID pointing at a
  `RESOLVED`/`SUPERSEDED` decision is rejected (`BLOCKING_DECISION_NOT_OPEN`),
  and an ID that can't be resolved at all is flagged
  (`BLOCKING_DECISION_NOT_VERIFIED`) rather than silently trusted;
- **an unoverridden entry** in `stop_conditions_triggered`; or
- **a meaningful `blocking_reason`** — non-empty is not suffient: a small
  set of placeholder answers (`TBD`, `x`, `blocked`, `N/A`, …) and anything
  under ~15 characters are rejected as not "meaningful enough to audit"
  (`BLOCKING_REASON_NOT_MEANINGFUL`).

An unsubstantiated `BLOCKED` claim is rejected as `UNJUSTIFIED_BLOCKED_STATUS`.

This 4-value `OverallStatus` (`COMPLETE` / `COMPLETE-WITH-WARNINGS` /
`BLOCKED` / `INCOMPLETE`) is implementation vocabulary, not an Appendix A
controlled vocabulary — the pack's own §40 template only shows `COMPLETE /
PARTIAL / BLOCKED`. `PARTIAL` is still accepted everywhere (CLI, direct
field assignment, JSON records) as a legacy alias that normalizes to
`INCOMPLETE`, and `render_final_report` emits both spellings so the
rendered artifact stays literally conformant with the §40 template while
this implementation reasons internally with the finer-grained model.

The report also carries a `core_principle_checklist` (v2 §43's "no claim
without provenance" list) as real per-item data (`report check-principle`)
rather than a static markdown checklist — it's rendered and reported but,
consistent with §43 being explicitly non-normative, does not itself gate
`overall_status`.

Every mutating command that produces a rule violation prints a findings
table (or, in `--json` mode, a `findings` array) tagged with the pack
section each finding comes from. Commands whose purpose is to enforce a
specific hard rule (illegal lifecycle jump, resolving a decision with no
attribution, promoting an unconfirmed Counterexample, etc.) exit non-zero
in both output modes.

## Library usage

See `examples/end_to_end_demo.py` for a full walkthrough: Repo Audit →
Knowledge Unit → Work Item (claim → lifecycle → gates) → Decision Record
(with a Stop Condition override) → Counterexample staging → Change-Impact
Analysis → Knowledge Graph → Final Report, all validated at each step.

```bash
python examples/end_to_end_demo.py
```

## Package layout

| Module | Pack reference | Purpose |
|---|---|---|
| `arena_agent.vocab` | v2 Appendix A | Controlled-vocabulary enums, plus v1 aliases; includes the closed 18-page `WikiPageNumber` index (v2 §38) |
| `arena_agent.ids` | v2 §8 | Stable ID generation/validation (`ARENA-...`) |
| `arena_agent.models` | v2 §7/§16/§22/§27/§36/§38/§39-40 | Record dataclasses, including the thin `WikiPage`/`WikiChangeHistoryEntry` model |
| `arena_agent.validation` | throughout | Rule enforcement — the actual "never silently claim X" logic |
| `arena_agent.graph` | v2 §34 | Knowledge graph, planned/observed partition, dependents traversal |
| `arena_agent.content_scan` | v2 §4.1 | Ingested Content Contract helper (flag, never obey) |
| `arena_agent.storage` | — | JSON file-backed workspace |
| `arena_agent.reporting` | — | Markdown rendering matching the companion template pack |
| `arena_agent.output` | — | Rich table/panel rendering vs. `--json` mode, shared by every CLI command |
| `arena_agent.export` | v2 §37/§38 companion templates | Workspace export: orchestrates existing `validate_*`/`render_*` functions into `export/` — no export-only rules or rendering logic |
| `arena_agent.html` | — | HTML presentation: projects an already-built `ExportPlan` into a browsable `export-html/` tree — no filesystem access, validation, or derivation of its own |
| `arena_agent.cli` | — | `arena` command-line tool |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Every record-type command group (`unit`, `work`, `decision`, `ce`, `audit`,
`impact`, `report`, `graph`, `wiki`) exposes the same `create`/`list`/
`show`/`validate` surface for consistency, plus type-specific commands
(`work claim`/`gate`/`authorize`/`set-execution-state`/`set-evidence-state`,
`decision resolve`, `ce promote`/`resolve`, `audit scan-fs`,
`graph add-node`/`add-edge`/`dependents`, `wiki update`/`render`, etc.). Run
`arena <group> --help` to see a group's full command list.

`WorkItem` tracks lifecycle state (the DISCOVERED..VERIFIED happy path) as
a separate axis from `authorization_state`, `execution_state`, and
`evidence_state` -- each is set independently via its own command, and
validation blocks the AUTHORIZED/VERIFIED lifecycle transitions unless the
corresponding axis has actually been advanced (not just left at its
default), so "VERIFIED" can't silently mean "moved to the VERIFIED bucket
without any evidence check."

241 tests cover vocabulary aliasing, ID generation, every validation rule
(including deliberately-triggered violations), the knowledge graph
integrity checks, JSON round-tripping, Markdown rendering, and full CLI
workflows in both output modes (including a filesystem-touching test that
asserts a scanned repository is never modified, `--json`-mode tests
that assert exactly one parseable JSON document with no leaked ANSI/box
characters, CLI-level regression tests confirming that corrupted JSON
records, missing required fields, and missing record IDs all produce a
single clean error line with a non-zero exit code rather than a raw Python
traceback, and a parametrized negative-path matrix asserting all 8
claimed-status/evidence-ceiling combinations plus both BLOCKED
substantiation outcomes for Final Report status derivation). Of these, 150
are the frozen Final Report/status-machinery suite (unchanged since Phase
1 was closed), 48 cover the Wiki Page model, storage, and the two-layer
validation/rendering/CLI added in Phase 2 — including that the closed
18-page index rejects out-of-range page numbers before persistence
(both from the CLI's `--page` choice and, defensively, from a
hand-constructed record that bypasses `__post_init__`), that
`validate_wiki_page`'s signature has no parameter for other records so it
is structurally incapable of doing cross-record checks, that malformed ID
syntax and legitimately-missing records are each caught by their own
distinct layer, that `derive_wiki_header` recomputes classification/
implementation-status/evidence-status/open-decisions fresh from referenced
records rather than reading them off `WikiPage` (which has no such fields
to read), and that a `WikiPage`'s `title` cannot be set independently of
its `page_number` — and 23 cover the Phase 3 export pipeline, including
that a canonical Wiki page with no record is reported as `WIKI_PAGE_MISSING`
(INFO) and never written as a synthesized file, that `export`'s output
directory always contains exactly the pages that actually exist, that
`export validate` writes nothing to disk while `export` always writes even
when ERROR findings are present, that `ExportPlan` carries a non-empty
ISO-parseable `generated_at`/`workspace_root`/`pack_version`, that
`write_export_plan` reproduces an item's `markdown` byte-for-byte with no
re-rendering (verified by mutating a plan's markdown in place and
confirming the write step doesn't overwrite it with a fresh render), that
`index.md`'s ERROR-severity banner appears before the per-record listing
sections (not just in the tail-end summary) and marks each offending
item's own line, and — the specific regression this phase exists to
prevent — that a Wiki page's exported header reflects a referenced
Knowledge Unit's *current* `implementation_status` across two exports
taken before and after that status changes, rather than a value computed
once and reused.

The remaining 20 (`tests/test_html.py`) cover Phase 4's HTML presentation
layer and are deliberately written as anti-regression boundary tests, not
just feature tests: an AST-level check that `html.py` never imports
`storage`/`Workspace` or any `validate_*`/`derive_*` function (so the
constraint holds even for code paths no runtime test happens to exercise),
a check that its public surface is exactly `render_html_document`/
`render_html_index`/`write_html_export`, that a missing `ExportItem`
never reaches `markdown.markdown(None)`, that an HTML document's ERROR
banner/findings table and an HTML index's ERROR-flagged links come from
`item.findings`/`plan.all_findings()` and nothing else, that link targets
in the HTML index are exactly each item's `relative_path` with `.md`
swapped for `.html`, that `arena html`'s JSON summary shares the same
`record_count`/`missing_wiki_pages` shape as `arena export validate`'s
(same `build_export_plan` call underneath), and — the load-bearing one,
directly mirroring Phase 3's `write_export_plan` mutation test — that
mutating an already-built `ExportPlan`'s markdown/findings/metadata and
re-rendering reflects the mutation exactly, with no workspace reopened
and no validation rerun in between.

One test (`test_lifecycle_failure_branches_match_pack_text_exactly`)
intentionally encodes a real gap found in the pack itself: v2 §9.1 defines
failure branches for 7 of its 8 canonical happy-path states — `NORMALIZED`
has none. The implementation transcribes this faithfully rather than
inventing one, and documents the gap in `vocab.py`.

## Implementation phases

This implementation was built in explicit phases, each frozen once
complete so later work builds strictly on top rather than reopening
earlier decisions:

1. **Final Report / Completion Contract** (`FinalReport`, the
   COMPLETE/COMPLETE-WITH-WARNINGS/BLOCKED/INCOMPLETE status machinery,
   `derive_overall_status_ceiling`, `STATUS_MASQUERADING`) — frozen.
2. **Wiki Page** (`WikiPage`, the closed 00–17 canonical index,
   `derive_wiki_header`, the two-layer `validate_wiki_page`/
   `validate_wiki_references` split) — frozen.
3. **Workspace export** (`arena_agent.export`, `ExportPlan` as a frozen
   manifest contract, `arena export`/`export validate`) — frozen.
4. **HTML presentation** (`arena_agent.html`, `arena html`) — frozen. See
   below.

## Design choices worth knowing about

- **No External Effect Contract (v2 §13) — disclosed scope decision.**
  This is a record-keeping / validation / reporting tool, not an execution
  engine: nothing in this codebase invokes an external effect on the
  agent's behalf, so §13's Proposal->...->Verification pipeline and its
  `HostInvoked(E) => DurableIssued(E)` durability invariant have no
  corresponding implementation here — there is no pipeline to specialize.
  This is a deliberate, disclosed scope boundary (conformance audit
  Recommendation R8), not a silent omission; see `arena_agent`'s package
  docstring for the full rationale. A caller that embeds this package
  inside a system which *does* invoke real external effects is
  responsible for enforcing §13 at that boundary itself.
- **Dataclasses, not Pydantic.** Keeps every validation rule explicit and
  readable in `validation.py` instead of hidden in a framework's model
  validators — matching the pack's own insistence on auditable, inspectable
  reasoning.
- **Validation returns findings, it doesn't raise on construction.** You
  can always build a record — even a knowingly-incomplete one while
  iteratively filling it in — but calling `validate_*` is a distinct,
  explicit step, mirroring the pack's separation of "data exists" from
  "data has been checked."
- **JSON workspace, one file per record.** Human-diffable, easy to put
  under version control, and directly comparable to the companion Markdown
  templates (`../templates/*.md`) which use the same one-file-per-record
  convention in prose form.
- **All dynamic text is markup-escaped before reaching Rich.** Rich's
  console markup parser treats a literal `[x]` (e.g. from a completion
  checklist) or a Python list repr like `['a', 'b']` as a style tag and
  silently drops it — the exact kind of silent information loss this pack
  forbids. Every renderer in `arena_agent.output` escapes first
  (`rich.markup.escape`), and `Output.table`/`findings` widen non-terminal
  console width and use `overflow="fold"` instead of Rich's default
  ellipsis truncation, so a long `ARENA-...` id is never silently cut off
  when output isn't attached to a real terminal (e.g. piped, redirected,
  or under a test runner).
