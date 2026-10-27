"""Join features and target into one modelling frame with warm-up and tail rows removed."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from sx_core.contracts import Candle
from sx_lab.features.volatility import DEFAULT_WINDOWS, build_features, forward_target


def make_dataset(candles: Sequence[Candle], horizon: int,
                 windows: Sequence[int] = DEFAULT_WINDOWS) -> pd.DataFrame:
    """Features at origin ``t`` (bar close) plus the label for the next ``horizon`` bars.

    Rows with an unfilled lookback (start) or an unfinished target window (end) are dropped, so
    the frame is contiguous when the candles have no gaps. Gaps (for example weekends in real
    FX data) are NOT handled here; see docs/PHASE_7A_NOTES.md.
    """
    if horizon not in windows:
        raise ValueError(f"horizon {horizon} must be one of the windows {tuple(windows)} so "
                         "the persistence baseline has its column")
    feats = build_features(candles, windows)
    target = forward_target(candles, horizon)
    return feats.join(target).dropna()
