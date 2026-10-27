"""TA-Lib candlestick patterns, counted only when the pattern bar is near a known level or zone.

A pattern's value at bar ``i`` is computed from bars ``<= i`` by TA-Lib, so it is known when
bar ``i`` closes. It is emitted only if (a) ATR(period) exists, and (b) some supplied level
that was already known at that close lies within ``proximity_atr`` x ATR of the bar's range.
Retrospective levels are refused: they would leak the future into a causal setup.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import talib

from sx_assistant.ta.common import check_series, fmt_price, lib_source, to_frame
from sx_core.clock import available_at
from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry

ADAPTER = "sx_assistant.ta.candles_talib"
PATTERNS: dict[str, tuple[str, str]] = {  # name -> (TA-Lib function, display text)
    "engulfing": ("CDLENGULFING", "engulfing candle"),
    "hammer": ("CDLHAMMER", "hammer"),
    "shooting_star": ("CDLSHOOTINGSTAR", "shooting star"),
    "morning_star": ("CDLMORNINGSTAR", "morning star"),
    "evening_star": ("CDLEVENINGSTAR", "evening star"),
}
NEAR_KINDS = ("session_level", "fvg", "order_block", "swing")
DEFAULT_ATR_PERIOD = 14          # proposed defaults, not tuned (I15)
DEFAULT_PROXIMITY_ATR = 0.5      # a level counts as near within this many ATRs of the bar


def _gap(lo: float, hi: float, level: Setup) -> float:
    return max(0.0, level.geometry.price_low - hi, lo - level.geometry.price_high)


def candle_pattern_setups(candles: Sequence[Candle], levels: Sequence[Setup], *,
                          atr_period: int = DEFAULT_ATR_PERIOD,
                          proximity_atr: float = DEFAULT_PROXIMITY_ATR) -> list[Setup]:
    instrument, tf = check_series(candles)
    if any(lv.status != "causal" for lv in levels):
        raise ValueError("candle patterns may only be placed near causal levels")
    near = [lv for lv in levels if lv.kind in NEAR_KINDS and lv.instrument == instrument
            and lv.tf == tf]
    df = to_frame(candles)
    o, h, lo, c = (df[x].to_numpy(dtype="float64") for x in ("open", "high", "low", "close"))
    atr = talib.ATR(h, lo, c, timeperiod=atr_period)
    src = lib_source("TA-Lib", ADAPTER)
    out: list[Setup] = []
    for name, (fn, text) in PATTERNS.items():
        res = getattr(talib, fn)(o, h, lo, c)
        for i in np.flatnonzero(res):
            if np.isnan(atr[i]):
                continue
            bar = candles[i]
            known = available_at(bar.time, tf)
            cands = [(_gap(bar.low, bar.high, lv), lv.id, lv) for lv in near
                     if lv.known_at <= known and lv.event_time <= bar.time]
            cands = [x for x in cands if x[0] <= proximity_atr * atr[i]]
            if not cands:
                continue
            _, _, lv = min(cands, key=lambda x: (x[0], x[1]))
            bull = res[i] > 0
            direction = "bullish" if bull else "bearish"
            out.append(Setup(
                id=setup_id("candle_pattern", instrument, tf, direction, bar.time, name),
                kind="candle_pattern", instrument=instrument, tf=tf, direction=direction,
                geometry=Geometry(price_low=bar.low, price_high=bar.high, t_start=bar.time,
                                  t_end=known),
                event_time=bar.time, known_at=known, lifecycle="fresh", source=src,
                plain_text=f"{direction.capitalize()} {text} near "
                           f"{fmt_price(lv.geometry.price_low, instrument)} "
                           f"({lv.kind.replace('_', ' ')}); a candle shape, not a signal",
                invalidation=f"A close {'below' if bull else 'above'} the pattern bar's "
                             f"{'low' if bull else 'high'} "
                             f"{fmt_price(bar.low if bull else bar.high, instrument)} "
                             "cancels it.", status="causal"))
    return sorted(out, key=lambda s: (s.known_at, s.event_time, s.id))
