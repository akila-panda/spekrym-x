"""Build the premarket analysis from closed bars only, as of a given time.

Everything returned has ``known_at <= as_of``. Only bars that had closed by ``as_of`` are read,
so the result for ``as_of = t`` equals the result on data truncated at ``t`` (tested).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sx_assistant.premarket.bias_checklist import ChecklistItem, build_checklist
from sx_assistant.premarket.data_source import MarketDataSource, SourceInfo
from sx_assistant.ta.normalize import analyze_causal, require_causal
from sx_assistant.ta.normalize import as_of as setups_as_of
from sx_core.contracts import Candle, Setup
from sx_core.storage import candles_to_frame, data_version

TF = "M15"
WINDOW_DAYS = 3  # calendar days of M15 history analysed; replay cost grows quadratically


@dataclass(frozen=True)
class PremarketAnalysis:
    instrument: str
    tf: str
    as_of: datetime
    source: SourceInfo
    candles: list[Candle]
    setups: list[Setup]
    checklist: list[ChecklistItem]
    data_version: str


def build_premarket(source: MarketDataSource, instrument: str, as_of: datetime,
                    window_days: int = WINDOW_DAYS) -> PremarketAnalysis:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")
    if as_of > source.last_close(instrument):
        raise ValueError(f"as_of {as_of.isoformat()} is after the newest closed bar")
    closed = source.candles(instrument, TF, as_of)
    floor = (as_of - timedelta(days=window_days)).replace(hour=0, minute=0, second=0,
                                                          microsecond=0)
    window = [c for c in closed if c.time >= floor]
    if len(window) < 8:
        raise ValueError("not enough closed bars to analyse")
    setups = require_causal(setups_as_of(analyze_causal(window), window, as_of))
    checklist = build_checklist(source.candles(instrument, "D", as_of),
                                source.candles(instrument, "H4", as_of))
    return PremarketAnalysis(instrument, TF, as_of, source.info, window, setups, checklist,
                             data_version(candles_to_frame(window)))
