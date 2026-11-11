#!/usr/bin/env python3
"""Validate a small evidence ledger without asserting that its claims are true."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

CLAIM_STATUS = {"PROVED", "ARGUMENT", "CONJECTURE", "OPEN"}
VERIFY_STATUS = {"VERIFIED", "PARTIALLY_VERIFIED", "PROVISIONAL", "BLOCKED"}

def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = data.get("sources")
    claims = data.get("claims")
    if not isinstance(sources, list) or not isinstance(claims, list):
        return ["sources and claims must both be arrays"]
    source_ids: set[str] = set()
    claim_ids: set[str] = set()
    for i, source in enumerate(sources):
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            errors.append(f"sources[{i}] must be an object with string id")
            continue
        sid = source["id"]
        if sid in source_ids:
            errors.append(f"duplicate source id: {sid}")
        source_ids.add(sid)
        if not source.get("uri"):
            errors.append(f"{sid}: uri is required")
    for i, claim in enumerate(claims):
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
            errors.append(f"claims[{i}] must be an object with string id")
            continue
        cid = claim["id"]
        if cid in claim_ids:
            errors.append(f"duplicate claim id: {cid}")
        claim_ids.add(cid)
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            errors.append(f"{cid}: statement is required")
        epistemic = claim.get("claim_status")
        verification = claim.get("verification_status")
        if epistemic not in CLAIM_STATUS:
            errors.append(f"{cid}: invalid claim_status {epistemic!r}")
        if verification not in VERIFY_STATUS:
            errors.append(f"{cid}: invalid verification_status {verification!r}")
        refs = claim.get("source_ids", [])
        if not isinstance(refs, list):
            errors.append(f"{cid}: source_ids must be an array")
            refs = []
        for ref in refs:
            if ref not in source_ids:
                errors.append(f"{cid}: unresolved source_id {ref!r}")
        evidence = claim.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{cid}: evidence must be an array")
            evidence = []
        if verification == "VERIFIED" and (not refs or not evidence):
            errors.append(f"{cid}: VERIFIED requires source_ids and evidence")
        if epistemic == "PROVED" and verification != "VERIFIED":
            errors.append(f"{cid}: PROVED requires verification_status VERIFIED")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.ledger.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"cannot load ledger: {exc}"]}, indent=2))
        return 2
    errors = validate(data)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
