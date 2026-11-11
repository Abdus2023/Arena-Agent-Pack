#!/usr/bin/env python3
"""Validate JSON instances against Draft 2020-12 schemas.

This performs schema meta-validation and instance validation. It does not prove
that the data is factually correct or that referenced resources exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_instances(schema_path: Path, instance_paths: list[Path]) -> dict[str, Any]:
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        return {
            "ok": False,
            "schema": str(schema_path),
            "errors": [f"invalid or unreadable Draft 2020-12 schema: {exc}"],
            "instances": [],
        }

    validator = Draft202012Validator(schema)
    results: list[dict[str, Any]] = []
    for path in instance_paths:
        try:
            instance = load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            results.append({"path": str(path), "ok": False, "errors": [f"cannot load JSON: {exc}"]})
            continue
        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: (list(error.absolute_path), error.message),
        )
        results.append({
            "path": str(path),
            "ok": not errors,
            "errors": [
                {
                    "instance_path": "/" + "/".join(str(part) for part in error.absolute_path),
                    "message": error.message,
                }
                for error in errors
            ],
        })

    return {
        "ok": all(item["ok"] for item in results),
        "schema": str(schema_path),
        "draft": "2020-12",
        "instances": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("instances", nargs="+", type=Path)
    args = parser.parse_args()
    result = validate_instances(args.schema, args.instances)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        schema_error = bool(result["errors"])
        return 2 if schema_error else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
