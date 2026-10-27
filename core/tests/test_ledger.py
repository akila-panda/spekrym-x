import json
from datetime import UTC, datetime

import pytest

from sx_core.ledger import GENESIS, Ledger, LedgerError, canonical_json, compute_hash

TS = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger.jsonl", now=lambda: TS)


def fill(ledger, n=3):
    return [ledger.append("order", {"i": i, "px": 1.0861 + i}, "dv:1", "r1") for i in range(n)]


def test_reading_missing_ledger_is_empty_and_creates_nothing(ledger):
    assert ledger.read() == [] and ledger.verify() == 0 and ledger.head() == GENESIS
    assert not ledger.path.exists()


def test_append_chains_hashes_and_verifies(ledger):
    entries = fill(ledger)
    assert ledger.verify() == 3
    assert entries[0].hash == compute_hash(GENESIS, json.loads(canonical_json({
        "ts": "2026-10-19T12:00:00Z", "kind": "order", "payload": {"i": 0, "px": 1.0861},
        "data_version": "dv:1", "rules_version": "r1"})))
    assert ledger.read() == entries and ledger.head() == entries[-1].hash


def test_append_only_earlier_bytes_never_change(ledger):
    fill(ledger, 2)
    before = ledger.path.read_bytes()
    ledger.append("fill", {"ok": True}, "dv:1")
    after = ledger.path.read_bytes()
    assert after.startswith(before) and len(after) > len(before)


def test_reads_do_not_mutate(ledger):
    fill(ledger)
    snap = (ledger.path.read_bytes(), ledger.path.stat().st_mtime_ns)
    ledger.read(), ledger.verify(), ledger.head()
    assert (ledger.path.read_bytes(), ledger.path.stat().st_mtime_ns) == snap


def test_there_is_no_update_or_delete_api(ledger):
    public = {n for n in dir(ledger) if not n.startswith("_")}
    assert public == {"path", "read", "verify", "head", "append"}


def lines(ledger):
    return ledger.path.read_text().splitlines()


def write(ledger, ls):
    ledger.path.write_text("\n".join(ls) + "\n")


def test_edited_payload_is_detected(ledger):
    fill(ledger)
    ls = lines(ledger)
    ls[1] = ls[1].replace('"i":1', '"i":99')
    write(ledger, ls)
    with pytest.raises(LedgerError, match="line 2"):
        ledger.verify()


def test_deleted_entry_is_detected(ledger):
    fill(ledger)
    ls = lines(ledger)
    del ls[1]
    write(ledger, ls)
    with pytest.raises(LedgerError, match="line 2"):
        ledger.verify()


def test_reordered_entries_are_detected(ledger):
    fill(ledger)
    ls = lines(ledger)
    ls[0], ls[1] = ls[1], ls[0]
    write(ledger, ls)
    with pytest.raises(LedgerError, match="line 1"):
        ledger.verify()


def test_deleting_the_first_entry_is_detected(ledger):
    fill(ledger)
    write(ledger, lines(ledger)[1:])
    with pytest.raises(LedgerError, match="line 1"):
        ledger.verify()


def test_torn_final_line_is_reported_and_blocks_append(ledger):
    fill(ledger, 2)
    with ledger.path.open("ab") as f:
        f.write(b'{"ts":"2026-10-19T12:00:0')
    with pytest.raises(LedgerError, match="incomplete"):
        ledger.read()
    with pytest.raises(LedgerError, match="refusing"):
        ledger.append("x", {}, "dv:1")


def test_tampered_tail_blocks_append(ledger):
    fill(ledger, 2)
    ls = lines(ledger)
    ls[-1] = ls[-1].replace('"i":1', '"i":7')
    write(ledger, ls)
    before = ledger.path.read_bytes()
    with pytest.raises(LedgerError, match="refusing"):
        ledger.append("x", {}, "dv:1")
    assert ledger.path.read_bytes() == before


@pytest.mark.parametrize("payload", [{"bad": float("nan")}, {"when": TS}, {"s": {1, 2}}])
def test_non_json_payload_refused_and_nothing_written(ledger, payload):
    with pytest.raises((TypeError, ValueError)):
        ledger.append("x", payload, "dv:1")
    assert not ledger.path.exists() or ledger.read() == []


def test_empty_kind_refused(ledger):
    with pytest.raises(ValueError):
        ledger.append("", {}, "dv:1")


def test_timestamps_are_utc_z_and_default_clock_is_used(tmp_path):
    e = Ledger(tmp_path / "l.jsonl").append("x", {}, "dv:1")
    assert e.ts.tzinfo is not None
    assert json.loads(Ledger(tmp_path / "l.jsonl").path.read_text())["ts"].endswith("Z")


def test_payload_key_order_does_not_change_hash(tmp_path):
    a = Ledger(tmp_path / "a.jsonl", now=lambda: TS).append("x", {"a": 1, "b": 2}, "dv:1")
    b = Ledger(tmp_path / "b.jsonl", now=lambda: TS).append("x", {"b": 2, "a": 1}, "dv:1")
    assert a.hash == b.hash


def test_second_ledger_instance_continues_the_chain(tmp_path):
    first = Ledger(tmp_path / "l.jsonl", now=lambda: TS)
    fill(first, 2)
    Ledger(tmp_path / "l.jsonl", now=lambda: TS).append("more", {}, "dv:1")
    assert first.verify() == 3


def test_unset_rules_version_is_omitted_and_payload_nulls_are_kept(ledger):
    e = ledger.append("note", {"a": None}, "dv:1")
    line = json.loads(ledger.path.read_text())
    assert "rules_version" not in line and line["payload"] == {"a": None}
    assert e.rules_version is None and ledger.verify() == 1
    assert ledger.read()[0].to_wire() == line
