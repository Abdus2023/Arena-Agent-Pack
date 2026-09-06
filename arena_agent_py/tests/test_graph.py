import pytest

from arena_agent.graph import GraphEdge, GraphIntegrityError, GraphNode, KnowledgeGraph
from arena_agent.vocab import GraphEdgeType, GraphNodeType


def _node(id_, planned, label=None, provenance="src"):
    return GraphNode(id=id_, node_type=GraphNodeType.COMPONENT, label=label or id_, planned=planned, provenance=provenance)


def test_node_without_provenance_rejected():
    g = KnowledgeGraph()
    with pytest.raises(GraphIntegrityError):
        g.add_node(GraphNode(id="N1", node_type=GraphNodeType.COMPONENT, label="x", planned=True, provenance=""))


def test_edge_to_missing_node_rejected():
    g = KnowledgeGraph()
    g.add_node(_node("N1", True))
    with pytest.raises(GraphIntegrityError):
        g.add_edge(GraphEdge(id="E1", from_id="N1", edge_type=GraphEdgeType.REQUIRES, to_id="N-missing", provenance="src"))


def test_edge_without_provenance_rejected():
    g = KnowledgeGraph()
    g.add_node(_node("N1", True))
    g.add_node(_node("N2", True))
    with pytest.raises(GraphIntegrityError):
        g.add_edge(GraphEdge(id="E1", from_id="N1", edge_type=GraphEdgeType.REQUIRES, to_id="N2", provenance=""))


def test_planned_observed_partition():
    g = KnowledgeGraph()
    g.add_node(_node("P1", True))
    g.add_node(_node("O1", False))
    g.add_edge(GraphEdge(id="E1", from_id="P1", edge_type=GraphEdgeType.REQUIRES, to_id="O1", provenance="src"))

    planned = g.planned_subgraph()
    observed = g.observed_subgraph()
    assert "P1" in planned.nodes and "O1" not in planned.nodes
    assert "O1" in observed.nodes and "P1" not in observed.nodes
    # cross-subgraph edge should not appear in either pure subgraph
    assert "E1" not in planned.edges
    assert "E1" not in observed.edges


def test_direct_and_indirect_dependents():
    g = KnowledgeGraph()
    for nid in ("A", "B", "C", "D"):
        g.add_node(_node(nid, False))
    # B requires A, C requires B, D requires C -> dependents of A: B (direct), C, D (indirect)
    g.add_edge(GraphEdge(id="E1", from_id="B", edge_type=GraphEdgeType.REQUIRES, to_id="A", provenance="s"))
    g.add_edge(GraphEdge(id="E2", from_id="C", edge_type=GraphEdgeType.REQUIRES, to_id="B", provenance="s"))
    g.add_edge(GraphEdge(id="E3", from_id="D", edge_type=GraphEdgeType.REQUIRES, to_id="C", provenance="s"))

    direct = {n.id for n in g.direct_dependents("A")}
    indirect = {n.id for n in g.indirect_dependents("A")}
    assert direct == {"B"}
    assert indirect == {"C", "D"}


def test_contradictions_surfaced():
    g = KnowledgeGraph()
    g.add_node(_node("A", True))
    g.add_node(_node("B", False))
    g.add_edge(GraphEdge(id="E1", from_id="A", edge_type=GraphEdgeType.CONTRADICTS, to_id="B", provenance="s"))
    contras = g.contradictions()
    assert len(contras) == 1
    assert contras[0].id == "E1"


def test_divergence_detection_planned_without_observed_counterpart():
    g = KnowledgeGraph()
    g.add_node(_node("P1", True, label="ghost-crate"))
    g.add_node(_node("O1", False, label="real-crate"))
    divergences = g.divergences()
    assert any(n.id == "P1" for n, _ in divergences)
    assert not any(n.id == "O1" for n, _ in divergences)


def test_roundtrip_to_dict_from_dict():
    g = KnowledgeGraph()
    g.add_node(_node("A", True))
    g.add_node(_node("B", False))
    g.add_edge(GraphEdge(id="E1", from_id="A", edge_type=GraphEdgeType.REQUIRES, to_id="B", provenance="s", derived=True))
    data = g.to_dict()
    g2 = KnowledgeGraph.from_dict(data)
    assert set(g2.nodes) == {"A", "B"}
    assert g2.edges["E1"].derived is True
