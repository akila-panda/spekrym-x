"""HAR-style regression (Phase 7B): OLS of the next-window variance on trailing realized
variances (default rv_6, rv_24, rv_120). Fitted on the training frame only.

Level regressions can predict a non-positive variance, which QLIKE refuses. Predictions are
floored at the smallest training target and the number floored is exposed as ``n_floored``
(last ``predict`` call) so it is never hidden.
"""

from __future__ import annotations

from typing import Self

import numpy as np
import pandas as pd

from sx_lab.baselines.naive import NotFittedError

DEFAULT_COLUMNS = ("rv_6", "rv_24", "rv_120")


class HAR:
    name = "har"

    def __init__(self, columns: tuple[str, ...] = DEFAULT_COLUMNS):
        self.columns = tuple(columns)
        self.coef: np.ndarray | None = None
        self.floor: float | None = None
        self.n_floored = 0

    def _x(self, frame: pd.DataFrame) -> np.ndarray:
        missing = [c for c in self.columns if c not in frame.columns]
        if missing:
            raise KeyError(f"frame has no column(s) {missing}")
        return np.column_stack([np.ones(len(frame)), frame[list(self.columns)].to_numpy()])

    def fit(self, train: pd.DataFrame) -> Self:
        y = train["target"].to_numpy(dtype="float64")
        self.coef, *_ = np.linalg.lstsq(self._x(train), y, rcond=None)
        self.floor = float(y.min())
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        if self.coef is None or self.floor is None:
            raise NotFittedError("call fit() first")
        raw = self._x(frame) @ self.coef
        self.n_floored = int((raw < self.floor).sum())
        return pd.Series(np.maximum(raw, self.floor), index=frame.index, name=self.name)

    def params(self) -> dict[str, object]:
        if self.coef is None:
            raise NotFittedError("call fit() first")
        return {"columns": list(self.columns), "coef": [round(float(c), 12) for c in self.coef]}
