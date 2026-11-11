---
name: openclaw-verifiable-plugin-graph
description: Design and audit OpenClaw plugins as explicitly constructed, dependency-checked runtime graphs with observable lifecycle and activation evidence.
---

# OpenClaw Verifiable Plugin Graph

## Purpose

Model a plugin as a declared component in a constructed runtime graph, not merely a dynamically imported module. Make identity, dependencies, capabilities, activation, and failure observable and testable.

## Activation

Use when designing, integrating, auditing, or debugging OpenClaw plugins, plugin loaders, activation planners, manifests, registration, or runtime lifecycle.

Do not use this skill to assert current OpenClaw implementation details without checking the exact source revision. Treat supplied architecture notes as research inputs until independently verified.

## Inputs and preconditions

- OpenClaw repository URL and exact commit/ref.
- Plugin manifest, entrypoint, config schema, declared capabilities, and dependencies.
- Host runtime APIs and supported SDK subpaths.
- Activation triggers and intended plugin surfaces.
- Security policy, filesystem trust boundary, and permission model.
- Required lifecycle, diagnostics, and conformance tests.

## Procedure

1. Pin the OpenClaw revision and inspect the actual loader, manifest parser, discovery, activation planner, registry, and lifecycle code.
2. Separate metadata/control-plane discovery from runtime/data-plane loading.
3. Define each plugin node with stable ID, version, origin, entrypoint, manifest digest, declared surfaces, dependencies, capabilities, permissions, and config contract.
4. Define typed edges: depends-on, activates-after, owns-surface, provides-capability, requires-capability, and lifecycle-order.
5. Validate unique identities, dependency resolution, version compatibility, permission policy, entrypoint containment, and graph acyclicity before import.
6. Produce a deterministic activation plan from explicit triggers and declared ownership. Empty or unresolved scope MUST NOT widen to load-all.
7. Track distinct states: DISCOVERED, MANIFEST_VALIDATED, PLANNED, LOADING, IMPORTED, REGISTERING, REGISTERED, ACTIVATING, ACTIVE, FAILED, STOPPING, STOPPED. Define legal transitions and terminal failure behavior.
8. Treat import success, registry insertion, and activation success as different events. Require a host-observable activation receipt or equivalent evidence before marking ACTIVE.
9. Make partial registration rollback or quarantine behavior explicit. Never leave a half-registered plugin silently usable.
10. Bound startup work, concurrency, retries, and diagnostics. Preserve the first failure cause and plugin identity.
11. Test malformed manifests, missing dependencies, cycles, duplicate IDs, path escape, untrusted ownership/permissions, import failure, registration failure, activation failure, shutdown failure, and empty activation scope.
12. Compare the graph plan with actual runtime events and record mismatches as counterexamples.

## Outputs

- Plugin node/edge model.
- Manifest and capability contract.
- Deterministic activation plan.
- Lifecycle state machine and transition table.
- Security and failure policy.
- Conformance test matrix and evidence ledger.

## Failure handling

Fail closed on invalid identity, unresolved required dependency, dependency cycle, entrypoint escape, denied permission, invalid configuration, or failed activation. Do not label a plugin ACTIVE based only on discovery, import, or registration.

## Acceptance criteria

- Every plugin has a stable identity and declared contract.
- Every dependency and capability edge resolves.
- Graph validation rejects cycles and duplicate identities.
- Activation plan is deterministic and does not broaden empty scope.
- Registration and activation are independently observable.
- Failure paths preserve plugin identity and causal diagnostics.
- Runtime claims are pinned to a source revision and tested behavior.
