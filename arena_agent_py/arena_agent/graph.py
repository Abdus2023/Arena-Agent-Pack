"""
Knowledge Graph. v2 §34 (v1 §34), consumed by Change-Impact Analysis (v2 §36).

Implements:
  - node/edge registries with mandatory provenance,
  - explicit DERIVED marking for inferred edges (never silently blended
    with directly-sourced edges),
  - Planned vs. Observed subgraph partitioning (v2 §34 / §6),
  - contradiction detection surfaced separately, never auto-resolved,
  - direct/indirect dependent traversal, feeding Change-Impact Analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .vocab import GraphEdgeType, GraphNodeType


class GraphIntegrityError(ValueError):
    """Raised when an edge references a node that doesn't exist, or provenance is missing."""


@dataclass
class GraphNode:
    id: str
    node_type: GraphNodeType
    label: str
    planned: bool  # True = planned architecture, False = observed implementation
    provenance: str = ""  # e.g. a KnowledgeUnit id, RepoAudit item path, WorkItem id, Decision id


@dataclass
class GraphEdge:
    id: str
    from_id: str
    edge_type: GraphEdgeType
    to_id: str
    provenance: str = ""
    derived: bool = False
    notes: str = ""


@dataclass
class KnowledgeGraph:
    """
    In-memory knowledge graph. Node/edge provenance is mandatory (v2 §34:
    "every edge must have provenance") -- both are validated at add time
    rather than silently accepted without it, since retrofitting provenance
    after the fact defeats the purpose.
    """

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, GraphEdge] = field(default_factory=dict)

    def add_node(self, node: GraphNode, *, require_provenance: bool = True) -> GraphNode:
        if require_provenance and not node.provenance:
            raise GraphIntegrityError(
                f"Node {node.id!r} has no provenance. Every node must be traceable "
                "to a Knowledge Unit, Repo-Audit item, Work Item, or Decision "
                "Record (v2 §34)."
            )
        self.nodes[node.id] = node
        return node

    def add_edge(self, edge: GraphEdge, *, require_provenance: bool = True) -> GraphEdge:
        if edge.from_id not in self.nodes:
            raise GraphIntegrityError(f"Edge {edge.id!r}: from_id {edge.from_id!r} not in graph.")
        if edge.to_id not in self.nodes:
            raise GraphIntegrityError(f"Edge {edge.id!r}: to_id {edge.to_id!r} not in graph.")
        if require_provenance and not edge.provenance:
            raise GraphIntegrityError(
                f"Edge {edge.id!r} has no provenance. Every edge must have "
                "provenance (v2 §34)."
            )
        self.edges[edge.id] = edge
        return edge

    # -- Planned / Observed partition (v2 §34 "separate planned architecture
    # from observed implementation") ---------------------------------------

    def planned_subgraph(self) -> "KnowledgeGraph":
        return self._subgraph_where(lambda n: n.planned)

    def observed_subgraph(self) -> "KnowledgeGraph":
        return self._subgraph_where(lambda n: not n.planned)

    def _subgraph_where(self, predicate) -> "KnowledgeGraph":
        sub = KnowledgeGraph()
        keep_ids = {nid for nid, n in self.nodes.items() if predicate(n)}
        for nid in keep_ids:
            sub.nodes[nid] = self.nodes[nid]
        for eid, e in self.edges.items():
            if e.from_id in keep_ids and e.to_id in keep_ids:
                sub.edges[eid] = e
        return sub

    def divergences(self) -> list[tuple[GraphNode, Optional[GraphNode]]]:
        """
        Planned nodes with no corresponding observed node sharing the same
        label (a crude but explicit "claimed but not seen" detector -- real
        matching logic is domain specific, so this is a starting point the
        caller can override/replace).
        """
        observed_labels = {n.label for n in self.nodes.values() if not n.planned}
        result: list[tuple[GraphNode, Optional[GraphNode]]] = []
        for n in self.nodes.values():
            if n.planned and n.label not in observed_labels:
                result.append((n, None))
        return result

    # -- Contradiction surfacing --------------------------------------------

    def contradictions(self) -> list[GraphEdge]:
        return [e for e in self.edges.values() if e.edge_type == GraphEdgeType.CONTRADICTS]

    # -- Traversal ------------------------------------------------------------

    def direct_dependents(self, node_id: str, edge_types: Optional[Iterable[GraphEdgeType]] = None) -> list[GraphNode]:
        """
        Nodes that point *at* ``node_id`` via one of ``edge_types``
        (defaults to the dependency-ish edges relevant to Change-Impact
        Analysis: requires, depends-on, constrains, implements).
        """
        edge_types = set(
            edge_types
            or {
                GraphEdgeType.REQUIRES,
                GraphEdgeType.DEPENDS_ON,
                GraphEdgeType.CONSTRAINS,
                GraphEdgeType.IMPLEMENTS,
            }
        )
        result = []
        for e in self.edges.values():
            if e.to_id == node_id and e.edge_type in edge_types:
                if e.from_id in self.nodes:
                    result.append(self.nodes[e.from_id])
        return result

    def indirect_dependents(
        self, node_id: str, edge_types: Optional[Iterable[GraphEdgeType]] = None
    ) -> list[GraphNode]:
        """BFS over direct_dependents, excluding the direct set and the origin node."""
        direct = {n.id for n in self.direct_dependents(node_id, edge_types)}
        seen = set(direct) | {node_id}
        frontier = list(direct)
        indirect: list[GraphNode] = []
        while frontier:
            current = frontier.pop()
            for dep in self.direct_dependents(current, edge_types):
                if dep.id not in seen:
                    seen.add(dep.id)
                    indirect.append(dep)
                    frontier.append(dep.id)
        return indirect

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": n.id,
                    "node_type": n.node_type.value,
                    "label": n.label,
                    "planned": n.planned,
                    "provenance": n.provenance,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "id": e.id,
                    "from_id": e.from_id,
                    "edge_type": e.edge_type.value,
                    "to_id": e.to_id,
                    "provenance": e.provenance,
                    "derived": e.derived,
                    "notes": e.notes,
                }
                for e in self.edges.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        g = cls()
        for n in data.get("nodes", []):
            g.nodes[n["id"]] = GraphNode(
                id=n["id"],
                node_type=GraphNodeType(n["node_type"]),
                label=n["label"],
                planned=n["planned"],
                provenance=n.get("provenance", ""),
            )
        for e in data.get("edges", []):
            g.edges[e["id"]] = GraphEdge(
                id=e["id"],
                from_id=e["from_id"],
                edge_type=GraphEdgeType(e["edge_type"]),
                to_id=e["to_id"],
                provenance=e.get("provenance", ""),
                derived=e.get("derived", False),
                notes=e.get("notes", ""),
            )
        return g
