# HARĒNA — Reusable Agent Engineering Substrate

HARĒNA is the conceptual identity of the reusable agent infrastructure. The directory name remains .agent for compatibility. ARENA remains the overarching evidence, lifecycle, and engineering discipline.

This package is an instruction/tool/workflow layer. It is not an agent runtime and does not automatically execute skills. Runtime discovery and invocation must be tested in each target agent environment.

## Architecture

| Layer | Responsibility |
|---|---|
| Skills | Reusable procedures, constraints, and acceptance criteria |
| Tools | Deterministic local computation and validation |
| Workflows | Declarative DAGs composing skills and tools |
| Schemas | Machine-readable contracts for workflow/evidence records |
| Tests | Regression checks for helper behavior and boundary cases |
| References | Provenance register for source candidates |
| .arena | Separate durable records, audits, work items, decisions, counterexamples, and reports |

## Skills

| Skill | Purpose |
|---|---|
| [skill-creator](skills/skill-creator/SKILL.md) | Create, validate, compose, register, and release skills |
| [continuity-and-process-extraction](skills/continuity-and-process-extraction/SKILL.md) | Resume work and extract durable processes without skipping phases |
| [github-research-to-project](skills/github-research-to-project/SKILL.md) | Convert repository research into a provenance-aware project |
| [source-intelligence-audit](skills/source-intelligence-audit/SKILL.md) | Audit provenance, licensing, buildability, maintenance, and security |
| [repository-bootstrap](skills/repository-bootstrap/SKILL.md) | Safely establish repository foundations and persist artifacts |
| [arena-evidence-workspace](skills/arena-evidence-workspace/SKILL.md) | Use the Arena CLI for durable evidence and lifecycle records |
| [plugin-ecosystem-forensics](skills/plugin-ecosystem-forensics/SKILL.md) | Audit plugin ecosystems, loaders, vendor trees, and candidate repositories |
| [openclaw-verifiable-plugin-graph](skills/openclaw-verifiable-plugin-graph/SKILL.md) | Model plugins as explicit, validated runtime graphs |
| [framework-agnostic-runtime-adapters](skills/framework-agnostic-runtime-adapters/SKILL.md) | Define host-neutral adapter ports, lifecycle, and conformance |
| [cordis-openclaw-composition](skills/cordis-openclaw-composition/SKILL.md) | Contain Cordis composition within an OpenClaw plugin boundary |
| [foxhole-radio-experimental-lab](skills/foxhole-radio-experimental-lab/SKILL.md) | Run reproducible passive RF detector experiments |

## Composable workflows

- [Repository forensics](workflows/repository-forensics.json)
- [OpenClaw runtime composition](workflows/openclaw-runtime-composition.json)
- [Foxhole radio lab](workflows/foxhole-radio-lab.json)

Workflow manifests declare dependencies; they do not execute their steps.

## Computational tools

- [validate_skill.py](tools/validate_skill.py) — structural lint for skill identity and required headings.
- [compose_workflow.py](tools/compose_workflow.py) — validates skill/tool references and topologically orders a workflow DAG; does not execute it.
- [validate_evidence_ledger.py](tools/validate_evidence_ledger.py) — checks source/claim references and evidence requirements; does not verify claim truth.
- [foxhole_rf_calc.py](tools/foxhole_rf_calc.py) — idealized LC, Q-bandwidth, thermal-noise, dBm, and rectification-ratio calculations.

## Schemas and references

- [Workflow schema](schemas/workflow.schema.json)
- [Evidence ledger schema](schemas/evidence-ledger.schema.json)
- [Source register](references/source-register.md)
- [Skill engineering standard](standards/skill-engineering-standard-v1.md)

## Continuous integration

The branch includes [.github/workflows/agent-package-validation.yml](../.github/workflows/agent-package-validation.yml), configured to run structural skill checks, workflow composition checks, JSON parsing, and helper tests on Python 3.10, 3.11, and 3.12. A workflow file being present does not prove that a run has completed; inspect the GitHub Actions result for the relevant commit.

## Validation commands

Run from repository root with Python 3.10+:

    python3 .agent/tools/validate_skill.py .agent/skills
    python3 .agent/tools/compose_workflow.py .agent/workflows/repository-forensics.json
    python3 .agent/tools/compose_workflow.py .agent/workflows/openclaw-runtime-composition.json
    python3 .agent/tools/compose_workflow.py .agent/workflows/foxhole-radio-lab.json
    python3 -m unittest discover -s .agent/tests -v

The existing arena CLI remains the record-keeping and validation layer for project audits, work items, decisions, counterexamples, gates, reports, and exports. Do not duplicate its data model in ad hoc files; link tool outputs and test artifacts into Arena records where practical.

## Evidence and status rules

- PROVED / ARGUMENT / CONJECTURE / OPEN classify claims.
- VERIFIED / PARTIALLY_VERIFIED / PROVISIONAL / BLOCKED classify verification.
- AUTHORING_COMPLETE, STRUCTURE_VALIDATED, STATIC_CHECKED, HELPER_TESTED, WORKFLOW_TESTED, RUNTIME_CONFORMANT, and PERSISTENCE_VERIFIED are reported independently.
- A successful GitHub fetch proves persistence only.
- A planned workflow is not an executed workflow.
- A passing helper test proves only the behavior exercised by that test.

## Project boundaries

See the source register. KARTAGO, THUGGA, OpenClaw/Cordis, and FOXHOLE LAB remain distinct projects. This shared substrate does not merge their implementation repositories or security boundaries. Android/ADB-specific skills and Galaxy A06 tools remain in [KARTAGO's own .agent workspace](https://github.com/Abdus2023/KARTAGO/tree/arena/galaxy-a06-forensic-debloat/.agent); they are intentionally not duplicated here.
