import json
import math

import pytest

from sx_core.config import TradingModeError
from sx_lab import cli
from sx_lab.baselines import HAR, HistoricalMean
from sx_lab.partition import LabPartition
from sx_lab.records import make_forecasts
from lab_fixtures import _dataset  # noqa: F401

FIX = "tests/fixtures/lab/eurusd_h1_synth_1000.json"


def test_forecast_records_are_valid_and_honest(dataset):
    p = LabPartition(dataset, horizon=24)
    tr, va = p.train(), p.validation()
    fc = make_forecasts(HAR().fit(tr), HistoricalMean().fit(tr), tr, va,
                        instrument="EUR_USD", tf="H1", variants_tried=7)
    assert len(fc) == len(va) and len({f.id for f in fc}) == len(fc)
    f = fc[0]
    assert f.status == "exploratory" and f.target == "realized_vol"
    assert f.interval.low <= f.point <= f.interval.high and f.issued_at < f.horizon_end
    assert f.track_record.variants_tried == 7 and 0 <= f.track_record.empirical_coverage <= 1
    assert f.baseline_comparison.baseline == "historical_mean"
    wire = json.dumps(f.to_wire())
    assert "NaN" not in wire and math.isfinite(f.point)


@pytest.fixture
def paper(monkeypatch):
    monkeypatch.setenv("SX_TRADING_MODE", "paper")


def _args(cmd, tmp_path, *extra):
    return [cmd, "--candles", FIX, "--out", str(tmp_path / "o"),
            "--ledger", str(tmp_path / "l.jsonl"), "--dotenv", str(tmp_path / "none.env"), *extra]


def test_cli_refuses_live_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("SX_TRADING_MODE", "live")
    with pytest.raises(TradingModeError):
        cli.main(_args("evaluate", tmp_path))


def test_cli_run_search_evaluate_report(paper, tmp_path, capsys):
    assert cli.main(_args("run", tmp_path)) == 0
    out = next((tmp_path / "o").iterdir())
    recs = json.loads((out / "forecasts_har.json").read_text())
    assert recs and recs[0]["status"] == "exploratory"
    assert cli.main(_args("search", tmp_path, "--trials", "4")) == 0
    assert cli.main(_args("evaluate", tmp_path)) == 0
    ev = json.loads((out / "evaluation.json").read_text())
    assert ev["holdout"] == "sealed" and ev["variants"]["trials"] == 4
    assert "Not validated" in ev["labels"] and ev["data_label"].startswith("SAMPLE DATA")
    assert set(ev["scores"]) == {"historical_mean", "persistence", "har", "garch11"}
    capsys.readouterr()
    assert cli.main(_args("report", tmp_path)) == 0
    assert "variants" in capsys.readouterr().out
