"""Causal volatility and session features (Phase 7A).

Row ``t`` is indexed by the bar's OPEN time and describes the information available at the bar's
CLOSE (``known_at``). Every feature at row ``t`` uses bars ``<= t`` only. The target is a
LABEL: the mean squared log return over the next ``h`` bars. It uses the future on purpose, is
never an input, and carries its own ``target_known_at`` so splits can be audited.

All variances are per-bar averages of squared close-to-close log returns, so features, target
and forecasts share one scale.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from sx_core.clock import tf_delta
from sx_core.contracts import Candle

DEFAULT_WINDOWS = (6, 24, 120)
ATR_PERIOD = 14


class FeatureInputError(ValueError):
    """The candles cannot be used (incomplete, unordered, mixed, or too short)."""


def _frame(candles: Sequence[Candle]) -> tuple[pd.DataFrame, str]:
    if not candles:
        raise FeatureInputError("no candles")
    tf, inst = candles[0].tf, candles[0].instrument
    if any(c.tf != tf or c.instrument != inst for c in candles):
        raise FeatureInputError("mixed instrument or timeframe")
    if not all(c.complete for c in candles):
        raise FeatureInputError("incomplete (forming) bar present; only closed bars are allowed")
    times = [c.time for c in candles]
    if any(b <= a for a, b in zip(times, times[1:], strict=False)):
        raise FeatureInputError("candles are not strictly increasing in time")
    df = pd.DataFrame({
        "open": [c.open for c in candles], "high": [c.high for c in candles],
        "low": [c.low for c in candles], "close": [c.close for c in candles],
    }, index=pd.DatetimeIndex(times, name="time"))
    return df, tf


def _tod(known_at: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    minutes = known_at.hour.to_numpy() * 60 + known_at.minute.to_numpy()
    angle = 2 * math.pi * minutes / 1440.0
    return np.sin(angle), np.cos(angle)


def build_features(candles: Sequence[Candle], windows: Sequence[int] = DEFAULT_WINDOWS
                   ) -> pd.DataFrame:
    """Causal features, one row per candle, NaN where the lookback is not yet filled."""
    df, tf = _frame(candles)
    delta = tf_delta(tf)
    r = np.log(df["close"] / df["close"].shift(1))
    out = pd.DataFrame(index=df.index)
    out["known_at"] = df.index + delta
    out["ret"] = r
    for w in windows:
        out[f"rv_{w}"] = (r ** 2).rolling(w).mean()
    pk = np.log(df["high"] / df["low"]) ** 2 / (4 * math.log(2))
    for w in windows:
        out[f"range_var_{w}"] = pk.rolling(w).mean()
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1, skipna=False)
    out[f"atr_{ATR_PERIOD}"] = tr.rolling(ATR_PERIOD).mean() / df["close"]
    sin, cos = _tod(pd.DatetimeIndex(out["known_at"]))
    out["tod_sin"], out["tod_cos"] = sin, cos
    return out


def forward_target(candles: Sequence[Candle], horizon: int) -> pd.DataFrame:
    """LABEL: mean r^2 over bars t+1..t+horizon, with the time it becomes knowable."""
    if horizon < 1:
        raise FeatureInputError("horizon must be >= 1")
    df, tf = _frame(candles)
    r2 = np.log(df["close"] / df["close"].shift(1)) ** 2
    fwd = r2[::-1].rolling(horizon).mean()[::-1].shift(-1)
    out = pd.DataFrame(index=df.index)
    out["target"] = fwd
    out["target_known_at"] = df.index + tf_delta(tf) * (horizon + 1)
    return out
