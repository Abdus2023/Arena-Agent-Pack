from arena_agent.models import KnowledgeUnit, RepoAudit, WorkItem
from arena_agent.storage import RecordNotFound, Workspace
from arena_agent.vocab import Confidence, EvidenceClass, LifecycleState


def test_workspace_init_creates_subdirs(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    for sub in Workspace.SUBDIRS:
        assert (tmp_path / "ws" / sub).exists()


def test_knowledge_unit_roundtrip(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    u = KnowledgeUnit(
        id="ARENA-A-B-C",
        meaning="a claim",
        evidence_class=EvidenceClass.OBSERVED,
        confidence=Confidence.MEDIUM,
        lifecycle_state=LifecycleState.CLASSIFIED,
    )
    ws.save_knowledge_unit(u)
    loaded = ws.load_knowledge_unit("ARENA-A-B-C")
    assert loaded.id == u.id
    assert loaded.evidence_class == EvidenceClass.OBSERVED
    assert loaded.lifecycle_state == LifecycleState.CLASSIFIED


def test_missing_record_raises(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    try:
        ws.load_knowledge_unit("ARENA-NOPE-NOPE-NOPE")
        assert False, "expected RecordNotFound"
    except RecordNotFound:
        pass


def test_work_item_with_nested_records_roundtrip(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    item = WorkItem(id="ARENA-WORK-1", title="t", responsibility="r")
    item.log("plan", actor="agent-1", note="initial plan")
    ws.save_work_item(item)
    loaded = ws.load_work_item("ARENA-WORK-1")
    assert len(loaded.lifecycle_log) == 1
    assert loaded.lifecycle_log[0].stage == "plan"
    assert loaded.lifecycle_log[0].details["note"] == "initial plan"


def test_dated_seq_id_helpers_avoid_collisions(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.init()
    from arena_agent.models import DecisionRecord

    id1 = ws.next_decision_id()
    ws.save_decision(DecisionRecord(id=id1, question="q1"))
    id2 = ws.next_decision_id()
    assert id1 != id2
    ws.save_decision(DecisionRecord(id=id2, question="q2"))
    assert set(ws.list_ids("decisions")) == {id1, id2}


def test_repo_audit_inventory_roundtrip(tmp_path):
    from arena_agent.models import InventoryItem
    from arena_agent.vocab import PresenceClass

    ws = Workspace(tmp_path / "ws")
    ws.init()
    audit = RepoAudit(id="ARENA-AUDIT-1", repository="repo")
    audit.inventory.append(
        InventoryItem(path="src/", kind="dir", classification=PresenceClass.PRESENT, evidence="seen")
    )
    ws.save_repo_audit(audit)
    loaded = ws.load_repo_audit("ARENA-AUDIT-1")
    assert loaded.inventory[0].classification == PresenceClass.PRESENT
