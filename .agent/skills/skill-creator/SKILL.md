---
name: skill-creator
description: Extract, design, compose, validate, register, and release reusable skills and computational workflows under the HARĒNA standard.
---

# Skill Creator

## Purpose

Create maintainable, portable, testable skills from repeatable workflows, technical domains, verified knowledge, and prior project work. This meta-skill governs authoring quality; it does not establish the truth of domain claims.

## Activation

Use when extracting processes from conversations, repositories, files, tool traces, or operator decisions; creating or revising skills; composing workflows; adding deterministic helpers; registering packages; or preparing releases.

Do not use it as a substitute for domain, legal, security, hardware, or runtime integration review. Do not create a skill for a one-off answer with no reusable procedure.

## Inputs and preconditions

Identify:
- Objective and domain.
- Source conversations, files, repositories, commands, and tool results available.
- Intended agents and target runtimes.
- Target repository, branch, and write permissions.
- Existing skills, tools, workflows, schemas, and standards.
- Required permissions, safety boundaries, outputs, and acceptance criteria.
- Unknowns and unavailable evidence.

Ask one focused question only when a missing decision prevents safe, non-destructive progress. Otherwise state assumptions and preserve project boundaries.

## Procedure

1. **Reconstruct sources.** Retrieve the relevant process from available context and files. Inspect repository state before editing. Do not assume prior summaries are complete.
2. **Classify evidence.** Separate performed actions, observed outputs, proposals, examples, inferred improvements, and untested hypotheses.
3. **Decompose.** Extract triggers, exclusions, inputs, preconditions, steps, branches, failure paths, state transitions, outputs, handoffs, and evidence.
4. **Choose the artifact type.** Use a skill for repeatable instructions; a tool for deterministic computation or validation; a workflow for composing multiple skills/tools; a schema for machine-checkable data contracts; a report for historical evidence.
5. **Define contracts.** State purpose, activation, dependencies, input/output shapes, permissions, safety constraints, acceptance tests, and stop conditions.
6. **Check boundaries and overlap.** Reuse existing skills where possible. Split unrelated projects and domains. Do not collapse KARTAGO, THUGGA, OpenClaw/Cordis, and FOXHOLE LAB into one implementation.
7. **Author focused packages.** Keep `SKILL.md` concise and independently usable. Put detailed references, schemas, workflow manifests, and examples in adjacent files.
8. **Add computational helpers selectively.** Require deterministic behavior, safe defaults, bounded execution, standard-library preference, documented units, and tests. Never disguise a plan generator or validator as an execution engine.
9. **Compose workflows.** Declare steps and dependencies in a machine-readable DAG. Validate references, missing dependencies, duplicate IDs, and cycles before reporting a plan.
10. **Validate.** Check frontmatter, name/directory match, required sections, local links, schemas, helper tests, and workflow manifests. Report each validation level independently.
11. **Exercise controlled examples.** Run representative positive, negative, malformed, and boundary cases where tools are available. Record exact commands and results.
12. **Check runtime discovery separately.** Test discovery and invocation in each target runtime. Never assume `.agent` auto-load behavior.
13. **Register and persist.** Update `.agent/README.md`; inspect existing paths; use current blob SHAs for updates; fetch every changed file back.
14. **Report honestly.** Distinguish authored, structurally validated, helper tested, workflow tested, runtime conformant, and persistence verified. List gaps and operator actions.

## Outputs

- A source/process inventory with provenance and evidence classifications.
- Focused skill packages.
- Deterministic tools, tests, and schemas where justified.
- Composable workflow manifests.
- Updated skill/workflow index.
- Validation and persistence report with exact revision and unresolved gaps.

## Failure handling

Stop or mark BLOCKED if repository identity/write permission is ambiguous, an overwrite cannot be reconciled, essential source material is unavailable, a project boundary would be violated, or legal/security constraints block the intended use. Preserve partial work and identify the exact blocked gate.

## Acceptance criteria

- Every artifact has a narrow, explicit purpose.
- Performed actions are not conflated with proposals or examples.
- Skills have valid frontmatter, clear triggers, inputs, procedure, outputs, failure handling, and acceptance criteria.
- Workflow dependencies form a valid DAG and resolve to existing skills/tools.
- Helpers have normal, malformed, and boundary tests.
- Existing skills are reused or overlap is justified.
- Runtime discovery is tested or marked NOT_RUN.
- Every changed repository file is fetched back and checked.
- No unsupported domain or implementation claim is promoted to VERIFIED.

## Governing standard

Follow `.agent/standards/skill-engineering-standard-v1.md`. If the standard is unavailable in another repository, apply these requirements and report the standard document as unavailable.
