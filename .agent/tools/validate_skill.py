#!/usr/bin/env python3
"""Standard-library structural lint for HARĒNA SKILL.md packages.

This checks frontmatter identity and required headings only. It does not prove
semantic quality, factual truth, safety, runtime discovery, or execution.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALIASES = {
    "purpose": {"purpose"},
    "activation": {"activation", "trigger", "triggers", "when to use"},
    "inputs": {"inputs", "input", "preconditions", "inputs and preconditions"},
    "procedure": {"procedure", "workflow", "required workflow", "steps"},
    "outputs": {"outputs", "output", "deliverables", "output format"},
    "failure handling": {"failure handling", "failure handling and stop conditions", "stop conditions"},
    "acceptance criteria": {"acceptance criteria", "acceptance checklist", "verification checklist"},
}

def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["missing YAML frontmatter opening delimiter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["missing YAML frontmatter closing delimiter"]
    fields: dict[str, str] = {}
    for number, line in enumerate(text[4:end].splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"frontmatter line {number}: expected key: value")
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        if not key:
            errors.append(f"frontmatter line {number}: empty key")
        elif key in fields:
            errors.append(f"duplicate frontmatter key: {key}")
        else:
            fields[key] = value
    return fields, errors

def validate(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read UTF-8 file: {exc}"]
    fields, errors = parse_frontmatter(content)
    name = fields.get("name", "")
    if not name:
        errors.append("frontmatter missing name")
    elif not NAME_RE.fullmatch(name):
        errors.append(f"invalid kebab-case name: {name!r}")
    elif path.parent.name != name:
        errors.append(f"name {name!r} does not match directory {path.parent.name!r}")
    if not fields.get("description", "").strip():
        errors.append("frontmatter missing description")
    headings = {
        re.sub(r"\s+", " ", match.group(1).strip().lower())
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", content, re.M)
    }
    for section, accepted in ALIASES.items():
        if not headings.intersection(accepted):
            errors.append(f"missing required heading: {section}")
    if len(content.strip()) < 250:
        errors.append("skill is unusually short")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="SKILL.md file or skills directory")
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args()
    if not args.path.exists():
        results = [{"path": str(args.path), "errors": ["path does not exist"]}]
    else:
        paths = [args.path] if args.path.is_file() else sorted(args.path.rglob("SKILL.md"))
        results = [{"path": str(p), "errors": validate(p)} for p in paths]
        if not paths:
            results = [{"path": str(args.path), "errors": ["no SKILL.md files found"]}]
    ok = all(not item["errors"] for item in results)
    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    else:
        for item in results:
            print(("PASS " if not item["errors"] else "FAIL ") + item["path"])
            for error in item["errors"]:
                print("  - " + error)
        print(f"RESULT: {'PASS' if ok else 'FAIL'} ({len(results)} file(s))")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
