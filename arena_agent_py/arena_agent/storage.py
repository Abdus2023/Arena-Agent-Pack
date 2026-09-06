"""
JSON file-backed workspace store.

One JSON file per record, grouped by record type into subdirectories, so
the workspace stays human-diffable and easy to inspect or put under version
control -- matching how the companion Markdown templates were designed to
be used (one file per audit/work-item/decision/etc.), just machine-readable
instead of prose.

Layout::

    <workspace_root>/
        knowledge_units/<id>.json
        work_items/<id>.json
        decisions/<id>.json
        counterexamples/<id>.json
        repo_audits/<id>.json
        change_impact/<id>.json
        final_reports/<id>.json
        graphs/<id>.json
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

from . import __pack_version__
from .graph import KnowledgeGraph
from .ids import IdKind, new_dated_seq_id
from .models import (
    ChangeImpactAnalysis,
    CounterexampleRecord,
    DecisionRecord,
    FinalReport,
    GateResult,
    InterpretationOption,
    InventoryItem,
    KnowledgeUnit,
    LifecycleLogEntry,
    MinimizationRecord,
    Ownership,
    RepoAudit,
    WikiChangeHistoryEntry,
    WikiPage,
    WorkItem,
    to_dict,
)
from .vocab import (
    AuthorizationState,
    ClaimStatus,
    Confidence,
    Coverage,
    CounterexampleStage,
    DecisionStatus,
    DivergenceClass,
    EvidenceClass,
    EvidenceState,
    ExecutionState,
    ExtractionClass,
    ImpactClass,
    LifecycleState,
    PresenceClass,
    ResolutionStatus,
    VerificationGate,
    VerificationMethod,
    VerificationResult,
    WikiPageNumber,
)

T = TypeVar("T")


class RecordNotFound(KeyError):
    pass


class RecordCorrupted(ValueError):
    """
    Raised when a record file exists but cannot be parsed as JSON or does
    not match the shape its record type requires (missing/extra/malformed
    fields). Wraps the underlying JSONDecodeError/KeyError/TypeError so
    callers (in particular the CLI) get one exception type to catch,
    carrying a message that identifies the file and the underlying cause,
    instead of a raw stdlib traceback leaking to the user.
    """


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Deserialization helpers (dict -> dataclass), written explicitly rather than
# via a generic reflection helper, so enum/nested-dataclass coercion stays
# obvious and easy to audit.
# ---------------------------------------------------------------------------


def _knowledge_unit_from_dict(d: dict[str, Any]) -> KnowledgeUnit:
    d = dict(d)
    d["evidence_class"] = EvidenceClass(d["evidence_class"])
    d["confidence"] = Confidence(d["confidence"])
    d["lifecycle_state"] = LifecycleState(d["lifecycle_state"])
    d["implementation_status"] = PresenceClass(d["implementation_status"])
    d["evidence_state"] = EvidenceState(d["evidence_state"])
    if d.get("extraction_class"):
        d["extraction_class"] = ExtractionClass(d["extraction_class"])
    return KnowledgeUnit(**d)


def _work_item_from_dict(d: dict[str, Any]) -> WorkItem:
    d = dict(d)
    d["evidence_class"] = EvidenceClass(d["evidence_class"])
    d["confidence"] = Confidence(d["confidence"])
    d["lifecycle_state"] = LifecycleState(d["lifecycle_state"])
    d["execution_state"] = ExecutionState(d["execution_state"])
    d["authorization_state"] = AuthorizationState(d["authorization_state"])
    d["evidence_state"] = EvidenceState(d["evidence_state"])
    own = d.get("ownership") or {}
    d["ownership"] = Ownership(
        owner=own.get("owner"),
        claimed_at=own.get("claimed_at"),
        status=ClaimStatus(own.get("status", ClaimStatus.RELEASED.value)),
    )
    d["gates"] = [
        GateResult(
            gate=VerificationGate(g["gate"]),
            method=VerificationMethod(g["method"]) if g.get("method") else None,
            result=VerificationResult(g["result"]),
            evidence=g.get("evidence", ""),
        )
        for g in d.get("gates", [])
    ]
    d["lifecycle_log"] = [
        LifecycleLogEntry(
            stage=entry["stage"],
            timestamp=entry.get("timestamp", ""),
            actor=entry.get("actor", ""),
            details=entry.get("details", {}),
        )
        for entry in d.get("lifecycle_log", [])
    ]
    return WorkItem(**d)


def _decision_from_dict(d: dict[str, Any]) -> DecisionRecord:
    d = dict(d)
    d["status"] = DecisionStatus(d["status"])
    d["options"] = [
        InterpretationOption(
            option_id=o["option_id"],
            description=o.get("description", ""),
            consequences=o.get("consequences", ""),
        )
        for o in d.get("options", [])
    ]
    return DecisionRecord(**d)


def _counterexample_from_dict(d: dict[str, Any]) -> CounterexampleRecord:
    d = dict(d)
    d["stage"] = CounterexampleStage(d["stage"])
    if d.get("divergence_classification"):
        d["divergence_classification"] = DivergenceClass(d["divergence_classification"])
    if d.get("resolution_status"):
        d["resolution_status"] = ResolutionStatus(d["resolution_status"])
    if d.get("minimization"):
        m = d["minimization"]
        d["minimization"] = MinimizationRecord(
            original_case=m.get("original_case"),
            minimized_case=m.get("minimized_case"),
            removed_structure=m.get("removed_structure", ""),
            preserved_invariant=m.get("preserved_invariant", ""),
            checklist=m.get("checklist", {}),
        )
    return CounterexampleRecord(**d)


def _repo_audit_from_dict(d: dict[str, Any]) -> RepoAudit:
    d = dict(d)
    d["inventory"] = [
        InventoryItem(
            path=i["path"],
            kind=i["kind"],
            classification=PresenceClass(i["classification"]),
            coverage=Coverage(i.get("coverage", Coverage.EXHAUSTIVE.value)),
            coverage_method=i.get("coverage_method", ""),
            evidence=i.get("evidence", ""),
            notes=i.get("notes", ""),
        )
        for i in d.get("inventory", [])
    ]
    return RepoAudit(**d)


def _change_impact_from_dict(d: dict[str, Any]) -> ChangeImpactAnalysis:
    from .models import ImpactCategoryResult

    d = dict(d)
    cats = {}
    for cat, result in d.get("categories", {}).items():
        cats[cat] = ImpactCategoryResult(
            category=cat,
            classification=ImpactClass(result.get("classification", ImpactClass.NONE.value)),
            details=result.get("details", ""),
            evidence=result.get("evidence", ""),
        )
    d["categories"] = cats
    return ChangeImpactAnalysis(**d)


def _final_report_from_dict(d: dict[str, Any]) -> FinalReport:
    return FinalReport(**d)


def _wiki_page_from_dict(d: dict[str, Any]) -> WikiPage:
    d = dict(d)
    d["page_number"] = WikiPageNumber(d["page_number"])
    d["change_history"] = [WikiChangeHistoryEntry(**entry) for entry in d.get("change_history", [])]
    return WikiPage(**d)


_LOADERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "knowledge_units": _knowledge_unit_from_dict,
    "work_items": _work_item_from_dict,
    "decisions": _decision_from_dict,
    "counterexamples": _counterexample_from_dict,
    "repo_audits": _repo_audit_from_dict,
    "change_impact": _change_impact_from_dict,
    "final_reports": _final_report_from_dict,
    "wiki_pages": _wiki_page_from_dict,
}


class Workspace:
    """A directory on disk holding all Arena record types as JSON files."""

    SUBDIRS = (
        "knowledge_units",
        "work_items",
        "decisions",
        "counterexamples",
        "repo_audits",
        "change_impact",
        "final_reports",
        "graphs",
        "wiki_pages",
    )

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def init(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in self.SUBDIRS:
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # -- generic save/load --------------------------------------------------

    def _path(self, subdir: str, record_id: str) -> Path:
        safe_id = record_id.replace("/", "_")
        return self.root / subdir / f"{safe_id}.json"

    def save(self, subdir: str, record_id: str, obj: Any) -> Path:
        path = self._path(subdir, record_id)
        _write_json(path, to_dict(obj) if is_dataclass(obj) else obj)
        return path

    def load(self, subdir: str, record_id: str) -> Any:
        path = self._path(subdir, record_id)
        if not path.exists():
            raise RecordNotFound(f"No {subdir} record with id {record_id!r} in {self.root}")
        try:
            data = _read_json(path)
        except json.JSONDecodeError as exc:
            raise RecordCorrupted(
                f"{path} is not valid JSON ({exc}). The record cannot be loaded as-is -- "
                "restore it from version control or recreate it; do not hand-edit past "
                "the point of producing invalid JSON."
            ) from exc
        loader = _LOADERS.get(subdir)
        if loader is None:
            return data
        try:
            return loader(data)
        except KeyError as exc:
            raise RecordCorrupted(
                f"{path} is missing required field {exc}. This {subdir[:-1] if subdir.endswith('s') else subdir} "
                "record cannot be loaded until that field is present -- if it was "
                "hand-edited, restore the missing field rather than guessing a value."
            ) from exc
        except (TypeError, ValueError) as exc:
            raise RecordCorrupted(
                f"{path} does not match the expected shape for a {subdir} record: {exc}. "
                "This can happen if the file was hand-edited, written by an older/newer "
                "version of this tool, or is otherwise not a valid record of this type."
            ) from exc

    def list_ids(self, subdir: str) -> list[str]:
        d = self.root / subdir
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.json"))

    def exists(self, subdir: str, record_id: str) -> bool:
        return self._path(subdir, record_id).exists()

    def delete(self, subdir: str, record_id: str) -> None:
        path = self._path(subdir, record_id)
        if path.exists():
            path.unlink()

    # -- typed convenience wrappers -----------------------------------------

    def save_knowledge_unit(self, unit: KnowledgeUnit) -> Path:
        return self.save("knowledge_units", unit.id, unit)

    def load_knowledge_unit(self, unit_id: str) -> KnowledgeUnit:
        return self.load("knowledge_units", unit_id)

    def list_knowledge_units(self) -> list[KnowledgeUnit]:
        return [self.load_knowledge_unit(i) for i in self.list_ids("knowledge_units")]

    def save_work_item(self, item: WorkItem) -> Path:
        return self.save("work_items", item.id, item)

    def load_work_item(self, item_id: str) -> WorkItem:
        return self.load("work_items", item_id)

    def list_work_items(self) -> list[WorkItem]:
        return [self.load_work_item(i) for i in self.list_ids("work_items")]

    def save_decision(self, decision: DecisionRecord) -> Path:
        return self.save("decisions", decision.id, decision)

    def load_decision(self, decision_id: str) -> DecisionRecord:
        return self.load("decisions", decision_id)

    def list_decisions(self) -> list[DecisionRecord]:
        return [self.load_decision(i) for i in self.list_ids("decisions")]

    def next_decision_id(self) -> str:
        return new_dated_seq_id(IdKind.DECISION, existing_ids=set(self.list_ids("decisions")))

    def save_counterexample(self, record: CounterexampleRecord) -> Path:
        return self.save("counterexamples", record.id, record)

    def load_counterexample(self, ce_id: str) -> CounterexampleRecord:
        return self.load("counterexamples", ce_id)

    def list_counterexamples(self) -> list[CounterexampleRecord]:
        return [self.load_counterexample(i) for i in self.list_ids("counterexamples")]

    def next_counterexample_id(self) -> str:
        return new_dated_seq_id(IdKind.CE, existing_ids=set(self.list_ids("counterexamples")))

    def save_repo_audit(self, audit: RepoAudit) -> Path:
        return self.save("repo_audits", audit.id, audit)

    def load_repo_audit(self, audit_id: str) -> RepoAudit:
        return self.load("repo_audits", audit_id)

    def list_repo_audits(self) -> list[RepoAudit]:
        return [self.load_repo_audit(i) for i in self.list_ids("repo_audits")]

    def next_repo_audit_id(self) -> str:
        return new_dated_seq_id(IdKind.AUDIT, existing_ids=set(self.list_ids("repo_audits")))

    def save_change_impact(self, analysis: ChangeImpactAnalysis) -> Path:
        return self.save("change_impact", analysis.id, analysis)

    def load_change_impact(self, analysis_id: str) -> ChangeImpactAnalysis:
        return self.load("change_impact", analysis_id)

    def list_change_impacts(self) -> list[ChangeImpactAnalysis]:
        return [self.load_change_impact(i) for i in self.list_ids("change_impact")]

    def next_change_impact_id(self) -> str:
        return new_dated_seq_id(IdKind.IMPACT, existing_ids=set(self.list_ids("change_impact")))

    def save_final_report(self, report: FinalReport) -> Path:
        return self.save("final_reports", report.id, report)

    def load_final_report(self, report_id: str) -> FinalReport:
        return self.load("final_reports", report_id)

    def list_final_reports(self) -> list[FinalReport]:
        return [self.load_final_report(i) for i in self.list_ids("final_reports")]

    def save_graph(self, graph_id: str, graph: KnowledgeGraph) -> Path:
        path = self._path("graphs", graph_id)
        _write_json(path, graph.to_dict())
        return path

    def load_graph(self, graph_id: str) -> KnowledgeGraph:
        path = self._path("graphs", graph_id)
        if not path.exists():
            raise RecordNotFound(f"No graph with id {graph_id!r} in {self.root}")
        try:
            data = _read_json(path)
        except json.JSONDecodeError as exc:
            raise RecordCorrupted(f"{path} is not valid JSON ({exc}).") from exc
        try:
            return KnowledgeGraph.from_dict(data)
        except (KeyError, TypeError, ValueError) as exc:
            raise RecordCorrupted(
                f"{path} does not match the expected shape for a graph record: {exc}."
            ) from exc

    def next_graph_id(self) -> str:
        return new_dated_seq_id(IdKind.GRAPH, existing_ids=set(self.list_ids("graphs")))

    def save_wiki_page(self, page: WikiPage) -> Path:
        return self.save("wiki_pages", page.id, page)

    def load_wiki_page(self, page_id: str) -> WikiPage:
        return self.load("wiki_pages", page_id)

    def list_wiki_pages(self) -> list[WikiPage]:
        return [self.load_wiki_page(i) for i in self.list_ids("wiki_pages")]

    @staticmethod
    def wiki_page_id(page_number: WikiPageNumber) -> str:
        """
        WikiPage IDs are stable per canonical page number, not date-stamped
        -- there is exactly one page 00 ("Status"), not one per day it was
        edited (that's what change_history is for). Format:
        ``ARENA-WIKI-<NN>``, e.g. ``ARENA-WIKI-00``.
        """
        number = page_number.value if isinstance(page_number, WikiPageNumber) else str(page_number)
        return f"ARENA-WIKI-{number}"
