"""
Arena Agent — Python implementation of the Arena Agent Prompt Instructions Pack.

This package is a working, programmatic implementation of the rules,
vocabularies, record types, and workflow described in:

    - arena-agent-instructions-pack.md      (v1, original 43-section pack)
    - arena-agent-instructions-pack-v2.md   (v2, consolidated revision)

v2 is treated as canonical here. Where v1 used different names for the same
concept (e.g. ``INAPPLICABLE`` vs ``NOT_APPLICABLE``), the v1 spelling is
kept as an alias so text written against either version of the pack still
resolves to the same enum member.

Scope: no External Effect Contract (v2 §13)
--------------------------------------------
This package is deliberately a record-keeping / validation / reporting
system, not an execution engine: it never invokes an external effect on
the agent's behalf. §13's pipeline (Proposal -> Validation -> Authorization
-> Resource check -> Policy check -> Durability -> Invocation ->
Observation -> Receipt/outcome -> Verification) and its durable-issuance
invariant (``HostInvoked(E) => DurableIssued(E)``) are a specialization of
the general Dependency Direction (§14) specifically for actions that cross
a durability or effect boundary. Because nothing in this codebase ever
crosses that boundary -- there is no code path anywhere that invokes an
externally-visible effect -- §13 has no corresponding pipeline object, no
durability-boundary check, and no invariant enforcement here. This is a
disclosed scope decision (conformance audit Recommendation R8), not a
silent omission: modeling an "effect" pipeline that nothing in this
package ever exercises would add a parallel concept with no real caller,
which the governing "do not manufacture scope merely to close a matrix
cell" rule for this project's remediation work explicitly forbids. A
caller embedding this package inside a system that *does* invoke real
external effects is responsible for enforcing §13 itself at that
boundary; this package's authority-related fields
(``WorkItem.required_authority``/``forbidden_authority``,
``KnowledgeUnit.authority_implications``) can inform such a caller's own
enforcement, but they are not themselves an External Effect Contract
implementation.

Scope: no Authority Contract enforcement (v2 §11)
--------------------------------------------------
v2 §11's Authority Contract requires that the Arena Agent distinguish
knowledge, permission, capability, authorization, and execution, and that
any derivation of a capability from an authority satisfy the governing
authority relation for attenuable authority: ``derive(A, C) ⪯ A`` (never
amplification), with no ambient authority, implicit capability creation,
capability duplication, capability amplification, hidden capability
lookup, or authority smuggling through metadata. This package never
derives a capability from an authority and never itself exercises one --
like §13 (see above), this is a record-keeping/validation/reporting
system, not an execution engine. Its authority-related fields
(``WorkItem.required_authority``/``forbidden_authority``,
``KnowledgeUnit.authority_implications``,
``DecisionRecord.required_authority``) are opaque free-text declarations
with no defined authority-value representation, partial order, or
attenuation relation anywhere in the pack to check ``⪯`` against for even
one concrete case. Inventing one here (e.g. treating a capability tag
list as the authority value and set-inclusion as ``⪯``) would fabricate
semantics §11 itself never specifies -- exactly the kind of unstated-state
invention this project's remediation work forbids. This is a disclosed
scope decision (conformance audit Recommendation R7), not a claim that
§11 is non-normative: §11 remains normative for whatever system actually
performs derivation or exercises a capability; enforcing it there is that
system's responsibility, informed by (but not discharged by) this
package's authority-related records.

Package layout
---------------
- ``arena_agent.vocab``       Controlled vocabularies (enums) — Appendix A of v2.
- ``arena_agent.ids``         Stable ID generation/validation — §8 / §28 / §29 etc.
- ``arena_agent.models``      Record dataclasses (Knowledge Unit, Work Item,
                               Decision Record, Counterexample, Repo Audit,
                               Change-Impact Analysis, Final Report).
- ``arena_agent.validation``  Rule enforcement: confidence/classification
                               constraints, lifecycle transition legality,
                               gate completeness, resource conservation,
                               counterexample staging, completion contract.
- ``arena_agent.graph``       Knowledge graph (nodes/edges), planned vs.
                               observed partitioning, forbidden-dependency
                               and contradiction detection.
- ``arena_agent.storage``     JSON file-backed workspace store.
- ``arena_agent.reporting``   Markdown rendering (mirrors the template pack).
- ``arena_agent.content_scan``Ingested Content Contract helper (§4.1) — flags
                               anti-pattern / imperative-sounding text found
                               in ingested (untrusted) source material.
- ``arena_agent.cli``         Command-line interface.

Nothing in this package will silently invent evidence, silently resolve
ambiguity, or silently promote a weaker classification into a stronger one —
consistent with the Core Contract (pack v2 §2 / v1 §1).
"""

__version__ = "2.0.0"
__pack_version__ = "2.0.0"

from .vocab import (
    EvidenceClass,
    ExtractionClass,
    ExecutionState,
    EvidenceState,
    AuthorizationState,
    DivergenceClass,
    LifecycleState,
    VerificationResult,
    VerificationGate,
    VerificationMethod,
    PresenceClass,
    ImpactClass,
    Confidence,
    Coverage,
    CounterexampleStage,
    GraphNodeType,
    GraphEdgeType,
    ClaimStatus,
    DecisionStatus,
    TrustTier,
)

__all__ = [
    "__version__",
    "__pack_version__",
    "EvidenceClass",
    "ExtractionClass",
    "ExecutionState",
    "EvidenceState",
    "AuthorizationState",
    "DivergenceClass",
    "LifecycleState",
    "VerificationResult",
    "VerificationGate",
    "VerificationMethod",
    "PresenceClass",
    "ImpactClass",
    "Confidence",
    "Coverage",
    "CounterexampleStage",
    "GraphNodeType",
    "GraphEdgeType",
    "ClaimStatus",
    "DecisionStatus",
    "TrustTier",
]
