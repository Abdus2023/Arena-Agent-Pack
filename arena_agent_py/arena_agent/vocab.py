"""
Controlled vocabularies for the Arena Agent pack.

Every enum here corresponds 1:1 to a named vocabulary in v2 Appendix A.
Where v1 used a different spelling for the same concept, the v1 spelling is
retained as an alias attribute pointing at the same member, so code or data
written against v1 still resolves correctly (pack v2 Appendix C, changelog
item #4).

Design notes
------------
- These are ``str``-subclassed Enums so they serialize cleanly to JSON and
  compare equal to their plain string value (``EvidenceClass.VERIFIED ==
  "VERIFIED"`` is True), which keeps on-disk records human-readable.
- Enums are intentionally closed sets: constructing an invalid value raises
  ``ValueError`` immediately rather than silently accepting free text. This
  mirrors the pack's "closed classification" requirement (v2 §5 / v1 §4) —
  every extracted statement must receive *exactly one* value from a fixed
  set, not an ad hoc string.
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """Base class: string-valued enum with a readable repr."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class EvidenceClass(_StrEnum):
    """Source-of-truth classification. v2 §5 / v1 §4. Vocabulary: EVIDENCE-CLASS."""

    NORMATIVE_SPECIFICATION = "NORMATIVE-SPECIFICATION"
    ARCHITECTURAL_PROPOSAL = "ARCHITECTURAL-PROPOSAL"
    IMPLEMENTED = "IMPLEMENTED"
    EXECUTED = "EXECUTED"
    TESTED = "TESTED"
    VERIFIED = "VERIFIED"
    OBSERVED = "OBSERVED"
    HISTORICAL = "HISTORICAL"
    DERIVED = "DERIVED"
    EXAMPLE = "EXAMPLE"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class ExtractionClass(_StrEnum):
    """Wiki/source extraction classification. v2 §19/§29. Vocabulary: EXTRACTION-CLASS."""

    DEFINITION = "DEFINITION"
    PRINCIPLE = "PRINCIPLE"
    REQUIREMENT = "REQUIREMENT"
    INVARIANT = "INVARIANT"
    TRANSITION = "TRANSITION"
    DEPENDENCY = "DEPENDENCY"
    INTERFACE = "INTERFACE"
    ERROR = "ERROR"
    VERIFICATION = "VERIFICATION"
    IMPLEMENTATION_STATUS = "IMPLEMENTATION-STATUS"
    EVIDENCE = "EVIDENCE"
    EXAMPLE = "EXAMPLE"
    LIMITATION = "LIMITATION"
    OPEN_DECISION = "OPEN-DECISION"


class ExecutionState(_StrEnum):
    """Durable execution status of an issued action. v2 §14/§15. Vocabulary: EXECUTION-STATE."""

    PLANNED = "PLANNED"
    STARTED = "STARTED"
    ISSUED = "ISSUED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INDETERMINATE = "INDETERMINATE"
    RECONCILED = "RECONCILED"


#: Legal ExecutionState transitions (v2 §15, conformance audit Recommendation
#: R10, row 2.2). Unlike LifecycleState's single linear happy path,
#: ExecutionState branches: ISSUED has three legal successors, not one.
#: This is transcribed directly from §15's own diagram:
#:
#:     PLANNED -> STARTED -> ISSUED -> COMPLETED
#:                              |
#:                              +-> FAILED
#:                              |
#:                              +-> INDETERMINATE -> RECONCILED
#:
#: "Issued + no completion -> INDETERMINATE -> Authoritative reconciliation
#: -> Resolved outcome" (§15) is what requires INDETERMINATE to be passed
#: through explicitly before RECONCILED -- ISSUED -> RECONCILED directly is
#: exactly the same "RUN_TASK -> DONE" compound-transition anti-pattern
#: §9.3 names for LifecycleState, applied to this axis.
#:
#: Deliberately NOT modeled here (disclosed gap, not an oversight): §15 also
#: says "missing completion evidence does not automatically mean 'not
#: executed'" -- i.e. a *stalled* ISSUED item (no terminal follow-up at all)
#: should eventually be treated as needing reconciliation. §15 defines no
#: staleness threshold or policy for that ("unless the governing
#: specification explicitly defines another semantics" -- it doesn't), so
#: this table only encodes the objectively checkable transition-legality
#: rule, not a time/policy-dependent staleness inference. See
#: validate_execution_transition's docstring.
EXECUTION_TRANSITIONS: dict[ExecutionState, tuple[ExecutionState, ...]] = {
    ExecutionState.PLANNED: (ExecutionState.STARTED,),
    ExecutionState.STARTED: (ExecutionState.ISSUED,),
    ExecutionState.ISSUED: (
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.INDETERMINATE,
    ),
    ExecutionState.COMPLETED: (),
    ExecutionState.FAILED: (),
    ExecutionState.INDETERMINATE: (ExecutionState.RECONCILED,),
    ExecutionState.RECONCILED: (),
}


class EvidenceState(_StrEnum):
    """Has evidence actually been captured? v2 §9.1 (new in v2). Vocabulary: EVIDENCE-STATE."""

    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    CAPTURED = "CAPTURED"
    VALIDATED = "VALIDATED"


class AuthorizationState(_StrEnum):
    """Current authority status of an item. v2 §9.1 (new in v2). Vocabulary: AUTHORIZATION-STATE."""

    NOT_REQUESTED = "NOT-REQUESTED"
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    ATTENUATED = "ATTENUATED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ResolutionStatus(_StrEnum):
    """
    Counterexample resolution status. NOT part of the pack's own controlled
    vocabulary (Appendix A has no closed set for this) -- it appears only
    in arena-counterexample-template.md's "Resolution" section as free
    labels: OPEN / FIXED / WONT-FIX / DUPLICATE / SPECIFICATION-CLARIFIED.
    Modeled here as a closed set anyway (rather than a bare str) so a typo
    doesn't silently pass through, while keeping this fact -- that it's
    template-sourced, not pack-normative -- documented rather than implied.
    """

    OPEN = "OPEN"
    FIXED = "FIXED"
    WONT_FIX = "WONT-FIX"
    DUPLICATE = "DUPLICATE"
    SPECIFICATION_CLARIFIED = "SPECIFICATION-CLARIFIED"


class DivergenceClass(_StrEnum):
    """Differential/failure divergence classification. v2 §22. Vocabulary: DIVERGENCE-CLASS."""

    PRODUCTION_DEFECT = "PRODUCTION_DEFECT"
    REFERENCE_DEFECT = "REFERENCE_DEFECT"
    HARNESS_DEFECT = "HARNESS_DEFECT"
    SPECIFICATION_AMBIGUITY = "SPECIFICATION_AMBIGUITY"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    UNRESOLVED = "UNRESOLVED"


class LifecycleState(_StrEnum):
    """
    Canonical per-item lifecycle state. v2 §9.1 (unifies v1 §8/§9/§42).
    Vocabulary: LIFECYCLE-STATE.

    Happy path:
        DISCOVERED -> CLASSIFIED -> NORMALIZED -> PLANNED -> AUTHORIZED
        -> EXECUTING -> OBSERVED -> VERIFIED

    Failure branches (each reachable only from the state named in the
    comment; see LIFECYCLE_FAILURE_BRANCHES below for the machine-checkable
    version of this table):
        DISCOVERED  -> REJECTED
        CLASSIFIED  -> AMBIGUOUS
        PLANNED     -> BLOCKED
        AUTHORIZED  -> FAILED
        EXECUTING   -> CRASHED
        OBSERVED    -> CONFLICTING
        VERIFIED    -> INVALIDATED
    """

    DISCOVERED = "DISCOVERED"
    CLASSIFIED = "CLASSIFIED"
    NORMALIZED = "NORMALIZED"
    PLANNED = "PLANNED"
    AUTHORIZED = "AUTHORIZED"
    EXECUTING = "EXECUTING"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"

    # Failure branches
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CRASHED = "CRASHED"
    CONFLICTING = "CONFLICTING"
    INVALIDATED = "INVALIDATED"


#: Canonical happy-path ordering (index = step number). Used by validation
#: to check that a transition only ever moves forward or into a legal
#: failure branch — never backward on the happy path (v2 §9.1/§9.2).
LIFECYCLE_HAPPY_PATH: tuple[LifecycleState, ...] = (
    LifecycleState.DISCOVERED,
    LifecycleState.CLASSIFIED,
    LifecycleState.NORMALIZED,
    LifecycleState.PLANNED,
    LifecycleState.AUTHORIZED,
    LifecycleState.EXECUTING,
    LifecycleState.OBSERVED,
    LifecycleState.VERIFIED,
)

#: Mapping of {happy-path state: failure state reachable from it}. v2 §9.1.
#:
#: NOTE: the pack's own text documents only 7 failure branches for the 8
#: happy-path states -- NORMALIZED has no defined failure branch anywhere in
#: v1 or v2. This is transcribed faithfully from the source; it is a real
#: gap in the pack itself (a NORMALIZED item that turns out to be, e.g.,
#: self-contradictory during normalization has no modeled failure state to
#: move to). Treat any attempt to fail out of NORMALIZED as a case requiring
#: a Decision Record (v2 §23) until the pack is amended to define one.
LIFECYCLE_FAILURE_BRANCHES: dict[LifecycleState, LifecycleState] = {
    LifecycleState.DISCOVERED: LifecycleState.REJECTED,
    LifecycleState.CLASSIFIED: LifecycleState.AMBIGUOUS,
    LifecycleState.PLANNED: LifecycleState.BLOCKED,
    LifecycleState.AUTHORIZED: LifecycleState.FAILED,
    LifecycleState.EXECUTING: LifecycleState.CRASHED,
    LifecycleState.OBSERVED: LifecycleState.CONFLICTING,
    LifecycleState.VERIFIED: LifecycleState.INVALIDATED,
}


class VerificationResult(_StrEnum):
    """
    Result recorded per verification gate. v2 §35.3. Vocabulary: VERIFICATION-RESULT.

    v1 spelled this value ``INAPPLICABLE`` in §33 and ``NOT-APPLICABLE`` in
    §38. v2 standardizes on NOT_APPLICABLE; INAPPLICABLE is kept below as a
    module-level alias constant for code written against v1 text.
    """

    PASS_ = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    NOT_TESTED = "NOT-TESTED"
    NOT_IMPLEMENTED = "NOT-IMPLEMENTED"
    BLOCKED = "BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_APPLICABLE = "NOT-APPLICABLE"


#: v1 §33 alias for VerificationResult.NOT_APPLICABLE (pack v2 Appendix C, item #4).
INAPPLICABLE = VerificationResult.NOT_APPLICABLE


class VerificationGate(_StrEnum):
    """The *what* axis of verification. v2 §35.1 (v1 §38). Vocabulary: VERIFICATION-GATE."""

    IDENTITY = "Identity"
    SCOPE = "Scope"
    SEMANTICS = "Semantics"
    AUTHORITY = "Authority"
    RESOURCES = "Resources"
    STATE = "State"
    EFFECTS = "Effects"
    PERSISTENCE = "Persistence"
    RECOVERY = "Recovery"
    DETERMINISM = "Determinism"
    INDEPENDENCE = "Independence"
    EVIDENCE = "Evidence"
    REPRODUCIBILITY = "Reproducibility"
    DOCUMENTATION = "Documentation"


class VerificationMethod(_StrEnum):
    """The *how* axis of verification. v2 §35.2 (v1 §27's verification list). Vocabulary: VERIFICATION-METHOD."""

    CONFORMANCE = "CONFORMANCE"
    PROPERTY = "PROPERTY"
    DIFFERENTIAL = "DIFFERENTIAL"
    MUTATION = "MUTATION"
    CRASH = "CRASH"
    SECURITY = "SECURITY"
    REPRODUCTION = "REPRODUCTION"
    MANUAL_REVIEW = "MANUAL-REVIEW"


class PresenceClass(_StrEnum):
    """Repository inventory classification. v2 §28 / v1 §28. Vocabulary: PRESENCE-CLASS."""

    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    PLANNED = "PLANNED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class ImpactClass(_StrEnum):
    """Change-impact classification. v2 §36 / v1 §35. Vocabulary: IMPACT-CLASS."""

    NONE = "NONE"
    LOCAL = "LOCAL"
    CROSS_COMPONENT = "CROSS-COMPONENT"
    SEMANTIC = "SEMANTIC"
    SECURITY = "SECURITY"
    PERSISTENCE = "PERSISTENCE"
    COMPATIBILITY = "COMPATIBILITY"
    VERIFICATION = "VERIFICATION"


class Confidence(_StrEnum):
    """Confidence scale. v2 §5.1 (new in v2). Vocabulary: CONFIDENCE."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


#: Confidence values that are legal for a given EvidenceClass. v2 §5.1's
#: table + explicit constraint sentence ("a statement classified VERIFIED
#: must not carry confidence LOW or NONE") together establish these floors:
#:   - VERIFIED/EXECUTED/TESTED/IMPLEMENTED/OBSERVED: at least MEDIUM
#:     (the table's "Required for: HIGH -> VERIFIED/EXECUTED" row is read
#:     narrowly here, deferring to the more specific, explicitly-worded
#:     MUST NOT constraint sentence rather than the table's own looser
#:     "Required for" phrasing -- raising VERIFIED/EXECUTED's floor to
#:     HIGH would be a separate, larger, currently-undecided change, not
#:     part of Recommendation R3's scope; see the conformance matrix row
#:     1.11 for this disclosed textual ambiguity).
#:   - DERIVED/ARCHITECTURAL-PROPOSAL: at least LOW, i.e. NONE is rejected
#:     (conformance audit Recommendation R3 -- previously missing here
#:     entirely, so a DERIVED/ARCHITECTURAL-PROPOSAL unit with confidence
#:     NONE passed validation silently, contradicting the table's explicit
#:     "Required for: LOW -> DERIVED, ARCHITECTURAL-PROPOSAL" row).
#:   - UNKNOWN/EXAMPLE: no floor (NONE is explicitly their own row in the
#:     table, so no ERROR should ever fire for these two classes).
MIN_CONFIDENCE_FOR_CLASS: dict[EvidenceClass, Confidence] = {
    EvidenceClass.VERIFIED: Confidence.MEDIUM,
    EvidenceClass.EXECUTED: Confidence.MEDIUM,
    EvidenceClass.TESTED: Confidence.MEDIUM,
    EvidenceClass.IMPLEMENTED: Confidence.MEDIUM,
    EvidenceClass.OBSERVED: Confidence.MEDIUM,
    EvidenceClass.DERIVED: Confidence.LOW,
    EvidenceClass.ARCHITECTURAL_PROPOSAL: Confidence.LOW,
}


#: Ordering used to compare confidence levels (index = strength).
CONFIDENCE_ORDER: tuple[Confidence, ...] = (
    Confidence.NONE,
    Confidence.LOW,
    Confidence.MEDIUM,
    Confidence.HIGH,
)


class Coverage(_StrEnum):
    """Inventory coverage tag. v2 §6.1 (new in v2). Vocabulary: COVERAGE."""

    EXHAUSTIVE = "EXHAUSTIVE"
    SAMPLED = "SAMPLED"


class CounterexampleStage(_StrEnum):
    """
    Stage of the Unified Counterexample Object. v2 §22 (consolidates v1
    §22/§23/§36). Vocabulary: stage sequence in Appendix A.15.
    """

    RAW_DIVERGENCE = "RAW-DIVERGENCE"
    OBSERVED_FAILURE = "OBSERVED-FAILURE"
    REPRODUCIBLE_DEFECT = "REPRODUCIBLE-DEFECT"
    MINIMIZED_REPRODUCER = "MINIMIZED-REPRODUCER"


#: Ordering of counterexample stages; used to enforce "promotion only moves
#: forward, and only when the stage's promotion requirement is met" (v2 §22).
COUNTEREXAMPLE_STAGE_ORDER: tuple[CounterexampleStage, ...] = (
    CounterexampleStage.RAW_DIVERGENCE,
    CounterexampleStage.OBSERVED_FAILURE,
    CounterexampleStage.REPRODUCIBLE_DEFECT,
    CounterexampleStage.MINIMIZED_REPRODUCER,
)


class GraphNodeType(_StrEnum):
    """Knowledge graph node types. v2 §34 / v1 §34. Vocabulary: Appendix A.16."""

    SOURCE = "Source"
    CLAIM = "Claim"
    REQUIREMENT = "Requirement"
    INVARIANT = "Invariant"
    COMPONENT = "Component"
    INTERFACE = "Interface"
    CAPABILITY = "Capability"
    RESOURCE = "Resource"
    TRANSITION = "Transition"
    ACTION = "Action"
    ARTIFACT = "Artifact"
    TEST = "Test"
    EVIDENCE = "Evidence"
    FAILURE = "Failure"
    DECISION = "Decision"
    COMMIT = "Commit"
    VERSION = "Version"


class GraphEdgeType(_StrEnum):
    """Knowledge graph edge types. v2 §34 / v1 §34. Vocabulary: Appendix A.17."""

    DEFINES = "defines"
    REQUIRES = "requires"
    CONSTRAINS = "constrains"
    DEPENDS_ON = "depends-on"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    VERIFIES = "verifies"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived-from"
    PRODUCES = "produces"
    CONSUMES = "consumes"
    AUTHORIZES = "authorizes"
    PERSISTS = "persists"
    RECOVERS = "recovers"
    OBSERVES = "observes"
    BLOCKS = "blocks"
    SUPERSEDES = "supersedes"


class TrustTier(_StrEnum):
    """Which tier of the v2 §3 Trust Model hierarchy an actor occupies.

    Implementation-only vocabulary (conformance audit Recommendation R1,
    row 1.5): §3 depicts the hierarchy (Human/Governance -> Arena
    Supervisor -> Arena Agent) as a diagram, and §26.2 requires an
    override decision to record "the authorizing party and their role in
    the trust hierarchy" -- but neither section names a closed
    ``TRUST-TIER`` enumeration, and there is no such entry in Appendix A.
    The 3 values below are this implementation's own, narrow, faithful
    encoding of §3's diagram, not a value transcribed verbatim from a
    pack-defined vocabulary.

    This is a classification of *who an actor is* (which position in the
    §3 hierarchy they occupy), never a magnitude or an ordering: there is
    deliberately no ``⪯`` relation, comparison operator, or "stronger
    than" semantics defined over these values anywhere in this codebase.
    Conflating "which trust tier issued this decision" with "how much
    authority a value carries" would smuggle in the v2 §11 Authority
    Contract's attenuation algebra (``derive(A, C) ⪯ A``) that this
    package deliberately does not implement (see ``arena_agent``'s
    package docstring, "Scope: no Authority Contract enforcement",
    Recommendation R7) -- ``TrustTier`` answers a different question
    (actor identity classification) and must never be used to answer
    that one (authority-value comparison).
    """

    HUMAN_GOVERNANCE = "HUMAN-GOVERNANCE"
    ARENA_SUPERVISOR = "ARENA-SUPERVISOR"
    ARENA_AGENT = "ARENA-AGENT"


class ClaimStatus(_StrEnum):
    """Work-item ownership claim status.

    Implementation-only vocabulary (conformance audit R22): §24.1 describes
    claim/expiry/release as *behavior* in prose, but never itself names a
    closed ``CLAIM-STATUS`` enumeration -- there is no ``CLAIM-STATUS``
    entry in Appendix A. The 3 values below are this implementation's own,
    narrow, faithful encoding of that prose, not a value transcribed
    verbatim from a pack-defined vocabulary. Referenced informally as
    "v2 §24.1 (new in v2)" elsewhere in this codebase/tests to mean
    "introduced to satisfy behavior new in v2 §24.1", not "defined by v2
    §24.1 as a vocabulary."
    """


    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


class WorkItemStage(_StrEnum):
    """LifecycleLogEntry.stage: which of a Work Item's five separated
    planning/execution phases one log entry records.

    Implementation-only vocabulary (conformance audit R19, row 4.4): the
    5-value set comes from v2 §31's Work Planner prompt text --
    "Separate: PLAN, AUTHORIZATION, EXECUTION, OBSERVATION, VERIFICATION"
    -- which is Sec 25-34 *prompt* prose (instructions for an LLM
    sub-agent, per §0.4's document-convention table), not a formally
    numbered Appendix A vocabulary; none of A.1-A.17 defines this set.
    Same disclosure category as ClaimStatus/DecisionStatus above: a real,
    checkable 5-value closed set that the pack states in prose but never
    itself names as an enumerated vocabulary.

    Spelling: the pack's own prompt text writes these UPPERCASE
    ("PLAN, AUTHORIZATION, ..."), but every existing call site in this
    codebase (``WorkItem.log()`` callers in `cli.py`, and every existing
    test) has always used lowercase ("plan", "authorization", ...) with
    no Appendix-A-mandated spelling to conform to (unlike e.g.
    VerificationGate's Title-case, which matches Appendix A.9 exactly
    because that vocabulary genuinely is pack-defined). Kept lowercase
    here to avoid an unnecessary, non-additive rename of every existing
    call site and on-disk record -- the pack gives no closed-vocabulary
    spelling authority to override here, only a prose list of names.
    """

    PLAN = "plan"
    AUTHORIZATION = "authorization"
    EXECUTION = "execution"
    OBSERVATION = "observation"
    VERIFICATION = "verification"


class DecisionStatus(_StrEnum):
    """Decision record status.


    Implementation-only vocabulary (conformance audit R22): like
    ``ClaimStatus``, §23/§25 (v1 §24) imply this status set through usage
    (``decided_by``/``chosen_option_id``/``supersedes_decision_id``) rather
    than stating it as an enumerated vocabulary, and there is no
    ``DECISION-STATUS`` entry in Appendix A. Referenced informally
    elsewhere as "v2 §23/§25 (v1 §24)" to mean "supports the record type
    those sections describe", not "defined by those sections as a
    vocabulary."
    """

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


class OverallStatus(_StrEnum):
    """
    Final Report overall status. v2 §40's own template literally only shows
    `COMPLETE / PARTIAL / BLOCKED` -- this is NOT an Appendix A controlled
    vocabulary the way EVIDENCE-CLASS etc. are. The 4-value model below is
    implementation vocabulary layered on top (same pattern as
    ResolutionStatus), chosen because §40's 3 values collapse two
    genuinely different situations into one word:

    - "the completion contract isn't satisfied yet, but nothing external
      is stopping it" (this implementation's INCOMPLETE)
    - "an external blocker -- a Stop Condition, a missing authorization,
      an open required decision -- actively prevents completion"
      (BLOCKED)

    PARTIAL is retained as a legacy/compatibility spelling for existing
    records, tests, and any external consumer written against the literal
    pack vocabulary; it is normalized to INCOMPLETE wherever this
    implementation reasons about status (see
    `validation.normalize_overall_status`), and the §40-conformant
    renderer maps INCOMPLETE back to PARTIAL when emitting the strict
    template's "Overall status" line (see reporting.render_final_report).
    """

    COMPLETE = "COMPLETE"
    COMPLETE_WITH_WARNINGS = "COMPLETE-WITH-WARNINGS"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"


#: v2 §40 template compatibility alias -- pack text only ever shows PARTIAL,
#: never INCOMPLETE. Treated the same as INCOMPLETE everywhere in this
#: implementation; see OverallStatus docstring.
PARTIAL = OverallStatus.INCOMPLETE


def to_pack_overall_status_label(status: OverallStatus) -> str:
    """
    Collapse the 4-value internal OverallStatus back onto the exact 3
    values v2 §40's own template literally shows (`COMPLETE / PARTIAL /
    BLOCKED`), for renderers that need strict pack-vocabulary
    conformance. COMPLETE_WITH_WARNINGS collapses into PARTIAL alongside
    INCOMPLETE -- from the pack's 3-value point of view, "materially
    complete but with warnings" and "not yet complete" are both simply
    "not a clean COMPLETE", which is exactly the ambiguity this
    implementation's richer model exists to resolve internally without
    losing pack-artifact conformance externally.
    """
    if status == OverallStatus.COMPLETE:
        return "COMPLETE"
    if status == OverallStatus.BLOCKED:
        return "BLOCKED"
    return "PARTIAL"


def normalize_overall_status(value: "OverallStatus | str") -> OverallStatus:
    """
    Coerce a status value to the canonical OverallStatus member, mapping the
    legacy ``PARTIAL`` spelling (and any case variant of it) onto
    ``INCOMPLETE``. Used at construction time (FinalReport.__post_init__)
    so ``overall_status`` is always a real enum member on every FinalReport
    instance regardless of how it was built -- old records/tests/callers
    written with the literal string "PARTIAL" still load and compare
    correctly, they just canonicalize immediately rather than requiring
    every comparison site to special-case the alias.
    """
    if isinstance(value, OverallStatus):
        return value
    normalized = str(value).strip().upper()
    if normalized == "PARTIAL":
        return OverallStatus.INCOMPLETE
    return OverallStatus(normalized)


class WikiPageNumber(_StrEnum):
    """
    The canonical 18-slot Wiki page index. v2 §38 (Prompt: Arena Wiki
    Generator) states this list *normatively*, not merely as template
    guidance -- unlike ResolutionStatus/OverallStatus above, this genuinely
    is pack vocabulary (repeated verbatim in the Wiki Page template too),
    so it is enforced as a closed set rather than left as documentation.

    Every WikiPage belongs to exactly one of these 18 slots; page_number
    is the authoritative identity and the title is a canonical, derived
    projection of it (see WIKI_PAGE_TITLES) -- not an independently
    settable field a caller could mismatch against the number.
    """

    STATUS = "00"
    SOURCE_CORPUS = "01"
    REPOSITORY_REALITY = "02"
    TRUST_MODEL = "03"
    SEMANTIC_MODEL = "04"
    INVARIANTS = "05"
    STATE_MACHINES = "06"
    AUTHORITY = "07"
    RESOURCES = "08"
    EXECUTION = "09"
    PERSISTENCE = "10"
    RECOVERY = "11"
    VERIFICATION = "12"
    EVIDENCE = "13"
    IMPLEMENTATION_INVENTORY = "14"
    DECISIONS = "15"
    COUNTEREXAMPLES = "16"
    RUNBOOKS = "17"


#: Canonical title for each page number, verbatim from v2 §38 / the Wiki
#: Page template's page index. Titles are never independently settable;
#: WikiPage.title is always derived from this via page_number.
WIKI_PAGE_TITLES: dict[WikiPageNumber, str] = {
    WikiPageNumber.STATUS: "Status",
    WikiPageNumber.SOURCE_CORPUS: "Source Corpus",
    WikiPageNumber.REPOSITORY_REALITY: "Repository Reality",
    WikiPageNumber.TRUST_MODEL: "Trust Model",
    WikiPageNumber.SEMANTIC_MODEL: "Semantic Model",
    WikiPageNumber.INVARIANTS: "Invariants",
    WikiPageNumber.STATE_MACHINES: "State Machines",
    WikiPageNumber.AUTHORITY: "Authority",
    WikiPageNumber.RESOURCES: "Resources",
    WikiPageNumber.EXECUTION: "Execution",
    WikiPageNumber.PERSISTENCE: "Persistence",
    WikiPageNumber.RECOVERY: "Recovery",
    WikiPageNumber.VERIFICATION: "Verification",
    WikiPageNumber.EVIDENCE: "Evidence",
    WikiPageNumber.IMPLEMENTATION_INVENTORY: "Implementation Inventory",
    WikiPageNumber.DECISIONS: "Decisions",
    WikiPageNumber.COUNTEREXAMPLES: "Counterexamples",
    WikiPageNumber.RUNBOOKS: "Runbooks",
}


#: The 13 numbered Stop Conditions, verbatim from v2 §26.1 (v1's equivalent
#: list; same conditions, this is the v2-numbered canonical form). This is
#: the machine-checkable enumeration referenced by "26.1.1-26.1.13" in
#: §26.2's Authorized Override Protocol, and by DecisionRecord's existing
#: `overrides_stop_condition` range check (`1 <= n <= 13`, validation.py's
#: INVALID_STOP_CONDITION_NUMBER).
#:
#: Conformance audit Recommendation R15: previously only the *override*
#: field (`DecisionRecord.overrides_stop_condition`) was range-checked
#: against "1-13" as a bare integer bound, with no lookup table backing
#: what the 13 conditions actually mean; and the *trigger* list
#: (`FinalReport.stop_conditions_triggered`, a free-form list of dicts) was
#: not checked against the 13 numbers at all -- nothing stopped an operator
#: from recording a nonexistent condition #14, or a typo'd string where a
#: number was expected. This dict exists so both call sites can validate
#: against one shared, pack-literal source of truth instead of a bare
#: magic-number range check in one place and nothing in the other.
STOP_CONDITIONS: dict[int, str] = {
    1: "Repository evidence contradicts the requested assumption.",
    2: "A planned component cannot be located.",
    3: "A state transition is undefined.",
    4: "Authority requirements are unclear.",
    5: "A decomposition would merge different trust levels.",
    6: "Persistence semantics would become ambiguous.",
    7: "An external effect could occur without the required authorization chain.",
    8: "A cleanup would weaken a normative requirement.",
    9: "A test would need to be weakened merely to accommodate implementation behavior.",
    10: "Production/reference independence would be compromised.",
    11: "Failure provenance would be lost.",
    12: "A proposed action exceeds its resource contract.",
    13: "The agent cannot distinguish observed facts from generated assumptions.",
}


