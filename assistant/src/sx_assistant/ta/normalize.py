"""Everything becomes a ``Setup``: orchestration, lifecycle as of a time, causal guards.

``lifecycle_at`` and ``as_of`` evaluate lifecycle from closed bars only, so a chart replayed at
``t`` never shows a state that needed later bars. Producers keep the lifecycle they were born
with (``fresh``); they never mutate, which is what keeps their output prefix-stable.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sx_assistant.ta.candles_talib import candle_pattern_setups
from sx_assistant.ta.sessions import session_setups
from sx_assistant.ta.smc_adapter import smc_setups
from sx_core.clock import bar_close, is_known
from sx_core.contracts import Candle, Setup
from sx_core.contracts.setup import Lifecycle


def analyze_causal(candles: Sequence[Candle], *, swing_length: int = 3) -> list[Setup]:
    """Sessions + SMC + candle patterns near known levels. Every output is ``causal``."""
    base = session_setups(candles) + smc_setups(candles, swing_length=swing_length)
    allset = base + candle_pattern_setups(candles, base)
    ids = [s.id for s in allset]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate setup ids across adapters")
    return sorted(allset, key=lambda s: (s.known_at, s.event_time, s.id))


def require_causal(setups: Sequence[Setup]) -> list[Setup]:
    """Gate for models and paper trading: refuses retrospective output."""
    bad = [s.id for s in setups if s.status != "causal"]
    if bad:
        raise ValueError(f"{len(bad)} non-causal setup(s) must not feed models or paper: {bad[:3]}")
    return list(setups)


def lifecycle_at(setup: Setup, candles: Sequence[Candle], t: datetime) -> Lifecycle:
    """Lifecycle of ``setup`` using only bars that opened at/after ``known_at`` and closed by ``t``.

    Zones (FVG, order block): ``tested`` once a bar's range enters them, ``mitigated`` once a
    bar closes beyond the far edge. Swings and session levels (high = bearish, low = bullish
    orientation): ``broken`` once a bar closes beyond them. Other kinds do not evolve.
    """
    k, g = setup.kind, setup.geometry
    if k not in ("fvg", "order_block", "swing", "session_level"):
        return setup.lifecycle
    bull = setup.direction == "bullish"
    state: Lifecycle = setup.lifecycle
    for c in candles:
        if c.time < setup.known_at or bar_close(c.time, c.tf) > t:
            continue
        if k in ("fvg", "order_block"):
            if (c.close < g.price_low) if bull else (c.close > g.price_high):
                return "mitigated"
            if c.low <= g.price_high and c.high >= g.price_low:
                state = "tested"
        elif (c.close < g.price_low) if bull else (c.close > g.price_high):
            return "broken"
    return state


def as_of(setups: Sequence[Setup], candles: Sequence[Candle], t: datetime) -> list[Setup]:
    """Setups known at ``t`` with lifecycle evaluated at ``t``."""
    return [s.model_copy(update={"lifecycle": lifecycle_at(s, candles, t)})
            for s in setups if is_known(s.known_at, t)]
