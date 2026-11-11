#!/usr/bin/env python3
"""Validate a declarative skill/tool workflow and emit a deterministic DAG plan.

This tool plans composition only. It does not invoke skills, tools, networks,
repositories, devices, or external side effects.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

IDENT = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

def contained_path(root: Path, relative: str) -> Path | None:
    """Resolve a repository-relative path while rejecting traversal and escapes."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        return None
    base = root.resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate

def compose(manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    errors: list[str] = []
    workflow_id = manifest.get("workflow_id")
    if not isinstance(workflow_id, str) or not IDENT.fullmatch(workflow_id):
        errors.append("workflow_id must be a lowercase identifier")
    if not isinstance(manifest.get("version"), str) or not manifest.get("version"):
        errors.append("version must be a non-empty string")
    steps = manifest.get("steps")
    if not isinstance(steps, list) or not steps:
        return {"ok": False, "workflow_id": workflow_id, "order": [], "errors": errors + ["steps must be a non-empty array"]}

    by_id: dict[str, dict[str, Any]] = {}
    order_index: dict[str, int] = {}
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"steps[{index}] must be an object")
            continue
        sid = step.get("id")
        if not isinstance(sid, str) or not IDENT.fullmatch(sid):
            errors.append(f"steps[{index}].id must be a lowercase identifier")
            continue
        if sid in by_id:
            errors.append(f"duplicate step id: {sid}")
            continue
        by_id[sid] = step
        order_index[sid] = index

        skill = step.get("skill")
        if not isinstance(skill, str) or not IDENT.fullmatch(skill):
            errors.append(f"{sid}: skill must be a lowercase skill identifier")
        elif not (root / ".agent" / "skills" / skill / "SKILL.md").is_file():
            errors.append(f"{sid}: missing skill package {skill!r}")

        tools = step.get("tools", [])
        if not isinstance(tools, list):
            errors.append(f"{sid}: tools must be an array")
            tools = []
        for tool in tools:
            if not isinstance(tool, str) or not tool.startswith(".agent/tools/"):
                errors.append(f"{sid}: tool must be a repository-relative path under .agent/tools/: {tool!r}")
                continue
            resolved = contained_path(root, tool)
            if resolved is None or not resolved.is_file():
                errors.append(f"{sid}: missing or unsafe tool path {tool!r}")

        deps = step.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            errors.append(f"{sid}: depends_on must be an array of strings")
        elif len(deps) != len(set(deps)):
            errors.append(f"{sid}: duplicate dependency declaration")

    indegree = {sid: 0 for sid in by_id}
    children = {sid: [] for sid in by_id}
    for sid, step in by_id.items():
        deps = step.get("depends_on", [])
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if dep not in by_id:
                errors.append(f"{sid}: unknown dependency {dep!r}")
            else:
                indegree[sid] += 1
                children[dep].append(sid)

    ready = sorted((sid for sid, degree in indegree.items() if degree == 0), key=order_index.get)
    ordered: list[str] = []
    while ready:
        sid = ready.pop(0)
        ordered.append(sid)
        for child in sorted(children[sid], key=order_index.get):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort(key=order_index.get)
    if len(ordered) != len(by_id):
        errors.append("dependency graph contains a cycle")

    return {
        "ok": not errors,
        "workflow_id": workflow_id,
        "version": manifest.get("version"),
        "order": ordered if not errors else [],
        "step_count": len(by_id),
        "errors": errors,
        "execution_performed": False
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"cannot load manifest: {exc}"]}, indent=2))
        return 2
    if not isinstance(manifest, dict):
        print(json.dumps({"ok": False, "errors": ["manifest root must be an object"]}, indent=2))
        return 2
    result = compose(manifest, args.root.resolve())
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
