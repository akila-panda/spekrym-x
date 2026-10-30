"""EXP-001 runner on the SYNTHETIC fixture with a shortened training config (8B).
Proves the plumbing and the guards, not any model quality. Skipped without torch."""

import argparse
import json

import pytest

pytest.importorskip("torch")
pytest.importorskip("minimamba")

from lab_fixtures import _dataset, _synth_candles  # noqa: E402, F401
from sx_core.ledger import Ledger  # noqa: E402
from sx_lab import exp001  # noqa: E402
from sx_lab.exp001_core import Exp001Refused, classify  # noqa: E402
from sx_lab.exp001_report import build_report  # noqa: E402
from sx_lab.models.minimamba_vol import TrainConfig  # noqa: E402
from sx_lab.partition import HoldoutRefused  # noqa: E402
from test_spec_lock import _run, approved, paper  # noqa: E402, F401


def test_classify_covers_every_case():
    assert classify(("minimamba",)) == "win"
    assert classify(("minimamba", "har")) == "tie"
    assert classify(("minimamba", "garch11", "har")) == "tie"
    assert classify(("har",)) == "loss"
    assert classify(("historical_mean",)) == "inconclusive"


@pytest.fixture
def ns(approved, tmp_path, monkeypatch):  # noqa: F811
    pq, spec = approved
    monkeypatch.setattr(exp001, "_cfg", lambda s: TrainConfig(epochs=1, context_bars=16))
    assert _run(tmp_path, "lock", "--candles", str(pq), "--spec", str(spec)) == 0
    return argparse.Namespace(spec=str(spec), candles=str(pq), ledger=str(tmp_path / "l.jsonl"),
                              out=str(tmp_path / "o"), reason="", confirm_spend_holdout=False)


def test_validate_then_one_shot_holdout_then_report(ns, tmp_path):
    ledger = Ledger(ns.ledger)
    res = exp001.run_validate(ns, log=lambda m: None)
    assert res["outcome"] in {"win", "tie", "loss", "inconclusive"}
    assert set(res["scores"]) == {"historical_mean", "persistence", "har", "garch11", "minimamba"}
    assert res["variants_tried"] == 3
    with pytest.raises(Exp001Refused, match="already ran"):
        exp001.run_validate(ns, log=lambda m: None)
    with pytest.raises(Exp001Refused, match="confirm-spend-holdout"):
        exp001.run_holdout(ns, log=lambda m: None)
    assert "(holdout not opened yet)" in build_report(tmp_path / "o" / "exp001")
    ns.reason, ns.confirm_spend_holdout = "EXP-001 test run", True
    hold = exp001.run_holdout(ns, log=lambda m: None)
    assert hold["n_holdout"] > 0 and (tmp_path / "o/exp001/holdout_frame.parquet").exists()
    assert ledger.verify() > 0
    with pytest.raises(HoldoutRefused):
        exp001.run_holdout(ns, log=lambda m: None)
    assert "Judged on the holdout" in build_report(tmp_path / "o" / "exp001")


def test_holdout_refuses_without_validation_and_after_tampering(ns, tmp_path):
    ns.reason, ns.confirm_spend_holdout = "x", True
    with pytest.raises(Exp001Refused, match="exp001-validate first"):
        exp001.run_holdout(ns, log=lambda m: None)
    exp001.run_validate(ns, log=lambda m: None)
    p = tmp_path / "o/exp001/validation_results.json"
    d = json.loads(p.read_text())
    d["outcome"] = "win"
    p.write_text(json.dumps(d))
    with pytest.raises(Exp001Refused, match="changed since"):
        exp001.run_holdout(ns, log=lambda m: None)
    assert Ledger(ns.ledger).verify() > 0
    assert not [e for e in Ledger(ns.ledger).read() if e.kind == "lab.holdout_opened"]


def test_runner_refuses_an_unlocked_spec(approved, tmp_path):  # noqa: F811
    pq, spec = approved
    ns = argparse.Namespace(spec=str(spec), candles=str(pq), ledger=str(tmp_path / "l.jsonl"),
                            out=str(tmp_path / "o"), reason="", confirm_spend_holdout=False)
    with pytest.raises(Exp001Refused, match="no lock"):
        exp001.run_validate(ns, log=lambda m: None)
