"""Gap policy for real FX data (Phase 8A, closes known issue L-2; decision L16).

Policy "trading-time windows, gap returns excluded":
  * A return that spans a missing-bar gap (weekend closure, holiday, outage) is NOT a one-bar
    return. It is excluded from every rolling window and from the target, and the bar that
    follows the gap is not a modelling row.
  * Windows and the horizon count VALID bars (trading time). "24 bars" means 24 traded hours,
    which may span a weekend in clock time. ``target_known_at`` is the close of the bar that
    ends the window, so it is honest about the clock time.
  * Rows therefore map 1:1 to valid bars, so an embargo of ``horizon`` rows covers the target
    window exactly (partition.py).
  * Gaps are checked first with ``sx_data.quality`` rules. An unexpected gap longer than the
    tolerance is refused (``GapPolicyError``): the data needs a human look, not a silent fix.
On gap-free candles the result equals ``make_dataset`` exactly (tested).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from sx_core.clock import tf_delta
from sx_core.contracts import Candle
from sx_core.storage import candles_to_frame
from sx_data.quality import DEFAULT_RULES, GapRules, QualityReport, check_quality
from sx_lab.features.volatility import ATR_PERIOD, _frame, _tod

__all__ = ["GapPolicyError", "gap_report", "make_gap_aware_dataset"]


class GapPolicyError(ValueError):
    """The candles have a gap or defect that the policy refuses to bridge."""


def gap_report(candles: Sequence[Candle], rules: GapRules = DEFAULT_RULES) -> QualityReport:
    return check_quality(candles_to_frame(candles), candles[0].tf, rules=rules)


def _roll(x: pd.Series, w: int) -> pd.Series:
    """Mean of the last ``w`` valid values; NaN rows stay NaN (they are dropped later)."""
    return x.dropna().rolling(w).mean().reindex(x.index)


def make_gap_aware_dataset(candles: Sequence[Candle], horizon: int, windows: Sequence[int],
                           rules: GapRules = DEFAULT_RULES) -> pd.DataFrame:
    if horizon not in windows:
        raise ValueError(f"horizon {horizon} must be one of the windows {tuple(windows)}")
    df, tf = _frame(candles)
    rep = gap_report(candles, rules)
    bad = [r for r in rep.reasons if "unexpected gap" in r or "duplicate" in r
           or "grid" in r or "order" in r]
    if bad:
        raise GapPolicyError("; ".join(bad))
    step = tf_delta(tf)
    gap_before = pd.Series(df.index.to_series().diff() > step, index=df.index)
    r = np.log(df["close"] / df["close"].shift(1)).where(~gap_before)
    out = pd.DataFrame(index=df.index)
    out["known_at"] = df.index + step
    out["ret"] = r
    for w in windows:
        out[f"rv_{w}"] = _roll(r ** 2, w)
    pk = (np.log(df["high"] / df["low"]) ** 2 / (4 * math.log(2))).where(r.notna())
    for w in windows:
        out[f"range_var_{w}"] = _roll(pk, w)
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1, skipna=False).where(r.notna())
    out[f"atr_{ATR_PERIOD}"] = _roll(tr, ATR_PERIOD) / df["close"]
    out["tod_sin"], out["tod_cos"] = _tod(pd.DatetimeIndex(out["known_at"]))
    # target: mean r^2 over the next `horizon` valid returns, on the compacted series
    v = (r ** 2).dropna()
    fwd = v[::-1].rolling(horizon).mean()[::-1].shift(-1)
    end_time = pd.Series(v.index, index=v.index).shift(-horizon) + step
    out["target"] = fwd.reindex(out.index)
    out["target_known_at"] = end_time.reindex(out.index)
    return out.dropna()

