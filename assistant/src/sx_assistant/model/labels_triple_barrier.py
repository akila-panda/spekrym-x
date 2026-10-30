"""Triple-barrier labels. TRAINING TARGETS ONLY: they read FUTURE bars by design.

For a setup decided at bar ``i`` (entry = close of bar ``i``), the barriers are ATR-scaled:
target at ``target_atr`` x ATR in the setup's direction, stop at ``stop_atr`` x ATR against it,
time barrier after ``horizon`` bars. Label 1 = target touched first; 0 = stop first or time
ran out. If a single bar touches both barriers the STOP wins (conservative). Rows without a full
horizon of future bars get no label (they are dropped, never labelled 0).

Mid prices, no costs: a diagnostic target, not a P&L claim (principle 9).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BarrierConfig:
    horizon: int = 24
    atr_period: int = 14
    target_atr: float = 1.5
    stop_atr: float = 1.0

    def __post_init__(self) -> None:
        if self.horizon < 1 or self.atr_period < 2 or self.target_atr <= 0 or self.stop_atr <= 0:
            raise ValueError("invalid barrier config")

    def as_dict(self) -> dict:
        return asdict(self)


def atr_series(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """Mean true range of the last ``period`` bars ending at each bar (NaN until available)."""
    n = len(close)
    tr = np.full(n, np.nan)
    if n > 1:
        pc = close[:-1]
        tr[1:] = np.maximum(high[1:] - low[1:],
                            np.maximum(np.abs(high[1:] - pc), np.abs(low[1:] - pc)))
    out = np.full(n, np.nan)
    for i in range(period, n):
        out[i] = tr[i - period + 1:i + 1].mean()
    return out


def label_one(high: np.ndarray, low: np.ndarray, close: np.ndarray, atr: np.ndarray,
              i: int, sign: int, cfg: BarrierConfig) -> tuple[int, int, str, float] | None:
    """``(label, end_index, outcome, forward_return_in_atr)`` or None if not labellable."""
    n = len(close)
    a = atr[i]
    if i + cfg.horizon > n - 1 or not np.isfinite(a) or a <= 0:
        return None
    entry = close[i]
    up, dn = entry + sign * cfg.target_atr * a, entry - sign * cfg.stop_atr * a
    for j in range(i + 1, i + cfg.horizon + 1):
        hit_t = high[j] >= up if sign > 0 else low[j] <= up
        hit_s = low[j] <= dn if sign > 0 else high[j] >= dn
        if hit_s:  # stop first, also when both are touched in the same bar
            return 0, j, "stop", sign * (close[j] - entry) / a
        if hit_t:
            return 1, j, "target", sign * (close[j] - entry) / a
    end = i + cfg.horizon
    return 0, end, "time", sign * (close[end] - entry) / a


def label_rows(rows: pd.DataFrame, candles: pd.DataFrame, cfg: BarrierConfig) -> pd.DataFrame:
    """Labels for feature rows (needs ``decision_idx`` and ``direction``). Unlabellable rows drop.

    Returns a frame with ``label``, ``label_end_idx``, ``outcome`` and ``fwd_ret_atr`` (the last
    is for the leak control ONLY and must never be a feature).
    """
    h, lo, c = (candles[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = atr_series(h, lo, c, cfg.atr_period)
    out = []
    for idx, i, d in zip(rows.index, rows["decision_idx"], rows["direction"], strict=True):
        r = label_one(h, lo, c, atr, int(i), int(d), cfg)
        if r is not None:
            out.append((idx, *r))
    return pd.DataFrame(out, columns=["row", "label", "label_end_idx", "outcome",
                                      "fwd_ret_atr"]).set_index("row")
