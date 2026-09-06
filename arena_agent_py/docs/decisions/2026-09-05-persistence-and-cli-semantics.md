# Architecture & Process Decisions — Persistence, Validation Flow, and CLI Semantics

**Date:** 2026-09-05
**Status:** Accepted
**Scope:** `arena_agent_py/` — record persistence, validation flow, and CLI command semantics.

This document captures a set of architecture and process decisions made
during a clarification pass on the Arena Agent Python implementation. It
exists so the reasoning behind these choices doesn't have to be
re-derived later, and so future changes are checked against it rather
than silently drifting away from it.

---

## 1. Persistence: JSON files on disk (one file per record)

**Decision:** JSON files on disk, one record per file. Not SQLite, not
in-memory-only.

### Why JSON

- **Human-diffable** — changes are visible in Git.
- **One record per file** — easy to inspect, move, review, and version.
- **Portable** — no database server or migration machinery.
- **Works naturally with the CLI.**
- **Supports provenance** — each record can carry IDs, timestamps,
  sources, validation metadata, and relationships.
- **Repository-friendly** — the records themselves can live alongside the
  project they describe.

This fits the project's nature: the records are **knowledge/governance
artifacts**, not merely runtime state.

### Recommended structure (reference shape)

```
.records/
├── knowledge-units/
│   ├── KU-000001.json
│   └── KU-000002.json
├── work-items/
│   ├── WI-000001.json
│   └── WI-000002.json
├── decisions/
│   └── DR-000001.json
├── gates/
│   └── GT-000001.json
├── stop-conditions/
│   └── SC-000001.json
└── repo-audits/
    └── RA-000001.json
```

(The implementation's actual on-disk layout — `.arena/knowledge_units/`,
`work_items/`, `decisions/`, `counterexamples/`, `repo_audits/`,
`change_impact/`, `final_reports/`, `graphs/` — follows this same
one-file-per-record principle; naming was adapted to match the record
types actually defined in the pack.)

### Not SQLite, not yet

Don't choose SQLite yet. The dependency-graph/query requirements that
would justify it can be added later, once real records demonstrate that
filesystem scanning is genuinely insufficient — not before.

### Layering: models must not depend on the filesystem

```
Structured record models (domain objects)
        ↓
Repository / Store interface
        ↓
JSON File Store
```

So a future backend swap doesn't touch the domain models:

```
                    ┌─ JSON File Store
Structured Models ──┼─ SQLite Store
                    └─ API / remote Store
```

**JSON is the initial persistence implementation, not a permanent
architectural constraint.**

---

## 2. Work sequencing: persistence + validation foundation before CLI polish

**Decision:** Prioritize the persistence + validation + core CLI
(`create`, `get/list`, `validate`) foundation over CLI polish or
reporting features.

Suggested build order:

```
Structured record models
        ↓
Validation rules
        ↓
JSON RecordStore
        ↓
CLI
 ├── create
 ├── get/list
 └── validate
        ↓
Tests
```

Only after that foundation is solid should the following be tackled, in
this relative order:

1. Markdown reports
2. Shell completion / config
3. Progress indicators
4. HTML export
5. Automated repository inspection

**Rationale:** this keeps the CLI from becoming a collection of UX
features sitting on top of an undefined persistence/semantic layer.

---

## 3. Domain models: keep plain dataclasses, do not migrate to Pydantic

**Decision:** Keep dataclasses. The mention of "Pydantic models" in
decision #2 was shorthand for **structured record models** in general,
not a literal instruction to adopt Pydantic — and the earlier
dataclass-based design is the better fit for this project.

Layering:

```
models.py
        ↓  (plain dataclasses)
validation.py
        ↓  (explicit schema + business invariants)
json_store.py
        ↓
CLI
```

### Why dataclasses over Pydantic here

- Dataclasses remain simple domain objects.
- `validation.py` is the **authoritative** place for validation rules.
- Validation logic stays explicit and inspectable rather than being
  distributed across framework decorators.
- Persistence can serialize/deserialize the dataclasses without coupling
  the domain model to a validation framework.
- Tests can directly exercise individual validation rules.
- A future JSON/SQLite/API backend doesn't require changing the domain
  models.

### Revised task statement

> Implement the JSON-backed `RecordStore` around the existing dataclasses
> and `validation.py`, then wire `create`, `list`/`get`, and `validate`
> into the CLI. **Do not migrate the models to Pydantic.**

### No duplicated validation

Validation must not be duplicated across models, store, and CLI. The
canonical flow is:

```
CLI input
        ↓
deserialize → dataclass
        ↓
validation.py
        ↓
valid?
 ├─ no  → structured validation errors
 └─ yes → RecordStore.save()
```

This keeps domain representation, validation semantics, persistence, and
presentation cleanly separated.

---

## 4. Process: audit the existing implementation before adding more

**Decision:** Given that a store + validation + CLI implementation
already exists and is tested across all 8 record types, the next step
was an **audit/review pass**, not new feature work — explicitly avoiding
adding redundant functionality just because it was previously discussed
in the abstract.

### Audit checklist

1. **Schema fidelity** — every field and closed-set vocabulary matches
   the pack.
2. **Validation completeness** — especially cross-field/business
   invariants.
3. **Persistence correctness** — round-trip serialization, deterministic
   JSON, IDs, corruption/missing-record behavior.
4. **CLI semantics** — `create`, `list`, `show`, `validate`, exit codes,
   malformed input, missing records.
5. **Separation of concerns** — no validation duplicated in models,
   store, or CLI.
6. **Error quality** — actionable, deterministic errors suitable for both
   humans and scripts.
7. **Test coverage** — identify semantic gaps rather than merely counting
   tests.
8. **Repository reality** — verify the implementation actually matches
   the current repository, rather than relying on the earlier design
   discussion.

### Required output shape

A short audit verdict, one of:

```
PASS
PASS WITH HARDENING
NEEDS CORRECTION
```

with concrete findings and fixes.

**Only after that audit should the next feature phase be chosen**
(reports, shell ergonomics, progress indicators, HTML export, etc.),
based on what the audit actually reveals — not on a pre-existing feature
wishlist.

---

## 5. Create-time validation semantics: `create` always persists

**Decision:** Keep the existing behavior — `create` always persists the
record, even if validation reports errors. This corrects an earlier,
stricter flow diagram that implied `create` should reject-and-not-save on
any validation error; that diagram was wrong, not the implementation.

```
create
        ↓
persist draft/record
        ↓
validate
 ├─ INFO / WARNING → persist
 └─ ERROR          → persist, but record remains non-promotable
```

Lifecycle operations then enforce the hard boundary:

```
set-state
resolve
promote
approve
        ↓
validation gate
        ↓
ERROR → BLOCK
```

### Why

This supports the **iterative knowledge-building workflow**: a record can
exist while incomplete, be progressively enriched, and only become
operationally accepted once it satisfies the required invariants.

### Authoritative distinction (to be enforced as an explicit invariant)

- **Persistence** answers "does this record exist?"
- **Validation** answers "is this record currently valid?"
- **Lifecycle transitions** answer "is this record allowed to advance?"

This distinction is itself part of what the audit (§4) should check for —
i.e., that no code path conflates "saved" with "valid" or "valid" with
"allowed to advance."

---

## 6. CLI vocabulary: keep `show`, no `get` alias

**Decision:** Leave the read command named `show`. Do not add a `get`
alias.

```
arena unit show <id>
arena unit list
```

`show` naturally means "display this specific record," while `list`
means "display a collection." The mention of `get/list` in an earlier
sequencing diagram (§2) was descriptive shorthand, not a literal command
naming requirement.

Adding `get` purely to match that earlier diagram would create
unnecessary surface area and potentially duplicate documentation/tests
for no semantic gain.

### Authoritative CLI vocabulary

- `create` → persist a record, even if incomplete
- `show` → retrieve/display one record
- `list` → enumerate records
- `validate` → report validation status
- lifecycle commands (`set-state`, `resolve`, `promote`, `approve`, etc.)
  → enforce blocking validation gates

**No CLI rename or alias needed.**
