from datetime import date

import pytest

from arena_agent.ids import (
    IdKind,
    InvalidArenaId,
    new_dated_seq_id,
    new_generic_id,
    parse_dated_seq_id,
    validate_dated_seq_id,
    validate_generic_id,
)


def test_new_generic_id_normalizes_parts():
    assert new_generic_id("repo", "core crate", "status!!") == "ARENA-REPO-CORE-CRATE-STATUS"


def test_generic_id_validation_rejects_short_ids():
    with pytest.raises(InvalidArenaId):
        validate_generic_id("ARENA-ONLY")


def test_dated_seq_id_generation_avoids_collisions():
    on = date(2026, 9, 5)
    first = new_dated_seq_id(IdKind.DECISION, existing_ids=set(), on=on)
    assert first == "ARENA-DECISION-20260905-001"
    second = new_dated_seq_id(IdKind.DECISION, existing_ids={first}, on=on)
    assert second == "ARENA-DECISION-20260905-002"


def test_dated_seq_id_validation_and_parsing():
    validate_dated_seq_id("ARENA-CE-20260905-003", IdKind.CE)
    parsed = parse_dated_seq_id("ARENA-CE-20260905-003")
    assert parsed.kind == "CE"
    assert parsed.seq == 3
    assert parsed.on == date(2026, 9, 5)


def test_dated_seq_id_wrong_kind_rejected():
    with pytest.raises(InvalidArenaId):
        validate_dated_seq_id("ARENA-CE-20260905-003", IdKind.DECISION)


def test_dated_seq_id_bad_date_rejected():
    with pytest.raises(InvalidArenaId):
        validate_dated_seq_id("ARENA-CE-20261399-003", IdKind.CE)
