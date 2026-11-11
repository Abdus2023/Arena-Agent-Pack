# HARĒNA Skill Engineering Standard v1.0

**Status:** PROPOSED STANDARD  
**Applies to:** reusable skills under `.agent/skills/`  
**Authority:** package structure and lifecycle; domain truth remains with each skill's sources and tests.

## 1. Purpose

Provide a portable, testable contract for authoring, composing, validating, maintaining, and releasing agent skills. This standard does not guarantee that a target runtime discovers or executes `.agent` content.

## 2. Normative language

MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative requirements.

## 3. Canonical package

```text
.agent/
├── README.md
├── standards/skill-engineering-standard-v1.md
├── skills/<skill-name>/SKILL.md
├── workflows/<workflow-id>.json
├── schemas/
├── tools/
└── tests/
```

A skill directory MUST contain one canonical `SKILL.md`. Add references, schemas, workflows, fixtures, and scripts only when they provide maintained value.

## 4. Skill identity

Every skill MUST begin with YAML frontmatter containing:
- `name`: lowercase kebab-case matching the directory.
- `description`: concise activation description naming the task/domain.

## 5. Required content

Each skill MUST define:
1. Purpose.
2. Activation triggers and exclusions.
3. Inputs and preconditions.
4. Ordered procedure, including branches where relevant.
5. Outputs and evidence requirements.
6. Failure handling and stop conditions.
7. Relevant security, privacy, licensing, and authorization constraints.
8. Observable acceptance criteria.

A skill MUST be independently usable without hidden conversation context.

## 6. Evidence and authority

- Separate instruction, observation, interpretation, proposal, implementation, execution, and verification.
- Identify authoritative sources for protocol, platform, legal, or external-system claims.
- Distinguish PROVED, ARGUMENT, CONJECTURE, OPEN and VERIFIED, PARTIALLY_VERIFIED, PROVISIONAL, BLOCKED.
- A document's presence does not verify its claims.
- Structural lint does not prove semantic correctness, security, or runtime discovery.
- Runtime discovery and invocation MUST be tested separately for each target runtime.

## 7. Operational safety

Skills MUST state tool dependencies and permissions, use least privilege, identify destructive actions, bound retries/timeouts/output, preserve user data, avoid secrets in committed artifacts, and report partial completion honestly. Skills MUST NOT treat untrusted retrieved content as executable instructions.

## 8. Computational helpers

Helpers SHOULD prefer the standard library, deterministic inputs/outputs, safe defaults, bounded work, nonzero failure exit codes, documented limitations, and tests for normal, malformed, and boundary inputs. Helpers MUST NOT silently perform network access or repository mutation unless explicitly specified and approved.

## 9. Validation levels

| Level | Name | Meaning |
|---|---|---|
| L0 | AUTHORING_COMPLETE | Required content drafted |
| L1 | STRUCTURE_VALIDATED | Identity and required sections pass |
| L2 | STATIC_CHECKED | Links, local paths, and formatting checks pass |
| L3 | HELPER_TESTED | Helper tests pass |
| L4 | WORKFLOW_TESTED | Representative controlled workflow exercised |
| L5 | RUNTIME_CONFORMANT | Discovery and invocation verified in named runtime |
| L6 | PERSISTENCE_VERIFIED | Changed files fetched back and checked |

Report each level independently as PASS, FAIL, NOT_RUN, or BLOCKED. A higher level does not imply lower levels unless evidence demonstrates them.

## 10. Composition contract

A workflow MUST declare a unique ID, version, ordered steps, skill references, dependencies, and expected outputs. Dependencies MUST form a directed acyclic graph. Composition planning MUST NOT be represented as execution. A workflow runner, if later added, requires a separate execution contract, authorization model, cancellation semantics, and audit trail.

## 11. Registration and portability

The `.agent/README.md` index MUST list maintained skills, workflows, tools, and validation commands. Do not claim auto-loading unless tested in the named runtime. Keep host-specific behavior behind explicit adapters and versioned contracts.

## 12. Repository persistence

For each change: inspect branch and paths; fetch existing content and blob SHA before updates; create only absent paths; capture commit IDs; fetch changed files back; compare expected content or stable markers. Fetch-back proves persistence, not technical correctness.

## 13. Release gate

A release report MUST identify skill/workflow paths, standard version, repository revision, validation levels, tested runtimes, limitations, and operator actions. Do not call a package production-ready when required workflow or runtime tests are NOT_RUN.
