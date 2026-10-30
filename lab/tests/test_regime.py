import itertools

import numpy as np
import pandas as pd
import pytest

from sx_core.contracts import Candle
from sx_lab.regime.changepoints_offline import offline_changepoints, pelt_l2
from sx_lab.regime.markov_switching import RegimeFitError, RegimeModel

T0 = pd.Timestamp("2026-01-01", tz="UTC")


def _series(seed=0):
    rng = np.random.default_rng(seed)
    x = np.concatenate([rng.normal(-6, .3, 300), rng.normal(-4, .6, 300), rng.normal(-6, .3, 300)])
    return pd.Series(x, pd.date_range(T0, periods=len(x), freq="h"))


def test_filtered_probabilities_find_the_high_regime():
    s = _series()
    m = RegimeModel.fit(s.iloc[:450])
    p = m.filtered(s)
    assert np.allclose(p["p_low"] + p["p_high"], 1.0)
    assert p["p_high"].iloc[350:450].mean() > 0.9 and p["p_high"].iloc[:250].mean() < 0.1


def test_prefix_equality_with_the_phase2_harness(assert_causal):
    s = _series()
    model = RegimeModel.fit(s.iloc[:450])               # parameters from the past only
    by_time = {c: v for c, v in zip(s.index, s.to_numpy(), strict=True)}

    def producer(candles):
        ser = pd.Series([by_time[c.time] for c in candles], [c.time for c in candles])
        p = model.filtered(ser)["p_high"]
        return [{"id": str(t), "event_time": t.to_pydatetime(),
                 "known_at": t.to_pydatetime() + pd.Timedelta(hours=1), "p": round(float(v), 9)}
                for t, v in p.items()]

    candles = [Candle(instrument="EUR_USD", tf="H1", time=t, open=1.0, high=1.0, low=1.0,
                      close=1.0, volume=0.0, complete=True) for t in s.index[:200]]
    assert_causal(producer, candles, prefix_lengths=list(range(20, 201, 20)))


def test_fit_refuses_short_or_nonfinite():
    with pytest.raises(RegimeFitError):
        RegimeModel.fit(_series().iloc[:50])
    bad = _series().iloc[:300].copy()
    bad.iloc[5] = np.nan
    with pytest.raises(RegimeFitError):
        RegimeModel.fit(bad)


def test_changepoints_are_retrospective_and_found():
    rng = np.random.default_rng(0)
    x = np.concatenate([rng.normal(0, 1, 200), rng.normal(4, 1, 200)])
    s = pd.Series(x, pd.date_range(T0, periods=400, freq="h"))
    cp = offline_changepoints(s, penalty=50.0)
    assert cp.status == "retrospective" and len(cp.times) == 1
    assert abs((cp.times[0] - s.index[200]) / pd.Timedelta(hours=1)) <= 5
    with pytest.raises(ValueError):
        offline_changepoints(s, penalty=0)


def _objective(x, ends, pen):
    s, tot = 0, 0.0
    for e in ends:
        seg = x[s:e]
        tot += float(((seg - seg.mean()) ** 2).sum()) + pen
        s = e
    return tot


def _brute(x, pen, min_size):
    n, best = len(x), None
    for k in range(1, n // min_size + 1):
        for cuts in itertools.combinations(range(min_size, n - min_size + 1), k - 1):
            ends = [*cuts, n]
            if min(np.diff([0, *ends])) < min_size:
                continue
            o = _objective(x, ends, pen)
            if best is None or o < best[0]:
                best = (o, ends)
    return best


def test_pelt_matches_brute_force_exactly():
    for seed in range(6):
        rng = np.random.default_rng(seed)
        x = np.concatenate([rng.normal(0, 1, 8), rng.normal(3, 1, 8), rng.normal(0, 1, 8)])
        for pen in (1.0, 8.0, 40.0):
            o, _ = _brute(x, pen, 5)
            got = pelt_l2(x, pen, 5)
            assert _objective(x, got, pen) == pytest.approx(o) and got[-1] == len(x)


def test_pelt_never_worse_than_ruptures_when_installed():
    rpt = pytest.importorskip("ruptures")        # not installable on Python 3.14
    for seed in range(10):
        rng = np.random.default_rng(seed)
        x = np.concatenate([rng.normal(0, 1, 80), rng.normal(3, 1, 90)])
        theirs = rpt.Pelt(model="l2", min_size=10, jump=1).fit(x).predict(pen=20.0)
        assert _objective(x, pelt_l2(x, 20.0, 10), 20.0) <= _objective(x, theirs, 20.0) + 1e-9
