import json

import pytest

from sx_core.contracts import Candle
from sx_core.storage import candles_to_frame, data_version, read_parquet
from sx_data.history import LABEL_OANDA, fetch_history
from sx_data.importer import ImportRefused, finalize_dataset, read_provenance
from sx_lab.spec import refuse_blocked_label


@pytest.fixture
def candles(fixtures_dir):
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return [Candle.model_validate(r) for r in raw]


class FakeSource:
    def __init__(self, candles):
        self.candles, self.calls = candles, []

    def fetch_candles(self, instrument, tf, start, end):
        self.calls.append((instrument, tf, start, end))
        return self.candles


def test_history_writes_dataset_with_honest_provenance(tmp_path, candles):
    src = FakeSource(candles)
    res = fetch_history(src, "EUR_USD", "H1", candles[0].time, candles[-1].time)
    prov = finalize_dataset(tmp_path / "o.parquet", res.candles, res.provenance)
    assert prov["label"] == LABEL_OANDA and prov["verified"] is False
    assert prov["assumed_complete"] is False and "mid" in prov["price_basis"]
    assert prov["data_version"] == data_version(candles_to_frame(candles))
    assert read_provenance(tmp_path / "o.parquet")["n_bars"] == len(candles)
    assert len(read_parquet(tmp_path / "o.parquet")) == len(candles)
    refuse_blocked_label(prov["label"])          # the L11 gate accepts a practice-feed label
    assert src.calls[0][:2] == ("EUR_USD", "H1")


def test_history_refuses_empty_and_degraded(candles):
    with pytest.raises(ImportRefused, match="no candles"):
        fetch_history(FakeSource([]), "EUR_USD", "H1", candles[0].time, candles[-1].time)
    gap = candles[:200] + candles[220:]
    with pytest.raises(ImportRefused, match="quality"):
        fetch_history(FakeSource(gap), "EUR_USD", "H1", candles[0].time, candles[-1].time)


def test_history_refuses_a_download_that_stops_early(candles):
    from datetime import timedelta
    src = FakeSource(candles[:500])
    with pytest.raises(ImportRefused, match="stopped early"):
        fetch_history(src, "EUR_USD", "H1", candles[0].time, candles[-1].time,
                      now=candles[-1].time)
    with pytest.raises(ImportRefused, match="starts late"):
        fetch_history(FakeSource(candles), "EUR_USD", "H1",
                      candles[0].time - timedelta(days=30), candles[-1].time,
                      now=candles[-1].time)
