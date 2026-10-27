"""Session ranges and previous-day levels as ``Setup`` objects (decision P9, X10).

Sessions come from ``sx_core.clock.LocalSessionConfig`` (DST-aware). A session's high and low
are emitted only once the whole window has closed and **every** bar in it is present, so they
are final and ``known_at`` is the window end. Incomplete or gappy sessions emit nothing.

Previous-day levels (decision P10 / X14) are per **trading day** of the instrument's calendar
(``sx_core.trading_calendar``): a UTC day (X10) cut at the weekly close on Fridays. A day emits
levels only when every bar slot of its trading window is present, and ``known_at`` is the end
of that window (Friday: the weekly close, not midnight). ``previous_day_levels`` picks the
levels that apply on a date: the nearest earlier complete trading day, within a lookback limit.

Orientation (I11): a high is ``bearish`` (a level overhead), a low is ``bullish`` (underfoot).
That describes where the reference sits, not a forecast.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sx_assistant.ta.common import check_series, fmt_price, in_house_source
from sx_core.clock import DEFAULT_LOCAL_SESSIONS, LocalSessionConfig, tf_delta
from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry
from sx_core.trading_calendar import (
    DEFAULT_MAX_LOOKBACK,
    TradingCalendar,
    calendar_for,
    reference_day,
)

ALLOWED_TF = {"M1", "M5", "M15", "M30", "H1"}
NAMES = {"asia": "Asia", "london": "London", "ny": "New York"}
ADAPTER = "sx_assistant.ta.sessions"


def _full_window(by_time: dict[datetime, Candle], start: datetime, end: datetime,
                 delta: timedelta) -> list[Candle] | None:
    if (end - start) % delta:
        raise ValueError(f"timeframe step {delta} does not divide the window {start}..{end}")
    bars = []
    t = start
    while t < end:
        c = by_time.get(t)
        if c is None:
            return None
        bars.append(c)
        t += delta
    return bars


def _extremes(bars: list[Candle]) -> tuple[Candle, Candle]:
    hi = bars[0]
    lo = bars[0]
    for c in bars[1:]:
        if c.high > hi.high:
            hi = c
        if c.low < lo.low:
            lo = c
    return hi, lo


def _pair(bars: list[Candle], label: str, tag: str, when: str, start: datetime,
          end: datetime | None, known_at: datetime) -> list[Setup]:
    hi, lo = _extremes(bars)
    out = []
    for side, bar, level, direction in (("high", hi, hi.high, "bearish"),
                                        ("low", lo, lo.low, "bullish")):
        beyond = "above" if side == "high" else "below"
        out.append(Setup(
            id=setup_id("session_level", bar.instrument, bar.tf, direction, bar.time,
                        f"{tag}_{side}:{when}"),
            kind="session_level", instrument=bar.instrument, tf=bar.tf, direction=direction,
            geometry=Geometry(price_low=level, price_high=level, t_start=start, t_end=end),
            event_time=bar.time, known_at=known_at, lifecycle="fresh",
            source=in_house_source(ADAPTER),
            plain_text=f"{label} {side} {fmt_price(level, bar.instrument)} ({when})",
            invalidation=f"A close {beyond} {fmt_price(level, bar.instrument)} breaks the level; "
                         "a wick through that closes back inside is a sweep, not a break.",
            status="causal"))
    return out


def _day_levels(candles: Sequence[Candle], calendar: TradingCalendar,
                delta: timedelta) -> dict[date, list[Setup]]:
    """Previous-day high/low ``Setup`` pair for every complete trading day in the series."""
    by_time = {c.time: c for c in candles}
    first, last = candles[0].time, candles[-1].time + delta
    out: dict[date, list[Setup]] = {}
    day = first.date()
    while day <= last.date():
        win = calendar.trading_window(day)
        if win is not None and win[1] > first and win[0] < last:
            bars = _full_window(by_time, win[0], win[1], delta)
            if bars:
                out[day] = _pair(bars, "Previous day", "pd", f"trading day {day.isoformat()}",
                                 win[0], None, win[1])
        day += timedelta(days=1)
    return out


def session_setups(candles: Sequence[Candle], cfg: LocalSessionConfig = DEFAULT_LOCAL_SESSIONS,
                   calendar: TradingCalendar | None = None) -> list[Setup]:
    """Session highs/lows and previous-day high/low from complete windows only."""
    instrument, tf = check_series(candles)
    if tf not in ALLOWED_TF:
        raise ValueError(f"sessions need an intraday timeframe that divides them, not {tf}")
    cal = calendar or calendar_for(instrument)
    delta = tf_delta(tf)
    by_time = {c.time: c for c in candles}
    first, last = candles[0].time, candles[-1].time + delta
    d0, d1 = first.date() - timedelta(days=1), last.date() + timedelta(days=1)
    out: list[Setup] = []
    day: date = d0
    while day <= d1:
        for name, (start, end) in cfg.windows_for_day(day).items():
            if end <= first or start >= last:
                continue
            bars = _full_window(by_time, start, end, delta)
            if bars:
                out += _pair(bars, NAMES.get(name, name.title()), name,
                             f"{day.isoformat()} {start:%H:%M}-{end:%H:%M} UTC", start, end, end)
        day += timedelta(days=1)
    for levels in _day_levels(candles, cal, delta).values():
        out += levels
    return sorted(out, key=lambda s: (s.known_at, s.event_time, s.id))


def previous_day_levels(candles: Sequence[Candle], on: date,
                        calendar: TradingCalendar | None = None,
                        max_lookback: int = DEFAULT_MAX_LOOKBACK) -> list[Setup]:
    """The previous-day high and low that apply on UTC date ``on`` (decision P10 / X14).

    Monday gets Friday's; Tuesday to Friday get the day before; weekends and holidays get the
    latest completed trading day. A day with any missing bar is skipped and the search goes
    further back, at most ``max_lookback`` trading days; then the result is empty. Only days
    that ended before ``on`` start are used, so the answer is causal at 00:00 UTC of ``on``.
    """
    instrument, tf = check_series(candles)
    if tf not in ALLOWED_TF:
        raise ValueError(f"sessions need an intraday timeframe that divides them, not {tf}")
    cal = calendar or calendar_for(instrument)
    levels = _day_levels(candles, cal, tf_delta(tf))
    ref = reference_day(on, levels.keys(), cal, max_lookback)
    return [] if ref is None else levels[ref]
