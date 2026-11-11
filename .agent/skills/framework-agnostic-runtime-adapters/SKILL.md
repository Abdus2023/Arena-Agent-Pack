---
name: framework-agnostic-runtime-adapters
description: Design portable runtime adapters that isolate host-specific APIs behind typed ports, capability negotiation, lifecycle contracts, and conformance tests.
---

# Framework-Agnostic Runtime Adapters

## Purpose

Create an adapter system that allows a domain runtime or composition framework to integrate with multiple host frameworks without leaking host-specific behavior into the domain core.

## Activation

Use when designing a framework-agnostic adapter architecture, integrating Cordis or another composition runtime into OpenClaw, or extracting host-specific APIs into ports and adapters.

Do not use to claim portability merely because an interface is named generic. Portability requires at least two independently exercised adapters or an explicit provisional status.

## Inputs and preconditions

- Domain core and host responsibilities.
- Host API revisions and supported lifecycle hooks.
- Required capabilities and optional capabilities.
- Lifecycle, error, cancellation, concurrency, and resource ownership requirements.
- Security and authorization boundaries.
- Test hosts or deterministic fakes.

## Procedure

1. Identify the domain core's invariants and the host's authoritative responsibilities.
2. Define narrow ports for logging, configuration, lifecycle, events, tools, storage, scheduling, and capability registration only where required.
3. Keep host-specific types at adapter boundaries; normalize them into domain-owned types.
4. Define capability negotiation with REQUIRED, OPTIONAL, and UNSUPPORTED states. Reject missing required capabilities before activation.
5. Define adapter lifecycle: CONSTRUCTED, VALIDATED, ATTACHED, STARTED, READY, DEGRADED, FAILED, STOPPING, STOPPED.
6. Define ownership and disposal rules for subscriptions, timers, resources, and child contexts.
7. Normalize errors while preserving original cause, host code, retryability, and correlation ID.
8. Specify concurrency, backpressure, cancellation, and reentrancy semantics.
9. Version the adapter contract independently from each host integration.
10. Build contract tests against a host fake, then run the same suite against each real adapter.
11. Test absent optional capabilities, missing required capabilities, duplicate attach, startup failure, partial startup, shutdown, cancellation, and host API drift.
12. Report portability only for the adapters and host versions actually tested.

## Outputs

- Domain ports and adapter interfaces.
- Capability negotiation model.
- Lifecycle and resource ownership contract.
- Error mapping and version policy.
- Host conformance suite and compatibility matrix.

## Failure handling

Reject activation when a required capability is missing, the host version is incompatible, ownership is ambiguous, or partial startup cannot be safely unwound. Do not silently emulate unsupported host behavior.

## Acceptance criteria

- Domain core has no direct dependency on host-specific APIs.
- Required and optional capabilities are explicit.
- Lifecycle and disposal are deterministic.
- Errors preserve causal information.
- Contract tests run against fakes and each claimed host adapter.
- Portability claims are scoped to tested host/version pairs.
