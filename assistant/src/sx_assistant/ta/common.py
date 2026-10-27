"""Shared helpers for the TA adapters: input checks, frames, price text, sources."""

from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import version

import pandas as pd

from sx_core.contracts import Candle
from sx_core.contracts.setup import Source

IN_HOUSE = "sx-internal"


def check_series(candles: Sequence[Candle]) -> tuple[str, str]:
    """Return ``(instrument, tf)``; reject anything that is not one clean, closed series."""
    if not candles:
        raise ValueError("candles must not be empty")
    instrument, tf = candles[0].instrument, candles[0].tf
    prev = None
    for c in candles:
        if c.instrument != instrument or c.tf != tf:
            raise ValueError("candles must be a single instrument and timeframe")
        if not c.complete:
            raise ValueError("only complete (closed) candles may be analysed")
        if prev is not None and c.time <= prev:
            raise ValueError("candles must be strictly increasing in time")
        prev = c.time
    return instrument, tf


def to_frame(candles: Sequence[Candle]) -> pd.DataFrame:
    """OHLCV frame with a 0..n-1 integer index (what the libraries expect)."""
    return pd.DataFrame({
        "open": [c.open for c in candles], "high": [c.high for c in candles],
        "low": [c.low for c in candles], "close": [c.close for c in candles],
        "volume": [c.volume for c in candles],
    }, dtype="float64")


def fmt_price(x: float, instrument: str) -> str:
    return f"{x:.3f}" if instrument.endswith("JPY") else f"{x:.5f}"


def lib_source(dist: str, adapter: str) -> Source:
    """``Source`` for an installed distribution (version read from its metadata)."""
    return Source(library=dist, version=version(dist), adapter=adapter)


def in_house_source(adapter: str) -> Source:
    from sx_assistant import __version__

    return Source(library=IN_HOUSE, version=__version__, adapter=adapter)
