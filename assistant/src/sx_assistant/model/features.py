"""Causal features for a decided ``Setup``. Everything uses bars and setups known at decision time.

Decision time = close of the first bar whose close is at or after ``known_at``. A feature row
for decision bar ``i`` reads only ``candles[: i + 1]`` and setups with ``known_at <= close(i)``.
Look-back is BOUNDED (``FEATURE_LOOKBACK`` bars) so the purge gap can be stated exactly.
Labels never appear here. Retrospective setups are refused (``require_causal``).
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Sequence

import numpy as np
import pandas as pd

from sx_assistant.model.labels_triple_barrier import BarrierConfig, atr_series
from sx_assistant.ta.normalize import require_causal
from sx_core.clock import DEFAULT_SESSIONS, session_at, tf_delta
from sx_core.contracts import Candle, Setup

FEATURE_LOOKBACK = 48  # bars; every window below is <= this
RECENT_BARS = 24
KINDS = ("swing", "bos", "choch", "fvg", "order_block", "liquidity_sweep", "session_level",
         "support_resistance", "candle_pattern")
SESSIONS = {"asia": 0, "london": 1, "ny": 2}
FEATURE_NAMES = ("kind_code", "direction", "atr_rel", "height_atr", "dist_mid_atr", "age_bars",
                 "hour_sin", "hour_cos", "dow", "session_code", "n_recent", "n_recent_same_dir",
                 "ret6_with_dir", "ret24_with_dir")
FEATURE_TEXT = {
    "kind_code": "setup type", "direction": "setup direction",
    "atr_rel": "volatility (ATR relative to price)", "height_atr": "setup height in ATR",
    "dist_mid_atr": "price distance from the setup middle (ATR, direction-signed)",
    "age_bars": "bars since the setup formed (capped)", "hour_sin": "time of day (sine)",
    "hour_cos": "time of day (cosine)", "dow": "day of week", "session_code": "trading session",
    "n_recent": "other setups in the last 24 bars",
    "n_recent_same_dir": "same-direction setups in the last 24 bars",
    "ret6_with_dir": "6-bar move in the setup direction (ATR)",
    "ret24_with_dir": "24-bar move in the setup direction (ATR)",
}


def _ret(c: np.ndarray, i: int, m: int, sign: int, a: float) -> float:
    return float(sign * (c[i] - c[i - m]) / a) if i >= m else float("nan")


def build_rows(setups: Sequence[Setup], candles: Sequence[Candle],
               cfg: BarrierConfig) -> pd.DataFrame:
    """One row per directional setup that has a decision bar in ``candles``. No labels."""
    sets = require_causal(list(setups))
    if not candles:
        return pd.DataFrame(columns=["setup_id", "kind", "decision_idx", "decision_time",
                                     *FEATURE_NAMES])
    delta = tf_delta(candles[0].tf)
    closes_t = [c.time + delta for c in candles]
    h, lo, c = (np.array([getattr(k, a) for k in candles], float)
                for a in ("high", "low", "close"))
    atr = atr_series(h, lo, c, cfg.atr_period)
    all_known = sorted(s.known_at for s in sets)
    same = {1: sorted(s.known_at for s in sets if s.direction == "bullish"),
            -1: sorted(s.known_at for s in sets if s.direction == "bearish")}
    span = delta * RECENT_BARS
    rows = []
    for s in sets:
        if s.direction == "neutral":
            continue
        i = bisect_left(closes_t, s.known_at)  # first bar whose close is >= known_at
        if i >= len(candles) or not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        t, sign, a = closes_t[i], (1 if s.direction == "bullish" else -1), atr[i]
        age = min(max((t - s.event_time) / delta, 0.0), FEATURE_LOOKBACK)
        lo_t = t - span
        n_all = bisect_right(all_known, t) - bisect_right(all_known, lo_t) - 1
        k = same[sign]
        n_same = bisect_right(k, t) - bisect_right(k, lo_t) - 1
        g = s.geometry
        sess = session_at(t, DEFAULT_SESSIONS)
        rows.append({
            "setup_id": s.id, "kind": s.kind, "decision_idx": i, "decision_time": t,
            "kind_code": KINDS.index(s.kind), "direction": sign, "atr_rel": a / c[i],
            "height_atr": (g.price_high - g.price_low) / a,
            "dist_mid_atr": sign * (c[i] - (g.price_low + g.price_high) / 2) / a,
            "age_bars": float(age), "hour_sin": np.sin(2 * np.pi * t.hour / 24),
            "hour_cos": np.cos(2 * np.pi * t.hour / 24), "dow": t.weekday(),
            "session_code": SESSIONS.get(sess, 3), "n_recent": max(n_all, 0),
            "n_recent_same_dir": max(n_same, 0), "ret6_with_dir": _ret(c, i, 6, sign, a),
            "ret24_with_dir": _ret(c, i, 24, sign, a)})
    df = pd.DataFrame(rows, columns=["setup_id", "kind", "decision_idx", "decision_time",
                                     *FEATURE_NAMES])
    return df.sort_values(["decision_idx", "setup_id"]).reset_index(drop=True)
