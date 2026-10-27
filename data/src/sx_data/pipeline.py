"""Fetch M1 from the OANDA practice API into the cache, then build the higher timeframes.

M1 is the single source of truth. M15, H1, H4 and D are always rebuilt from cached M1 with
``resample`` (UTC alignment, closed bars only), never fetched, so every timeframe agrees.
"""

from __future__ import annotations

from datetime import datetime

from sx_core.contracts._base import Tf
from sx_core.storage import candles_to_frame
from sx_data.cache import CandleCache
from sx_data.errors import DataError
from sx_data.oanda_rest import OandaClient
from sx_data.resample import resample_frame

HIGHER: tuple[Tf, ...] = ("M15", "H1", "H4", "D")


def sync_m1(client: OandaClient, cache: CandleCache, instrument: str, start: datetime,
            end: datetime) -> str | None:
    """Fetch closed M1 bars in ``[start, end)`` and merge them into the cache."""
    candles = client.fetch_candles(instrument, "M1", start, end)
    return cache.store(candles_to_frame(candles)) if candles else None


def rebuild_higher(cache: CandleCache, instrument: str, tfs: tuple[Tf, ...] = HIGHER
                   ) -> dict[str, str]:
    """Rebuild ``tfs`` from cached M1. Returns ``{tf: data_version}``."""
    m1 = cache.load(instrument, "M1")
    if m1 is None:
        raise DataError(f"no cached M1 for {instrument}; run sync first")
    out: dict[str, str] = {}
    for tf in tfs:
        frame = resample_frame(m1, tf)
        if not frame.empty:
            out[tf] = cache.store(frame)
    return out
