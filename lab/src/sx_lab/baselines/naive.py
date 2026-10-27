"""Naive baselines (Phase 7A): persistence and historical mean. HAR and GARCH come in 7B."""

from __future__ import annotations

from typing import Self

import pandas as pd


class NotFittedError(RuntimeError):
    pass


class Persistence:
    """Forecast = realized variance over the last ``horizon`` bars (column ``rv_<horizon>``)."""

    def __init__(self, horizon: int):
        self.horizon = horizon
        self.name = f"persistence_{horizon}"

    def fit(self, train: pd.DataFrame) -> Self:
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        col = f"rv_{self.horizon}"
        if col not in frame.columns:
            raise KeyError(f"frame has no column {col!r}")
        return frame[col].rename(self.name)


class HistoricalMean:
    """Constant forecast = mean of the training target. Fitted on the training frame only."""

    name = "historical_mean"

    def __init__(self) -> None:
        self._mean: float | None = None

    def fit(self, train: pd.DataFrame) -> Self:
        self._mean = float(train["target"].mean())
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        if self._mean is None:
            raise NotFittedError("call fit() first")
        return pd.Series(self._mean, index=frame.index, name=self.name)
