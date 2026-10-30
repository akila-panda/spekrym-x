import json

import pandas as pd
import pytest

from sx_core.contracts import Candle
from sx_core.storage import candles_to_frame, data_version
from sx_data.importer import (LABEL_UNVERIFIED, ImportRefused, import_candles, read_provenance,
                              write_provenance)


@pytest.fixture
def candles(fixtures_dir):
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return [Candle.model_validate(r) for r in raw]


def _csv(tmp_path, candles, *, drop=None, naive=False, name="x.csv"):
    df = candles_to_frame(candles)[["time", "open", "high", "low", "close", "volume"]]
    if naive:
        df["time"] = df["time"].dt.tz_localize(None)
    if drop:
        df = df.drop(index=range(*drop))
    p = tmp_path / name
    df.to_csv(p, index=False)
    return p


def test_import_ok_has_honest_provenance(tmp_path, candles):
    r = import_candles(_csv(tmp_path, candles), instrument="EUR_USD", tf="H1", source="owner")
    assert len(r.candles) == len(candles) and not r.report.feed_degraded
    p = r.provenance
    assert p["label"] == LABEL_UNVERIFIED and p["verified"] is False
    assert p["assumed_complete"] is True and "LIVE" not in p["label"].replace("NOT", "")
    assert p["data_version"] == data_version(candles_to_frame(r.candles))


def test_naive_time_refused_unless_tz_given(tmp_path, candles):
    f = _csv(tmp_path, candles, naive=True)
    with pytest.raises(ImportRefused, match="timezone"):
        import_candles(f, instrument="EUR_USD", tf="H1", source="owner")
    r = import_candles(f, instrument="EUR_USD", tf="H1", source="owner", assume_tz="UTC")
    assert r.candles[0].time == candles[0].time


def test_missing_column_and_degraded_feed_refused(tmp_path, candles):
    bad = pd.read_csv(_csv(tmp_path, candles)).drop(columns=["close"])
    bad.to_csv(tmp_path / "b.csv", index=False)
    with pytest.raises(ImportRefused, match="cannot find column"):
        import_candles(tmp_path / "b.csv", instrument="EUR_USD", tf="H1", source="o")
    gap = _csv(tmp_path, candles, drop=(200, 220), name="g.csv")
    with pytest.raises(ImportRefused, match="quality"):
        import_candles(gap, instrument="EUR_USD", tf="H1", source="o")
    r = import_candles(gap, instrument="EUR_USD", tf="H1", source="o", accept_degraded=True)
    assert r.provenance["feed_degraded"] is True and r.provenance["unexpected_gaps"] == 1


def test_changed_file_invalidates_provenance(tmp_path, candles):
    f = _csv(tmp_path, candles)
    r = import_candles(f, instrument="EUR_USD", tf="H1", source="o")
    write_provenance(f, r.provenance)
    assert read_provenance(f)["n_bars"] == len(candles)
    f.write_text(f.read_text() + "\n")
    with pytest.raises(ImportRefused, match="changed"):
        read_provenance(f)


def _duka(tmp_path, candles, name, sl=slice(None), sep=","):
    """A file in a Dukascopy-like layout (header 'Gmt time', DD.MM.YYYY HH:MM:SS.000)."""
    df = candles_to_frame(candles[sl])[["time", "open", "high", "low", "close", "volume"]].copy()
    df["time"] = df["time"].dt.strftime("%d.%m.%Y %H:%M:%S.000")
    df.columns = ["Gmt time", "Open", "High", "Low", "Close", "Volume"]
    p = tmp_path / name
    df.to_csv(p, index=False, sep=sep)
    return p


def test_aliases_and_dayfirst_format_detected(tmp_path, candles):
    r = import_candles(_duka(tmp_path, candles, "d.csv"), instrument="EUR_USD", tf="H1",
                       source="o", assume_tz="UTC")
    assert r.candles[0].time == candles[0].time and len(r.candles) == len(candles)
    assert r.provenance["files"][0]["time_format"] == "%d.%m.%Y %H:%M:%S.%f"
    assert sum(r.provenance["bars_per_year"].values()) == len(candles)


def test_ambiguous_or_unknown_time_and_columns_refused(tmp_path, candles):
    p = tmp_path / "amb.csv"
    p.write_text("time,open,high,low,close\n01/02/2026 00:00:00,1,1.1,0.9,1\n"
                 "02/03/2026 01:00:00,1,1.1,0.9,1\n")
    with pytest.raises(ImportRefused, match="ambiguous"):
        import_candles(p, instrument="EUR_USD", tf="H1", source="o", assume_tz="UTC")
    r = import_candles(p, instrument="EUR_USD", tf="H1", source="o", assume_tz="UTC",
                       time_format="%d/%m/%Y %H:%M:%S", accept_degraded=True)
    assert r.candles[0].time.month == 2
    q = tmp_path / "bad.csv"
    q.write_text("when,px\n1,2\n")
    with pytest.raises(ImportRefused, match="columns seen"):
        import_candles(q, instrument="EUR_USD", tf="H1", source="o")


def test_two_files_merge_dedupe_overlap_and_refuse_conflict(tmp_path, candles):
    a = _duka(tmp_path, candles, "a.csv", slice(0, 600))
    b = _duka(tmp_path, candles, "b.csv", slice(500, None))      # 100 overlapping bars
    r = import_candles([b, a], instrument="EUR_USD", tf="H1", source="o", assume_tz="UTC")
    assert len(r.candles) == len(candles) and r.provenance["file"] == "2 files"
    assert r.provenance["data_version"] == data_version(candles_to_frame(candles))
    bad = pd.read_csv(b)
    bad.loc[3, "Close"] = bad.loc[3, "Close"] + 0.01
    bad.to_csv(tmp_path / "b2.csv", index=False)
    with pytest.raises(ImportRefused, match="different values"):
        import_candles([a, tmp_path / "b2.csv"], instrument="EUR_USD", tf="H1", source="o",
                       assume_tz="UTC")


def test_flat_bars_are_counted(tmp_path, candles):
    df = pd.read_csv(_duka(tmp_path, candles, "f.csv"))
    df.loc[10:14, ["Open", "High", "Low", "Close"]] = df.loc[9, "Close"]   # 5 filler bars
    df.to_csv(tmp_path / "f2.csv", index=False)
    r = import_candles(tmp_path / "f2.csv", instrument="EUR_USD", tf="H1", source="o",
                       assume_tz="UTC")
    assert r.provenance["flat_bars"] >= 5 and r.provenance["longest_flat_run"] >= 5
