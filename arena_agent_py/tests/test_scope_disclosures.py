"""
Documentation-only scope-disclosure checks.

Conformance audit Recommendation R8 (Phase 5C): rather than manufacturing
an External Effect Contract (v2 §13) subsystem that nothing in this
record-keeping/validation/reporting package ever exercises, the adopted
position is to document -- in code, not just in the conformance matrix --
that §13 is deliberately out of scope here. This mirrors the R22 pattern
(a docstring-only fix, verified by a dedicated test asserting the
disclosure text is actually present, so it can't silently regress back to
an undocumented gap).

Conformance audit Recommendation R4 (Phase 5C, row 1.14): v2 §6.1's rule
that a SAMPLED coverage tag must not justify PRESENT/ABSENT for an
uninspected item is a real-world-inspection fact that no validator over
persisted strings can independently establish -- the existing
PRESENT_WITHOUT_EVIDENCE/SAMPLED_WITHOUT_METHOD checks enforce necessary,
not sufficient, shape prerequisites (same boundary as row 1.13). Rather
than add a mechanical proxy heuristic that would create false confidence
rather than real verification, this is disclosed as a permanent scope
limit, following the same R22 disclosure-test pattern.

Conformance audit Recommendation R7 (Phase 6, row 1.25): v2 §11's
Authority Contract (`derive(A, C) \u2aaf A`; no ambient authority, implicit
capability creation, capability duplication, capability amplification,
hidden capability lookup, or authority smuggling through metadata) is
normative for any system that actually derives a capability from an
authority or exercises one. This package never does either -- it is a
record-keeping/validation/reporting system (see also R8's §13 scope
disclosure) that stores authority-related declarations
(`WorkItem.required_authority`/`forbidden_authority`,
`KnowledgeUnit.authority_implications`,
`DecisionRecord.required_authority`) as opaque free text, with no
authority-value representation, partial order, or attenuation relation
defined anywhere in the pack to implement `\u2aaf` against for even one
concrete case. Inventing one (e.g. treating a capability tag list as the
authority value and set-inclusion as `\u2aaf`) would fabricate semantics
the pack itself never specifies, which the governing "do not invent
unstated state" rule for this project's remediation work forbids. This
is disclosed as a scope boundary, not a claim that \u00a711 is non-normative:
\u00a711 remains a live invariant for whatever system actually performs
derivation; enforcing it there is that system's responsibility, informed
by (but not discharged by) this package's authority-related records.
"""

import arena_agent
from arena_agent.models import DecisionRecord, InventoryItem, KnowledgeUnit, WorkItem


def test_package_docstring_discloses_no_external_effect_contract():
    """The package docstring must explicitly state that v2 §13 (External
    Effect Contract) has no implementation here, and that this is a
    deliberate, disclosed scope decision (R8) rather than a silent gap.
    """
    doc = (arena_agent.__doc__ or "").lower()
    assert "§13" in (arena_agent.__doc__ or "")
    assert "external effect" in doc
    assert "not an execution engine" in doc
    assert "r8" in doc


def test_work_item_docstring_points_to_the_external_effect_scope_disclosure():
    """WorkItem carries the closest fields to §13's authority concept
    (required_authority/forbidden_authority) -- its docstring must point a
    reader at the package-level disclosure rather than leaving the
    connection implicit.
    """
    doc = (WorkItem.__doc__ or "").lower()
    assert "external effect" in doc
    assert "§13" in (WorkItem.__doc__ or "")
    assert "r8" in doc


def test_inventory_item_docstring_discloses_the_sampling_inspection_limit():
    """InventoryItem's docstring must explicitly disclose that §6.1's
    "actually inspected" requirement is a permanent verification boundary
    (R4), not something PRESENT_WITHOUT_EVIDENCE/SAMPLED_WITHOUT_METHOD
    can fully close, and must name why a mechanical proxy was rejected.
    """
    doc = (InventoryItem.__doc__ or "").lower()
    assert "§6.1" in (InventoryItem.__doc__ or "")
    assert "necessary, not sufficient" in doc
    assert "r4" in doc
    assert "permanent" in doc


# ---------------------------------------------------------------------------
# R7 (Phase 6, row 1.25): v2 §11 Authority Contract scope disclosure.
#
# Each assertion also carries an explicit "not non-normative" check: the
# disclosure must state that §11 remains a live invariant for a system that
# actually performs derivation, not merely that this package ignores it.
# ---------------------------------------------------------------------------


def test_package_docstring_discloses_no_authority_contract_enforcement():
    """The package docstring must explicitly state that v2 §11 (Authority
    Contract) has no enforcement implementation here, that this is a
    deliberate, disclosed scope decision (R7) rather than a silent gap, and
    that §11 remains normative for a system that actually derives/exercises
    authority (i.e. this is a boundary disclosure, not a claim that §11 is
    non-normative).
    """
    doc_raw = arena_agent.__doc__ or ""
    doc = doc_raw.lower()
    assert "§11" in doc_raw
    assert "authority contract" in doc
    assert "r7" in doc
    assert "remains normative" in doc or "remains a live invariant" in doc


def test_work_item_docstring_points_to_the_authority_contract_scope_disclosure():
    """WorkItem carries required_authority/forbidden_authority -- the
    fields closest to §11's derivation/attenuation concept -- so its
    docstring must point a reader at the package-level §11 disclosure, not
    just the existing §13 one.
    """
    doc = (WorkItem.__doc__ or "").lower()
    assert "§11" in (WorkItem.__doc__ or "")
    assert "authority contract" in doc
    assert "r7" in doc


def test_knowledge_unit_docstring_points_to_the_authority_contract_scope_disclosure():
    """KnowledgeUnit carries authority_implications -- its docstring must
    point a reader at the package-level §11 disclosure.
    """
    doc = (KnowledgeUnit.__doc__ or "").lower()
    assert "§11" in (KnowledgeUnit.__doc__ or "")
    assert "authority contract" in doc
    assert "r7" in doc


def test_decision_record_docstring_points_to_the_authority_contract_scope_disclosure():
    """DecisionRecord carries required_authority -- its docstring must
    point a reader at the package-level §11 disclosure.
    """
    doc = (DecisionRecord.__doc__ or "").lower()
    assert "§11" in (DecisionRecord.__doc__ or "")
    assert "authority contract" in doc
    assert "r7" in doc
