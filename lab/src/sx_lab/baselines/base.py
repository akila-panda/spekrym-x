from __future__ import annotations

from typing import Protocol, Self

import pandas as pd


class Baseline(Protocol):
    """A variance forecaster. ``fit`` sees the training frame only; ``predict`` reads the
    causal feature columns of any frame and never the ``target`` column."""

    name: str

    def fit(self, train: pd.DataFrame) -> Self: ...

    def predict(self, frame: pd.DataFrame) -> pd.Series: ...
