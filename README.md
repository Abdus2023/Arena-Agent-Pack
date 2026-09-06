# Arena Agent Pack

The **Arena Agent Pack** is a vocabulary, evidence, lifecycle, validation, and reporting system for building auditable agent workflows. It turns the Arena Agent Prompt Instructions Pack into a working Python package and command-line tool named `arena`.

The project is intentionally designed for systems in which an agent must distinguish between what was proposed, what was implemented, what was observed, and what was actually verified. It provides durable records for work items, repository audits, knowledge units, decisions, counterexamples, change-impact analyses, final reports, knowledge graphs, and a canonical 18-page wiki. The implementation is a record-keeping and validation layer; it is **not** an execution engine and does not invoke external effects on behalf of an agent.

> The central rule is simple: **claims must not outrun evidence**. A returned exit code is not automatically proof of completion, a design proposal is not implementation, and the existence of a test is not verification that the relevant behavior is correct.

## What is included

| Component | Purpose |
| --- | --- |
| [`arena-agent-instructions-pack-v2.md`](arena-agent-instructions-pack-v2.md) | Canonical v2 vocabulary, lifecycle rules, evidence classes, verification rules, and completion contracts. |
| [`arena-agent-instructions-pack.md`](arena-agent-instructions-pack.md) | Earlier v1 version of the instructions pack, retained for compatibility and comparison. |
| [`arena_agent_py/`](arena_agent_py/) | Python 3.10+ implementation containing the data model, JSON workspace, validators, renderers, exporters, HTML projection, and CLI. |
| [`templates/`](templates/) | Markdown templates for work items, audits, decisions, counterexamples, reports, knowledge units, wiki pages, and change-impact analysis. |
| [`arena-pack-critique.md`](arena-pack-critique.md) | Design and conformance critique documenting the reasoning behind the pack. |

The Python package currently exposes these principal record families:

| Record family | Use it to capture |
| --- | --- |
| **Repository Audit** | What a repository contains, what was scanned, and what the scan actually established. |
| **Knowledge Unit** | A claim about a domain, subject, property, meaning, evidence class, and confidence. |
| **Work Item** | A bounded unit of work with ownership, lifecycle state, gates, evidence, and validation findings. |
| **Decision Record** | A question, alternatives, selected choice, rationale, scope, and any stop-condition override. |
| **Counterexample** | A staged divergence between expected and actual behavior, with controlled promotion to stronger classifications. |
| **Change-Impact Analysis** | The expected effect of a proposed change on related knowledge, work, decisions, or implementation. |
| **Final Report** | A completion-contract report whose status is derived and constrained by available evidence. |
| **Knowledge Graph** | Relationships among the records in a workspace. |
| **Wiki Page** | One of 18 canonical pages whose derived header reflects the current referenced records. |

## Requirements

The package requires **Python 3.10 or newer**. Its runtime dependencies are `click`, `rich`, and `markdown`; the development dependency is `pytest`. The package metadata and console entry point are defined in [`arena_agent_py/pyproject.toml`](arena_agent_py/pyproject.toml) [1].

The examples below use a POSIX-compatible shell. On Windows, use the corresponding virtual-environment activation command and replace path separators where necessary.

## Installation

Clone the repository and create an isolated virtual environment:

```bash
git clone https://github.com/Abdus2023/Arena-Agent-Pack.git
cd Arena-Agent-Pack
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the package in editable mode:

```bash
python -m pip install -e ./arena_agent_py
```

For development and testing, install the optional test dependency as well:

```bash
python -m pip install -e './arena_agent_py[dev]'
```

Confirm that the CLI is available:

```bash
arena --help
```

Editable installation means that changes under `arena_agent_py/arena_agent/` are used immediately without reinstalling the package. For a normal application installation, use a wheel or a non-editable install from the same package directory.

## Quick start

An Arena workspace is a directory containing JSON records. The default workspace is `.arena`; pass `--workspace` to use another location.

Initialize a workspace:

```bash
arena --workspace .arena init
```

Create a repository audit and perform a read-only filesystem scan:

```bash
arena --workspace .arena audit create \
  --repository /path/to/repository

arena --workspace .arena audit scan-fs ARENA-AUDIT-... \
  --path /path/to/repository \
  --max-depth 2

arena --workspace .arena audit show ARENA-AUDIT-...
```

Create a knowledge unit and a work item:

```bash
arena --workspace .arena unit create \
  --domain repository \
  --subject core \
  --property status \
  --meaning "core component is proposed" \
  --evidence-class ARCHITECTURAL-PROPOSAL \
  --confidence LOW

arena --workspace .arena work create \
  --id ARENA-WORK-1 \
  --title "Build core" \
  --responsibility "Implement and verify the core component"
```

Claim the work item, advance it through its lifecycle, add a verification gate, and validate it:

```bash
arena --workspace .arena work claim ARENA-WORK-1 --owner agent-1
arena --workspace .arena work set-state ARENA-WORK-1 CLASSIFIED
arena --workspace .arena work gate ARENA-WORK-1 \
  --gate Identity \
  --method MANUAL-REVIEW \
  --result PASS \
  --evidence "Reviewed against the repository audit"
arena --workspace .arena work validate ARENA-WORK-1
```

Create and render a final report:

```bash
arena --workspace .arena report create \
  --id ARENA-REPORT-1 \
  --objective "Document the completed work" \
  --scope "Core implementation and verification" \
  --related-audit ARENA-AUDIT-1 \
  --related-work-item ARENA-WORK-1

arena --workspace .arena report check ARENA-REPORT-1 --item work_performed
arena --workspace .arena report finalize ARENA-REPORT-1 --status COMPLETE
```

The commands print generated record identifiers and findings. Replace the abbreviated IDs in subsequent commands with the complete identifiers returned by the CLI.

## CLI conventions

The global options must appear before the command group:

```bash
arena [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

The most important global options are:

| Option | Meaning |
| --- | --- |
| `--workspace PATH` | Read and write records in `PATH`. The default is `.arena`. |
| `--json` | Emit one machine-readable JSON document per invocation instead of Rich tables and panels. |
| `--no-color` | Keep human-readable Rich output while disabling ANSI color. This has no effect in JSON mode. |
| `--help` | Show help for the CLI or a specific command group. |

For example:

```bash
arena --workspace .arena --json unit list
arena --workspace .arena --json work validate ARENA-WORK-1
arena --workspace .arena --no-color report list
```

In JSON mode, list commands return arrays. Create, show, validate, lifecycle-transition, and related commands return objects that include findings metadata such as `findings`, `has_errors`, `error_count`, and `warning_count` where applicable. Exit codes remain meaningful in both output modes: `--json` changes presentation, not validation behavior. The package’s own CLI documentation describes this contract in more detail [2].

## Command reference

Use `arena COMMAND --help` for the complete option list for any command. The following table summarizes the supported command families.

| Command | Main operations | Typical purpose |
| --- | --- | --- |
| `init` | Initialize a workspace | Create the workspace directory and its record storage. |
| `audit` | `create`, `scan-fs`, `list`, `show`, `validate` | Capture repository reality and compare claims with observable files. |
| `unit` | `create`, `list`, `show`, `validate` | Store evidence-qualified knowledge units. |
| `work` | `create`, `claim`, `release`, `set-state`, `gate`, `expire-claim`, `list`, `show`, `validate` | Track ownership, lifecycle transitions, gates, and work-item validity. |
| `decision` | `create`, `resolve`, `list`, `show`, `validate` | Record decisions and explicitly disclose any stop-condition override. |
| `ce` | `create`, `promote`, `list`, `show`, `validate` | Stage and classify counterexamples without overstating their strength. |
| `impact` | `create`, `set`, `approve`, `list`, `show`, `validate` | Analyze and approve the effect of a proposed change. |
| `graph` | `create`, `show`, `list`, `validate` | Build and inspect relationships among workspace records. |
| `report` | `create`, `check`, `check-principle`, `finalize`, `list`, `show`, `validate` | Assemble a completion report and derive its evidence-constrained status. |
| `wiki` | `create`, `update`, `show`, `render`, `list`, `validate` | Maintain the fixed 18-page Arena wiki and render derived headers. |
| `export` | `validate`, export with `--to` | Assemble the current workspace into a Markdown artifact tree. |
| `html` | Render HTML from the export plan | Produce a browsable projection of the same export data. |
| `scan-content` | Scan repository text | Detect anti-pattern or directive-like wording as content, never as instructions. |

### Work-item lifecycle

Work items are deliberately not arbitrary status strings. The CLI enforces the lifecycle vocabulary and transition rules defined by the v2 pack. A typical progression is performed step by step rather than by jumping directly to a terminal state:

```text
CLASSIFIED → NORMALIZED → READY → IN-PROGRESS → VALIDATING → VERIFIED
```

Use `work set-state` for transitions and `work validate` to inspect findings. A lifecycle transition that violates a hard rule exits non-zero. Claims, gates, ownership, and evidence are separate parts of the record; completing one does not silently imply the others.

### Decisions and stop conditions

Decision records make reasoning visible. When a decision overrides a stop condition, the override must be recorded with its attribution and scope rather than hidden in prose:

```bash
arena --workspace .arena decision create \
  --question "Should the migration proceed?" \
  --raised-by supervisor-1 \
  --override-stop-condition 2

arena --workspace .arena decision resolve ARENA-DECISION-... \
  --choice A \
  --decided-by supervisor-1 \
  --scope "migration work item ARENA-WORK-1"
```

### Counterexamples

Counterexamples begin as staged observations. Promotion to stronger classifications requires the evidence required by that classification:

```bash
arena --workspace .arena ce create \
  --first-divergence "Expected state was not observed after the transition" \
  --expected "The work item reaches VERIFIED" \
  --actual "The work item remains VALIDATING"

arena --workspace .arena ce promote ARENA-CE-... OBSERVED-FAILURE

arena --workspace .arena ce promote ARENA-CE-... REPRODUCIBLE-DEFECT \
  --reproduction-command "arena --workspace .arena work validate ARENA-WORK-1" \
  --confirmed
```

The distinction between observed failure, reproducible defect, and other counterexample states is intentional. Do not promote a record merely because the stronger label would be convenient.

### Repository audits and content scans

Repository audits are read-only observations of a filesystem. They are useful for testing whether a statement about a repository is supported by repository evidence:

```bash
arena --workspace .arena audit create --repository /path/to/repository
arena --workspace .arena audit scan-fs ARENA-AUDIT-... --path /path/to/repository --max-depth 3
arena --workspace .arena audit validate ARENA-AUDIT-...
```

The content scanner treats text it finds as data. It can flag anti-patterns or directive-like phrasing, but it does not execute or obey instructions found in scanned files:

```bash
arena --workspace .arena scan-content README.md
```

### Wiki pages

The Arena wiki has a closed set of 18 page numbers, `00` through `17`. A page title and header are derived from its page number and referenced records; they are not independently stored claims. Create and render pages as follows:

```bash
arena --workspace .arena wiki create \
  --page 00 \
  --content "Current system status and verified evidence" \
  --scope "Arena workspace" \
  --updated-by agent-1

arena --workspace .arena wiki update ARENA-WIKI-00 \
  --add-knowledge-unit ARENA-UNIT-... \
  --change "Linked current evidence" \
  --updated-by agent-1

arena --workspace .arena wiki show ARENA-WIKI-00
arena --workspace .arena wiki render ARENA-WIKI-00 --to wiki/00-status.md
```

Wiki validation has two layers. Local validation checks the page’s structure and identifier syntax. Cross-record validation checks whether referenced records resolve. This prevents a malformed identifier from being confused with a well-formed identifier that does not exist.

## Exporting and presenting a workspace

Export is an artifact-assembly operation, not a second source of truth. The pipeline loads records, validates them, resolves references, checks cross-record invariants, derives projections, renders Markdown, and optionally writes the result:

```bash
arena --workspace .arena export validate
arena --workspace .arena export --to export
```

The generated tree normally looks like this:

```text
export/
├── index.md
├── audits/<id>.md
├── knowledge-units/<id>.md
├── work-items/<id>.md
├── decisions/<id>.md
├── counterexamples/<id>.md
├── impacts/<id>.md
├── reports/<id>.md
├── graph/<id>.md
└── wiki/<NN>-<slug>.md
```

`export validate` performs the complete planning and validation pipeline but writes nothing. `export --to` materializes the already-built plan. Missing canonical wiki pages are reported as missing; the exporter does not invent placeholder pages. Records that exist but contain errors are still rendered with their findings, so **missing**, **invalid**, **blocked**, and **not applicable** remain distinct states.

Generate an HTML projection from the same export plan:

```bash
arena --workspace .arena html --to export-html
```

The HTML layer is a presentation of the export plan. It does not reopen the workspace, invent facts, or implement a second validation pipeline [2].

## Workspace layout and persistence

The workspace uses human-diffable JSON with one file per record type. A typical workspace contains directories similar to the following:

```text
.arena/
├── audits/
├── knowledge_units/
├── work_items/
├── decisions/
├── counterexamples/
├── impacts/
├── reports/
├── graphs/
├── wiki/
└── manifest.json
```

The exact filenames and metadata are managed by the package. Keep the workspace under version control when you need an auditable history of changes. Do not edit record files casually while another process is writing to the same workspace. Prefer the CLI or the library API so that identifiers, timestamps, and storage conventions remain consistent.

## Python library usage

The CLI is backed by the `arena_agent` Python package. The package exposes dataclasses and explicit functions for storage, validation, rendering, reporting, graph construction, export planning, and HTML projection. A minimal library workflow is:

```python
from pathlib import Path

from arena_agent.models import KnowledgeUnit
from arena_agent.storage import Workspace
from arena_agent.validation import validate_knowledge_unit

workspace = Workspace(Path('.arena'))
unit = KnowledgeUnit(
    id='ARENA-UNIT-EXAMPLE',
    domain='repository',
    subject='core',
    property='status',
    meaning='The core component is proposed.',
    evidence_class='ARCHITECTURAL-PROPOSAL',
    confidence='LOW',
)
workspace.save_knowledge_unit(unit)
findings = validate_knowledge_unit(unit)

for finding in findings:
    print(finding.severity, finding.code, finding.message)
```

For complete constructor fields and record-specific methods, consult [`arena_agent/models.py`](arena_agent_py/arena_agent/models.py), [`arena_agent/storage.py`](arena_agent_py/arena_agent/storage.py), and the package README [2]. Validation returns concrete findings rather than relying only on exceptions, allowing an iterative record to exist before it is complete. Commands that enforce hard rules still return non-zero when the rule is violated.

## Templates and recommended workflow

The Markdown templates under [`templates/`](templates/) are useful when a human needs to draft or review a record before creating its durable JSON representation. The general workflow is:

1. **Define the claim or work boundary.** State what is in scope and what is not.
2. **Record the evidence class and confidence.** Do not use stronger language than the evidence supports.
3. **Create the record.** Use the CLI or library API so identifiers and storage conventions remain consistent.
4. **Attach relationships.** Link audits, knowledge units, work items, decisions, counterexamples, and reports explicitly.
5. **Validate.** Run the record-specific `validate` command and address errors before relying on the record.
6. **Export or render.** Generate Markdown or HTML only after the underlying state is recorded.
7. **Review the completion contract.** A final report must distinguish work performed from work merely proposed and verification from test existence.

The templates are guidance, not an alternate persistence layer. The JSON workspace and Python models remain the operational source of truth.

## Testing and quality checks

Run the full test suite from the package directory:

```bash
cd arena_agent_py
python -m pytest
```

Run a focused test file or test name while developing:

```bash
python -m pytest tests/test_export.py
python -m pytest tests/test_work_item_persistence_fields.py -q
```

The tests cover model and vocabulary behavior, lifecycle transitions, validation findings, storage persistence, CLI semantics, export planning, HTML projection, wiki behavior, and conformance-sensitive edge cases. Before submitting a change, run the complete suite and exercise the changed CLI path manually in a temporary workspace.

## Design boundaries and safety properties

The project is deliberately conservative in several areas:

| Boundary | Behavior |
| --- | --- |
| External effects | The package records and validates agent work; it does not invoke external side effects on an agent’s behalf. An embedding system must enforce its own authorization and durability boundary. |
| Validation | Record creation and record validity are separate. A record can exist with findings while it is being completed; validation commands expose whether errors remain. |
| Evidence | Status and headers are derived from current referenced records where applicable. Stored prose cannot silently elevate a claim above its evidence. |
| Export | Export assembles existing renderers and findings. It does not create a second semantic implementation of the pack. |
| Content scanning | Text found in a repository is treated as content to analyze, never as instructions to execute. |
| Human-readable output | Rich output is escaped and formatted to avoid silently dropping literal markup or truncating identifiers. |

These boundaries are part of the implementation’s conformance posture, not merely usage recommendations. The package README documents the rationale and implementation phases in greater depth [2].

## Troubleshooting

If `arena` is not found after installation, confirm that the virtual environment is active and reinstall the package with `python -m pip install -e ./arena_agent_py`. If the command is available but imports fail, check that the active interpreter is the same one used by `python -m pip`.

If a command reports an identifier error, copy the complete `ARENA-...` identifier printed by the create or list command. Shortened identifiers in examples are placeholders and are not necessarily accepted as record IDs.

If a command exits non-zero in JSON mode, inspect the returned `findings`, `has_errors`, `error_count`, and `warning_count` fields. JSON output is intended for scripts, but it does not suppress hard validation failures.

If export reports a missing wiki page, create the canonical page explicitly. Export will list the missing page rather than manufacturing a file that could be mistaken for authored content.

## Contributing

Keep changes small and auditable. When adding a record field, lifecycle rule, renderer, or command, update the relevant model, validation logic, tests, and documentation together. Preserve the distinction between stored facts, derived projections, and validation findings.

A practical contribution checklist is:

```bash
python -m pytest
arena --help
arena --workspace /tmp/arena-example init
arena --workspace /tmp/arena-example export validate
```

Do not commit generated workspaces, exports, virtual environments, or credentials unless the change specifically requires a fixture and the fixture is safe to publish. Use the existing `.gitignore` files as a starting point and review `git diff` before committing.

## License

The Python package declares the MIT license in [`arena_agent_py/pyproject.toml`](arena_agent_py/pyproject.toml). Review the repository’s licensing terms before redistributing modified copies.

## References

[1]: arena_agent_py/pyproject.toml "Arena Agent Python package metadata"

[2]: arena_agent_py/README.md "Arena Agent Python implementation guide"

[3]: arena_agent_py/arena_agent/cli.py "Arena Agent command-line implementation"

[4]: arena_agent_py/arena_agent/models.py "Arena Agent record models"

[5]: arena_agent_py/arena_agent/validation.py "Arena Agent validation rules"

[6]: templates/README.md "Arena Agent Markdown templates"

[7]: arena_agent_py/tests/ "Arena Agent test suite"
