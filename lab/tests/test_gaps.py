import pandas as pd
import pytest

from sx_core.contracts import Candle
from sx_lab.features import make_dataset
from sx_lab.features.volatility import FeatureInputError
from sx_lab.features.gaps import GapPolicyError, make_gap_aware_dataset
from lab_fixtures import _synth_candles  # noqa: F401

W = (3, 6, 12, 24, 72, 120)


def test_equals_make_dataset_without_gaps(synth_candles):
    pd.testing.assert_frame_equal(make_dataset(synth_candles, 24, W),
                                  make_gap_aware_dataset(synth_candles, 24, W))


def _with_weekend(cs: list[Candle]) -> list[Candle]:
    """Remove Fri 21:00 .. Sun 22:00 UTC bars, a normal FX weekend closure."""
    return [c for c in cs if not (
        (c.time.weekday() == 4 and c.time.hour >= 21) or c.time.weekday() == 5
        or (c.time.weekday() == 6 and c.time.hour <= 22))]


def test_weekend_return_is_excluded_and_windows_count_traded_bars(synth_candles):
    cs = _with_weekend(synth_candles)
    ds = make_gap_aware_dataset(cs, 24, W)
    step = pd.Timedelta(hours=1)
    gap_bars = [c.time for a, c in zip(cs, cs[1:], strict=False) if c.time - a.time > step]
    assert gap_bars, "fixture must contain gaps"
    idx = pd.DatetimeIndex(ds.index)
    assert not any(t in idx for t in gap_bars)          # the first bar after a gap is no row
    assert ds["ret"].abs().max() < 0.05                   # no weekend-sized return survived
    # target window = 24 valid bars: its known_at is the close of the 24th valid return's bar
    times = [c.time for c in cs]
    t0 = ds.index[0]
    pos = times.index(t0)
    valid = [t for a, t in zip(times, times[1:], strict=False) if t - a == step]
    nxt = [t for t in valid if t > t0][23]
    assert ds.loc[t0, "target_known_at"] == nxt + step
    assert times[pos] == t0


def test_known_at_never_before_row_time_and_targets_after(synth_candles):
    ds = make_gap_aware_dataset(_with_weekend(synth_candles), 24, W)
    assert (ds["target_known_at"] > ds["known_at"]).all()
    assert ds["known_at"].is_monotonic_increasing


def test_unexpected_long_gap_is_refused(synth_candles):
    cs = synth_candles[:200] + synth_candles[220:]       # 20 missing hours, a Tuesday
    with pytest.raises(GapPolicyError, match="unexpected gap"):
        make_gap_aware_dataset(cs, 24, W)


def test_duplicate_bar_is_refused(synth_candles):
    cs = synth_candles[:100] + [synth_candles[99]] + synth_candles[100:]
    with pytest.raises(FeatureInputError, match="increasing"):
        make_gap_aware_dataset(cs, 24, W)

