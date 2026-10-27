"""Forecast metrics for variance forecasts (Phase 7A). Lower QLIKE and RMSE are better.

No significance testing here; the model confidence set arrives with Phase 8. Bad input raises:
nothing is clipped or dropped silently.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

Array = npt.ArrayLike


class MetricInputError(ValueError):
    pass


def _pair(forecast: Array, realized: Array) -> tuple[np.ndarray, np.ndarray]:
    f = np.asarray(forecast, dtype="float64")
    y = np.asarray(realized, dtype="float64")
    if f.shape != y.shape or f.ndim != 1:
        raise MetricInputError(f"need two 1-D arrays of equal length, got {f.shape} and {y.shape}")
    if f.size == 0:
        raise MetricInputError("empty input")
    if not (np.isfinite(f).all() and np.isfinite(y).all()):
        raise MetricInputError("NaN or infinite value in input")
    return f, y


def qlike_losses(forecast: Array, realized: Array) -> np.ndarray:
    """Per-observation QLIKE: y/f - ln(y/f) - 1 (zero only when forecast equals realized)."""
    f, y = _pair(forecast, realized)
    if (f <= 0).any() or (y <= 0).any():
        raise MetricInputError("QLIKE needs strictly positive forecasts and realized values")
    ratio = y / f
    return ratio - np.log(ratio) - 1.0


def qlike(forecast: Array, realized: Array) -> float:
    return float(qlike_losses(forecast, realized).mean())


def rmse(forecast: Array, realized: Array) -> float:
    f, y = _pair(forecast, realized)
    return float(np.sqrt(np.mean((f - y) ** 2)))


def interval_coverage(lower: Array, upper: Array, realized: Array) -> float:
    """Share of realized values inside [lower, upper]. Reported next to the nominal level."""
    lo, y = _pair(lower, realized)
    hi, _ = _pair(upper, realized)
    if (lo > hi).any():
        raise MetricInputError("lower bound above upper bound")
    return float(np.mean((y >= lo) & (y <= hi)))


def score(forecast: Array, realized: Array) -> dict[str, float | int]:
    f, _ = _pair(forecast, realized)
    return {"qlike": qlike(forecast, realized), "rmse": rmse(forecast, realized), "n": int(f.size)}
