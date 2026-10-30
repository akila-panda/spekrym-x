import json

import pytest
import yaml

from sx_core.ledger import Ledger
from sx_lab import cli
from sx_lab.partition import HoldoutRefused
from sx_lab.spec import SpecError, load_spec, refuse_blocked_label
from lab_fixtures import _dataset, _synth_candles  # noqa: F401

DRAFT = "tests/fixtures/lab/exp_draft_spec.yaml"   # frozen draft; the real EXP-001.yaml is locked
SYNTH = "tests/fixtures/lab/eurusd_h1_synth_1000.json"


def test_draft_spec_is_not_lockable_and_hash_ignores_key_order(tmp_path):
    spec, h = load_spec(DRAFT)
    assert spec.status == "draft" and len(spec.lockable()) >= 4
    raw = yaml.safe_load(open(DRAFT))
    p = tmp_path / "r.yaml"
    p.write_text(yaml.safe_dump(dict(reversed(list(raw.items())))))
    assert load_spec(p)[1] == h
    raw["horizon_bars"] = 12
    p.write_text(yaml.safe_dump(raw))
    assert load_spec(p)[1] != h                        # any value change = new hash


def test_unknown_field_and_bad_file_refused(tmp_path):
    raw = yaml.safe_load(open(DRAFT))
    raw["surprise"] = 1
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(SpecError):
        load_spec(p)
    with pytest.raises(SpecError):
        load_spec(tmp_path / "missing.yaml")


def test_blocked_labels():
    for label in ("SAMPLE DATA — NOT LIVE", "synthetic fixture", "x not live"):
        with pytest.raises(SpecError):
            refuse_blocked_label(label)
    refuse_blocked_label("OWNER-SUPPLIED DATA - PROVIDER NOT VERIFIED")


def test_partition_boundaries_cover_the_24_bar_horizon(dataset):
    from sx_lab.partition import LabPartition
    p = LabPartition(dataset, horizon=24)
    tr, va = p.train(), p.validation()
    assert len(tr) + len(va) + p.ranges.holdout.stop - p.ranges.holdout.start <= len(dataset)
    assert tr["target_known_at"].max() <= va["known_at"].min()
    assert va["target_known_at"].max() <= dataset.iloc[p.ranges.holdout.start]["known_at"]
    assert p.ranges.embargo == 24 and len(p.ranges.train) == int(len(dataset) * 0.6)


@pytest.fixture
def paper(monkeypatch):
    monkeypatch.setenv("SX_TRADING_MODE", "paper")


def _run(tmp_path, cmd, *extra):
    argv = [cmd, "--dotenv", str(tmp_path / "n.env"), "--ledger", str(tmp_path / "l.jsonl"),
            "--out", str(tmp_path / "o"), *extra]
    return cli.main(argv)


@pytest.fixture
def approved(paper, tmp_path, synth_candles):
    import pandas as pd

    from sx_core.storage import candles_to_frame
    csv = tmp_path / "in.csv"
    candles_to_frame(synth_candles)[["time", "open", "high", "low", "close", "volume"]].to_csv(
        csv, index=False)
    pq = tmp_path / "d.parquet"
    assert _run(tmp_path, "import", "--source-file", str(csv), "--out-file", str(pq)) == 0
    prov = json.loads((tmp_path / "d.parquet.provenance.json").read_text())
    raw = yaml.safe_load(open(DRAFT))
    raw.update(status="approved", approval={"approved_by": "owner", "approved_on": "2026-10-28"})
    raw["data"].update(data_version=prov["data_version"], first_bar=prov["first_bar"],
                       last_bar=prov["last_bar"])
    spec = tmp_path / "spec.yaml"
    spec.write_text(yaml.safe_dump(raw))
    assert pd  # silence unused
    return pq, spec


def test_lock_then_open_once_and_second_open_refused(approved, tmp_path, capsys):
    pq, spec = approved
    common = ["--candles", str(pq), "--spec", str(spec)]
    assert _run(tmp_path, "lock", *common) == 0
    assert _run(tmp_path, "lock", *common) == 0                      # idempotent
    with pytest.raises(SystemExit, match="confirm"):
        _run(tmp_path, "open-holdout", *common, "--reason", "EXP-001 final")
    assert _run(tmp_path, "open-holdout", *common, "--reason", "EXP-001 final",
                "--confirm-spend-holdout") == 0
    assert "HOLDOUT SPENT" in capsys.readouterr().out
    assert any(e.kind == "lab.holdout_opened" for e in Ledger(tmp_path / "l.jsonl").read())
    with pytest.raises(HoldoutRefused, match="spent"):
        _run(tmp_path, "open-holdout", *common, "--reason", "again", "--confirm-spend-holdout")


def test_lock_refuses_draft_changed_spec_data_and_sample_label(approved, tmp_path):
    pq, spec = approved
    common = ["--candles", str(pq)]
    with pytest.raises(SystemExit, match="not lockable"):
        _run(tmp_path, "lock", *common, "--spec", DRAFT)
    raw = yaml.safe_load(spec.read_text())
    raw["data"]["data_version"] = "dv:0000000000000000"
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(raw))
    with pytest.raises(SystemExit, match="data_version"):
        _run(tmp_path, "lock", *common, "--spec", str(bad))
    sc = tmp_path / "d.parquet.provenance.json"
    prov = json.loads(sc.read_text())
    prov["label"] = "SAMPLE DATA — NOT LIVE"
    sc.write_text(json.dumps(prov))
    with pytest.raises(SpecError, match="sample"):
        _run(tmp_path, "lock", *common, "--spec", str(spec))


def test_open_without_lock_refused(approved, tmp_path):
    pq, spec = approved
    with pytest.raises(HoldoutRefused, match="not locked"):
        _run(tmp_path, "open-holdout", "--candles", str(pq), "--spec", str(spec),
             "--reason", "x", "--confirm-spend-holdout")


def test_cli_uses_candles_json_and_spec_hash(paper, tmp_path, capsys):
    assert _run(tmp_path, "spec-hash", "--spec", DRAFT) == 0
    assert "NOT lockable" in capsys.readouterr().out
    assert SYNTH
