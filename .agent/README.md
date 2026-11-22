# Arena Agent Pack — Reusable Agent Workspace

This `.agent/` workspace exposes the Arena Agent Pack's repeatable evidence, audit, decision, lifecycle, and publication procedures as composable skills. The Python package remains the computational implementation and source of truth for its CLI behavior.

## Skills
- [skill-creator](skills/skill-creator/SKILL.md)
- [arena-evidence-governance](skills/arena-evidence-governance/SKILL.md)
- [arena-repository-audit-and-knowledge](skills/arena-repository-audit-and-knowledge/SKILL.md)
- [arena-workspace-publication](skills/arena-workspace-publication/SKILL.md)

## Workflow
- [Evidence-governed repository-to-publication workflow](workflows/arena-evidence-to-publication.md)

## Computational tools
- [validate_skill.py](tools/validate_skill.py) — structural skill lint only.
- [test_validate_skill.py](tests/test_validate_skill.py) — validator tests.
- [Arena Python package and CLI](../arena_agent_py/README.md) — the actual record models, validators, persistence, export and rendering implementation.

## Governing rule
Claims must not outrun evidence. Arena records and validates work; it does not execute external effects or authorize an embedding system to do so.

Run:
```sh
python3 .agent/tools/validate_skill.py .agent/skills
python3 -m unittest discover -s .agent/tests -v
```
