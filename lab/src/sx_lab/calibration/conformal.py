"""Split-conformal intervals for variance forecasts (Phase 8A, replaces decision L5).

Score: s = ln(y / f) for a positive forecast f and realized y (multiplicative error, so the
band scales with the forecast and is always positive). Calibrate on rows the model was NOT
fitted on and that are NOT used to report coverage. Band: [f*exp(q_lo), f*exp(q_hi)] where the
quantiles are the finite-sample split-conformal ones (rank ceil((n+1)(1-a/2)) from the top,
floor((n+1)(a/2)) from the bottom). A band that cannot be formed from n rows is refused.

HONEST CAVEAT (written down because it matters): the split-conformal guarantee,
P(y in band) >= 1 - alpha, needs calibration and test scores to be EXCHANGEABLE. Volatility
series are autocorrelated, regimes shift, and horizon-h targets overlap, so the guarantee does
NOT hold for them. Coverage here is a measured, approximate property: always report
``coverage_report`` on rows after the calibration block and treat a gap to nominal as a finding.
Tests show coverage holds on exchangeable data and degrades under a variance shift.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

Array = npt.ArrayLike


class ConformalError(ValueError):
    pass


def _positive_pair(f: Array, y: Array) -> tuple[np.ndarray, np.ndarray]:
    fa, ya = np.asarray(f, dtype="float64"), np.asarray(y, dtype="float64")
    if fa.shape != ya.shape or fa.ndim != 1 or fa.size == 0:
        raise ConformalError("need two equal-length non-empty 1-D arrays")
    if not (np.isfinite(fa).all() and np.isfinite(ya).all()) or (fa <= 0).any() or (ya <= 0).any():
        raise ConformalError("forecasts and realized values must be finite and positive")
    return fa, ya


class SplitConformal:
    def __init__(self, alpha: float = 0.2):
        if not 0 < alpha < 1:
            raise ConformalError("alpha must be in (0, 1)")
        self.alpha = alpha
        self.q_lo: float | None = None
        self.q_hi: float | None = None
        self.n_calibration = 0

    @property
    def nominal(self) -> float:
        return 1.0 - self.alpha

    def calibrate(self, forecast: Array, realized: Array) -> SplitConformal:
        f, y = _positive_pair(forecast, realized)
        s = np.sort(np.log(y / f))
        n = s.size
        k_lo = math.floor((n + 1) * self.alpha / 2)           # 1-based rank from the bottom
        k_hi = math.ceil((n + 1) * (1 - self.alpha / 2))      # 1-based rank
        if k_lo < 1 or k_hi > n:
            raise ConformalError(f"{n} calibration rows are too few for alpha={self.alpha}; "
                                 f"need at least {math.ceil(2 / self.alpha) - 1}")
        self.q_lo, self.q_hi, self.n_calibration = float(s[k_lo - 1]), float(s[k_hi - 1]), n
        return self

    def interval(self, forecast: Array) -> tuple[np.ndarray, np.ndarray]:
        if self.q_lo is None or self.q_hi is None:
            raise ConformalError("call calibrate() first")
        f = np.asarray(forecast, dtype="float64")
        if f.ndim != 1 or not np.isfinite(f).all() or (f <= 0).any():
            raise ConformalError("forecasts must be finite, positive and 1-D")
        return f * math.exp(self.q_lo), f * math.exp(self.q_hi)


@dataclass(frozen=True)
class CoverageReport:
    nominal: float
    empirical: float
    n: int
    worst_rolling: float | None     # lowest coverage over rolling windows, None if n < window
    window: int
    mean_width_ratio: float         # mean of (high - low) / forecast


def coverage_report(lower: Array, upper: Array, forecast: Array, realized: Array, *,
                    nominal: float, window: int = 50) -> CoverageReport:
    lo, y = _positive_pair(lower, realized)
    hi, f = _positive_pair(upper, forecast)
    if (lo > hi).any():
        raise ConformalError("lower bound above upper bound")
    inside = ((y >= lo) & (y <= hi)).astype("float64")
    worst = None
    if inside.size >= window:
        roll = np.convolve(inside, np.ones(window) / window, mode="valid")
        worst = float(roll.min())
    return CoverageReport(nominal, float(inside.mean()), int(inside.size), worst, window,
                          float(np.mean((hi - lo) / f)))
