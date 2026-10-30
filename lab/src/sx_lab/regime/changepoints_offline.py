"""Offline change-point labelling, PELT with an L2 cost (Phase 8A). RETROSPECTIVE ONLY.

PELT sees the whole series, so a change point reported at time t is known only after the fact.
Output is tagged ``retrospective`` and must never feed a model, a forecast, a setup or a paper
order. It is for describing history (for example, labelling regimes in a report).

Why in-house: ``ruptures`` 1.1.10 requires Python < 3.14 and the owner runs 3.14.3, so it cannot
be installed there (found when the owner ran ``pip install -e lab``). This is an exact dynamic
program (no pruning, O(n^2) vectorised; fine for a few thousand bars, a few seconds for ~30k).
It minimises  sum of segment squared deviations + penalty * number_of_segments  with every
segment at least ``min_size`` long. ``ruptures`` stays an optional cross-check: the tests
compare both when it is installed (Python < 3.14 only). Measured in the sandbox: on 120 random
cases ruptures matched in 117 and in the other 3 (penalty 5, many segments) this function had a
strictly lower objective, so ruptures' pruning is not exact with ``min_size``; brute force in
the tests is the oracle, not ruptures.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

STATUS = "retrospective"


@dataclass(frozen=True)
class ChangePoints:
    times: tuple[pd.Timestamp, ...]   # first row of each new segment
    penalty: float
    status: str = STATUS


def pelt_l2(x: np.ndarray, penalty: float, min_size: int) -> list[int]:
    """Segment end indices (exclusive), the last being ``len(x)``."""
    n = len(x)
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    best = np.full(n + 1, np.inf)
    best[0] = 0.0
    prev = np.zeros(n + 1, dtype=int)
    for t in range(min_size, n + 1):
        s = np.arange(0, t - min_size + 1)
        s = s[(s == 0) | (s >= min_size)]
        m = t - s
        cost = (c2[t] - c2[s]) - (c1[t] - c1[s]) ** 2 / m
        total = best[s] + cost + penalty
        k = int(np.argmin(total))
        best[t], prev[t] = total[k], int(s[k])
    ends, t = [], n
    while t > 0:
        ends.append(int(t))
        t = int(prev[t])
    return ends[::-1]


def offline_changepoints(series: pd.Series, *, penalty: float, min_size: int = 24,
                         ) -> ChangePoints:
    x = np.asarray(series, dtype="float64")
    if x.ndim != 1 or len(x) < 2 * min_size or not np.isfinite(x).all():
        raise ValueError("need a finite 1-D series of at least 2 * min_size points")
    if penalty <= 0:
        raise ValueError("penalty must be positive")
    ends = pelt_l2(x, penalty, min_size)
    return ChangePoints(tuple(series.index[e] for e in ends[:-1]), penalty)
