"""Candle quality checks and the ``feed_degraded`` flag.

Checks (all on a candle frame, one instrument and timeframe): duplicate times, out-of-order
times, bars not on the timeframe grid, crossed quotes (bid_close > ask_close), incomplete bars,
gaps, and (when ``now`` is given) a stale feed.

Gaps: a gap is the run of missing bars between two consecutive bars. A gap inside the weekly
closure window is *expected*; any other gap is *unexpected* and, if longer than
``max_gap_bars``, degrades the feed. Both the window and ``max_gap_bars`` are ASSUMPTIONS
(Exploratory, see ``GapRules``), not exchange calendars: market holidays show up as unexpected
gaps (except the Dec 25 and Jan 1 closures, see ``GapRules.holiday_closures``), and a
single missing quiet minute on M1 is normal and tolerated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from sx_core.clock import TF_SECONDS


@dataclass(frozen=True)
class GapRules:
    """Weekly closure window (UTC) and gap tolerance. Defaults are assumptions, not a calendar.

    Friday 20:00 UTC to Sunday 23:00 UTC covers the usual FX weekend closure across both US
    daylight-saving states, at the cost of tolerating a late Sunday open.
    """

    closure_start: tuple[int, int, int] = (4, 20, 0)   # (weekday Mon=0, hour, minute): Friday
    closure_end: tuple[int, int, int] = (6, 23, 0)     # Sunday
    max_gap_bars: int = 3
    stale_after_bars: int = 3
    # Christmas and New Year closures (UTC windows, wide enough for both US DST states).
    # Seen on real OANDA practice H1: last bar Dec 24 21:00, next Dec 25 22:00; same on Jan 1.
    # Other holidays (Good Friday and so on) are NOT listed: they stay unexpected gaps.
    holiday_closures: bool = True


@dataclass(frozen=True)
class Gap:
    after: datetime        # open time of the last bar before the gap
    before: datetime       # open time of the first bar after the gap
    missing_bars: int


@dataclass(frozen=True)
class QualityReport:
    n_bars: int
    duplicates: int
    out_of_order: int
    off_grid: int
    crossed_quotes: int
    incomplete: int
    expected_gaps: tuple[Gap, ...]
    unexpected_gaps: tuple[Gap, ...]
    stale: bool
    feed_degraded: bool
    reasons: tuple[str, ...] = field(default=())


_EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def _week_minute(t: pd.Timestamp) -> int:
    return int(t.weekday() * 1440 + t.hour * 60 + t.minute)


def _bounds(rules: GapRules) -> tuple[int, int]:
    """Closure window as minutes since Monday 00:00 UTC."""
    lo = rules.closure_start[0] * 1440 + rules.closure_start[1] * 60 + rules.closure_start[2]
    hi = rules.closure_end[0] * 1440 + rules.closure_end[1] * 60 + rules.closure_end[2]
    return lo, hi


def _in_closure(a: pd.Timestamp, b: pd.Timestamp, rules: GapRules) -> bool:
    """True if the missing span ``[a, b)`` lies inside one weekly closure window."""
    lo, hi = _bounds(rules)
    return lo <= _week_minute(a) and _week_minute(b) <= hi and b - a <= pd.Timedelta(
        minutes=hi - lo)


def _in_holiday(a: pd.Timestamp, b: pd.Timestamp, rules: GapRules) -> bool:
    """True if the missing span ``[a, b)`` lies inside a Dec 25 or Jan 1 closure window."""
    if not rules.holiday_closures:
        return False
    for y in (a.year - 1, a.year):
        windows = ((pd.Timestamp(y, 12, 24, 20, tz="UTC"), pd.Timestamp(y, 12, 26, tz="UTC")),
                   (pd.Timestamp(y, 12, 31, 20, tz="UTC"),
                    pd.Timestamp(y + 1, 1, 2, tz="UTC")))
        if any(lo <= a and b <= hi for lo, hi in windows):
            return True
    return False


DEFAULT_RULES = GapRules()


def check_quality(df: pd.DataFrame, tf: str, *, now: datetime | None = None,
                  rules: GapRules = DEFAULT_RULES) -> QualityReport:
    """Inspect ``df`` (columns per ``CANDLE_COLUMNS``). Never mutates it."""
    secs = TF_SECONDS[tf]
    step = pd.Timedelta(seconds=secs)
    n = len(df)
    if n == 0:
        stale = now is not None
        why = ("no bars",) + (("stale feed",) if stale else ())
        return QualityReport(0, 0, 0, 0, 0, 0, (), (), stale, True, why)

    t = df["time"].reset_index(drop=True)
    duplicates = int(t.duplicated().sum())
    out_of_order = int((t.diff().dropna() < pd.Timedelta(0)).sum())
    off_grid = int(((t - _EPOCH) % step != pd.Timedelta(0)).sum())
    crossed = int((df["bid_close"] > df["ask_close"]).sum())
    incomplete = int((~df["complete"]).sum())

    ordered = t.drop_duplicates().sort_values().reset_index(drop=True)
    expected: list[Gap] = []
    unexpected: list[Gap] = []
    for a, b in zip(ordered[:-1], ordered[1:], strict=True):
        missing = int((b - a) / step) - 1
        if missing <= 0:
            continue
        gap = Gap(a.to_pydatetime(), b.to_pydatetime(), missing)
        (expected if _in_closure(a + step, b, rules) or _in_holiday(a + step, b, rules)
         else unexpected).append(gap)

    stale = False
    if now is not None:
        last_close = ordered.iloc[-1] + step
        age = pd.Timestamp(now).tz_convert("UTC") - last_close
        lo, hi = _bounds(rules)
        in_closure = lo <= _week_minute(pd.Timestamp(now).tz_convert("UTC")) <= hi
        stale = age > step * rules.stale_after_bars and not in_closure

    reasons: list[str] = []
    if duplicates:
        reasons.append(f"{duplicates} duplicate bar time(s)")
    if out_of_order:
        reasons.append(f"{out_of_order} bar(s) out of time order")
    if off_grid:
        reasons.append(f"{off_grid} bar(s) not on the {tf} grid")
    if crossed:
        reasons.append(f"{crossed} bar(s) with bid above ask")
    if incomplete:
        reasons.append(f"{incomplete} incomplete bar(s)")
    long_gaps = [g for g in unexpected if g.missing_bars > rules.max_gap_bars]
    if long_gaps:
        reasons.append(f"{len(long_gaps)} unexpected gap(s) longer than {rules.max_gap_bars} bars")
    if stale:
        reasons.append("stale feed")
    return QualityReport(n, duplicates, out_of_order, off_grid, crossed, incomplete,
                         tuple(expected), tuple(unexpected), stale, bool(reasons), tuple(reasons))


__all__ = ["Gap", "GapRules", "QualityReport", "check_quality"]
