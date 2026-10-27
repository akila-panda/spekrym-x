"""The numpy ports in ``smc_fast`` must equal the real library, prefix by prefix (issue 27).

The library is the oracle. Random series use a coarse price grid on purpose, so equal highs,
equal lows, ties and flat bars are common (the library's tie-breaking is where a port breaks).
"""

import random
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from sx_assistant.ta import smc_fast
from sx_assistant.ta.common import to_frame
from sx_assistant.ta.smc_adapter import smc, smc_setups
from sx_core.contracts import Candle

T0 = datetime(2026, 10, 19, tzinfo=UTC)


def random_series(seed: int, n: int, tick: float) -> list[Candle]:
    rng = random.Random(seed)
    px, out = 1.1, []
    for i in range(n):
        o = round(px / tick) * tick
        c = round((o + rng.gauss(0, 3 * tick)) / tick) * tick
        hi = max(o, c) + rng.choice([0, 0, tick, 2 * tick]) * 1.0
        lo = min(o, c) - rng.choice([0, 0, tick, 2 * tick]) * 1.0
        px = c
        out.append(Candle(instrument="EUR_USD", tf="M15", time=T0 + timedelta(minutes=15 * i),
                          open=o, high=hi, low=lo, close=c, volume=float(rng.randint(1, 9)),
                          bid_close=c, ask_close=c, complete=True))
    return out


SERIES = [(seed, 48, tick) for seed in range(8) for tick in (0.0005, 0.00001)]


def same(a: np.ndarray, b: np.ndarray) -> bool:
    return a.shape == b.shape and bool(np.array_equal(a, b, equal_nan=True))


@pytest.mark.parametrize("seed,n,tick", SERIES)
@pytest.mark.parametrize("length", [1, 2, 3])
def test_swings_and_bos_choch_equal_the_library_on_every_prefix(seed, n, tick, length):
    df = to_frame(random_series(seed, n, tick))
    for k in range(1, n + 1):
        p = df.iloc[:k].reset_index(drop=True)
        sw = smc.swing_highs_lows(p, swing_length=length)
        sw.loc[[0, k - 1], ["HighLow", "Level"]] = np.nan       # what the adapter does
        h, lo, c = (p[x].to_numpy() for x in ("high", "low", "close"))
        hl, lvl = smc_fast.swings(h, lo, length)
        assert same(hl, sw["HighLow"].to_numpy()), (seed, k)
        assert same(lvl, sw["Level"].to_numpy()), (seed, k)
        if np.isnan(hl).all():
            continue
        lib = smc.bos_choch(p, sw)
        got = smc_fast.bos_choch(c, hl, lvl)
        for name, arr in zip(("BOS", "CHOCH", "Level", "BrokenIndex"), got, strict=True):
            assert same(arr, lib[name].to_numpy()), (seed, k, name)
            assert arr.dtype == lib[name].to_numpy().dtype, (seed, k, name)


@pytest.mark.parametrize("seed,n,tick", SERIES)
def test_fvg_at_equals_the_gap_the_library_adds_with_the_newest_bar(seed, n, tick):
    df = to_frame(random_series(seed, n, tick))
    for k in range(3, n + 1):
        p = df.iloc[:k].reset_index(drop=True)
        f = smc.fvg(p)
        j = k - 2
        lib = None if np.isnan(f["FVG"].iloc[j]) else (
            int(f["FVG"].iloc[j]), float(f["Top"].iloc[j]), float(f["Bottom"].iloc[j]))
        o, h, lo, c = (p[x].to_numpy() for x in ("open", "high", "low", "close"))
        assert smc_fast.fvg_at(o, h, lo, c) == lib, (seed, k)
        # the claim the incremental form rests on: nothing older changes when a bar is added
        older = f["FVG"].iloc[:j].to_numpy()
        prev = smc.fvg(df.iloc[:k - 1].reset_index(drop=True))["FVG"].iloc[:j].to_numpy()
        assert same(older, prev), (seed, k)


@pytest.mark.parametrize("seed,n,tick", [(s, 40, t) for s in range(4) for t in (0.0005, 0.00001)])
@pytest.mark.parametrize("length", [1, 2, 3])
def test_fast_and_library_engines_give_identical_setups(seed, n, tick, length):
    cs = random_series(seed, n, tick)
    fast = smc_setups(cs, swing_length=length, engine="fast")
    ref = smc_setups(cs, swing_length=length, engine="library")
    assert fast == ref and len(ref) > 0


def test_engines_agree_on_the_frozen_fixtures(day, m15_candles, liq):
    for cs, length in ((day, 2), (m15_candles, 3), (liq["candles"], 2)):
        assert smc_setups(cs, swing_length=length) == smc_setups(
            cs, swing_length=length, engine="library")


def test_unknown_engine_is_rejected(day):
    with pytest.raises(ValueError, match="engine"):
        smc_setups(day, engine="turbo")


def test_series_shorter_than_three_windows_have_no_swings():
    h = np.array([1.0, 2.0, 1.5, 1.7])
    hl, lvl = smc_fast.swings(h, h - 0.1, 2)
    assert np.isnan(hl).all() and np.isnan(lvl).all()
