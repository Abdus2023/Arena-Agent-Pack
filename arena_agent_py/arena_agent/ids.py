"""
Stable Arena Knowledge IDs.

Pack reference: v2 §8 / v1 §7 ("Stable Arena Knowledge IDs") plus the
per-record ID conventions scattered through v2 §26-40 (ARENA-DECISION-...,
ARENA-CE-..., ARENA-AUDIT-..., ARENA-IMPACT-..., ARENA-GRAPH-...).

Rule enforced here: "IDs must not be reused for materially different
obligations." This module can't detect *semantic* reuse, but it does:

  - validate the required ``ARENA-<...>`` shape,
  - generate collision-checked sequential IDs for date-stamped record types
    (decisions, counterexamples, audits, impact analyses, graphs) so two
    records created on the same day never silently collide,
  - keep ID generation pure/deterministic given an explicit "existing IDs"
    set, so it works the same whether backed by a JSON store or an
    in-memory set in a unit test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


_ARENA_ID_RE = re.compile(r"^ARENA-[A-Z0-9]+(-[A-Z0-9]+)+$")

#: Regex for the "<PREFIX>-<yyyymmdd>-<seq>" family of IDs used by Decision
#: Records, Counterexamples, Repo Audits, Change-Impact Analyses, and
#: Knowledge Graph snapshots.
_DATED_SEQ_RE = re.compile(r"^ARENA-(?P<kind>[A-Z]+)-(?P<date>\d{8})-(?P<seq>\d{3,})$")


class IdKind(str, Enum):
    """Which dated-sequential ID family a record belongs to."""

    DECISION = "DECISION"
    CE = "CE"  # counterexample
    AUDIT = "AUDIT"
    IMPACT = "IMPACT"
    GRAPH = "GRAPH"


class InvalidArenaId(ValueError):
    """Raised when a string does not conform to the ARENA-* ID grammar."""


def validate_generic_id(value: str) -> str:
    """
    Validate the general ``ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>`` shape
    (v2 §8). Requires at least two hyphen-separated segments after
    ``ARENA-``. Returns the value unchanged if valid.
    """
    if not _ARENA_ID_RE.match(value):
        raise InvalidArenaId(
            f"{value!r} does not match required shape "
            "'ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>' (at least ARENA-X-Y)."
        )
    return value


def validate_dated_seq_id(value: str, kind: IdKind) -> str:
    """Validate a dated-sequential ID (e.g. ``ARENA-DECISION-20260905-001``)."""
    m = _DATED_SEQ_RE.match(value)
    if not m or m.group("kind") != kind.value:
        raise InvalidArenaId(
            f"{value!r} is not a valid ARENA-{kind.value}-<yyyymmdd>-<seq> id."
        )
    try:
        datetime.strptime(m.group("date"), "%Y%m%d")
    except ValueError as exc:
        raise InvalidArenaId(f"{value!r} has an invalid date component.") from exc
    return value


def new_dated_seq_id(
    kind: IdKind,
    existing_ids: set[str] | None = None,
    on: date | None = None,
) -> str:
    """
    Generate the next free dated-sequential ID for ``kind`` on date ``on``
    (defaults to today), given the set of IDs already in use.

    This is deterministic and side-effect free: callers (e.g. the storage
    layer) are responsible for actually reserving/persisting the returned
    ID. This keeps ID generation testable without a filesystem.
    """
    existing_ids = existing_ids or set()
    on = on or date.today()
    date_str = on.strftime("%Y%m%d")
    seq = 1
    while True:
        candidate = f"ARENA-{kind.value}-{date_str}-{seq:03d}"
        if candidate not in existing_ids:
            return candidate
        seq += 1


def new_generic_id(domain: str, subject: str, prop: str) -> str:
    """
    Build a generic ``ARENA-<DOMAIN>-<SUBJECT>-<PROPERTY>`` id from parts,
    normalizing to upper-kebab segments. This is for Knowledge Units,
    invariants, and other named (not date-stamped) durable identifiers
    (v2 §8).
    """

    def norm(part: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]+", "-", part.strip()).strip("-").upper()
        if not cleaned:
            raise ValueError(f"Cannot build an ID segment from {part!r}.")
        return cleaned

    value = f"ARENA-{norm(domain)}-{norm(subject)}-{norm(prop)}"
    return validate_generic_id(value)


@dataclass(frozen=True)
class ParsedDatedId:
    kind: str
    on: date
    seq: int
    raw: str


def parse_dated_seq_id(value: str) -> ParsedDatedId:
    """Parse a dated-sequential ID into its components, or raise InvalidArenaId."""
    m = _DATED_SEQ_RE.match(value)
    if not m:
        raise InvalidArenaId(f"{value!r} is not a dated-sequential ARENA id.")
    on = datetime.strptime(m.group("date"), "%Y%m%d").date()
    return ParsedDatedId(kind=m.group("kind"), on=on, seq=int(m.group("seq")), raw=value)
