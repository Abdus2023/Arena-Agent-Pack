---
name: cordis-openclaw-composition
description: Integrate Cordis as a composition and lifecycle subsystem inside OpenClaw while preserving OpenClaw as the host authority.
---

# Cordis–OpenClaw Composition

## Purpose

Design a Cordis-powered composition plugin for OpenClaw. Cordis supplies context composition, dependency management, and lifecycle coordination for the plugin's internal modules; OpenClaw remains responsible for agent execution, channels, tools, sessions, gateway, and host policy.

## Activation

Use when planning or implementing Cordis integration into OpenClaw as a plugin or when reviewing the boundary between a composition runtime and a host agent framework.

Do not use to replace OpenClaw's core runtime, create a second gateway/session authority, or assume undocumented Cordis/OpenClaw APIs.

## Inputs and preconditions

- Exact Cordis and OpenClaw source revisions.
- Plugin SDK and host lifecycle contract.
- Required Cordis services, contexts, plugins, and dependency graph.
- Mapping of OpenClaw host surfaces to Cordis-owned internal services.
- Version, build, security, and rollback constraints.

## Procedure

1. Inspect both projects at pinned revisions; record APIs from source and tests, not names inferred from documentation alone.
2. Write a responsibility matrix: OpenClaw owns host lifecycle and public surfaces; Cordis owns composition inside the plugin boundary.
3. Define a single plugin entrypoint and an explicit Cordis root context.
4. Map host startup, configuration, logging, event, and disposal hooks into a narrow adapter.
5. Build the Cordis service graph before exposing plugin-owned tools, hooks, or routes.
6. Validate dependencies and configuration before registration.
7. Register host-facing surfaces only after Cordis composition reaches READY.
8. Keep OpenClaw sessions, channels, gateway, and tool execution as host-owned resources; access them through versioned ports.
9. Make shutdown idempotent and dispose Cordis contexts, subscriptions, and resources before host unload completes.
10. Test missing services, duplicate registration, host restart, partial activation, config reload, event ordering, cancellation, and shutdown.
11. Compare direct OpenClaw plugin behavior with the Cordis-backed variant to identify added complexity and failure modes.
12. Record the decision to adopt, defer, or reject Cordis based on measured benefit and operational cost.

## Outputs

- Host-versus-composition responsibility matrix.
- Cordis root-context and service graph design.
- OpenClaw adapter contract.
- Startup/shutdown sequence.
- Integration tests and decision record.

## Failure handling

Do not expose partially constructed services. If Cordis composition fails, report plugin activation failure and clean up acquired resources. Do not create duplicate host authorities for sessions, tools, or gateway state.

## Acceptance criteria

- OpenClaw remains the sole host authority for its public runtime surfaces.
- Cordis is contained behind one plugin boundary.
- No host-specific API leaks into domain services.
- Registration occurs only after composition validation.
- Shutdown is idempotent and resource-complete.
- Integration benefit is demonstrated against a non-Cordis baseline.
