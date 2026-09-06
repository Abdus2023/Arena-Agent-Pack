from arena_agent.models import KnowledgeUnit, WorkItem
from arena_agent.reporting import render_knowledge_unit, render_work_item
from arena_agent.validation import validate_knowledge_unit, validate_work_item
from arena_agent.vocab import Confidence, EvidenceClass


def test_render_knowledge_unit_includes_id_and_classification():
    u = KnowledgeUnit(
        id="ARENA-A-B-C",
        meaning="a claim",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.MEDIUM,
    )
    text = render_knowledge_unit(u, validate_knowledge_unit(u))
    assert "ARENA-A-B-C" in text
    assert "OBSERVED" in text
    assert "MEDIUM" in text


def test_render_work_item_includes_gates_table_header():
    item = WorkItem(id="ARENA-WORK-1", title="Do the thing", responsibility="single responsibility")
    text = render_work_item(item, validate_work_item(item))
    assert "ARENA-WORK-1" in text
    assert "Verification Gates" in text
    assert "Validation Findings" in text


def test_render_work_item_includes_persistence_section():
    """Conformance audit R18 (row 3.6): §27's "### Persistence" narrative
    section (Durable state / Journal / Recovery behavior / Indeterminate
    states and reconciliation path) must actually render, not just exist
    as unrendered fields on the dataclass."""
    item = WorkItem(
        id="ARENA-WORK-1",
        title="Do the thing",
        responsibility="single responsibility",
        durable_state="Recorded in the workspace store once saved.",
        journal="No separate write-ahead journal.",
        recovery_behavior="Last saved JSON file is authoritative.",
        indeterminate_states_reconciliation_path="See ExecutionState.INDETERMINATE.",
    )
    text = render_work_item(item, validate_work_item(item))
    assert "### Persistence" in text
    assert "Recorded in the workspace store once saved." in text
    assert "No separate write-ahead journal." in text
    assert "Last saved JSON file is authoritative." in text
    assert "See ExecutionState.INDETERMINATE." in text
