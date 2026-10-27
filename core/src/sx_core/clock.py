"""Bar timing, ``known_at`` / ``available_at`` helpers and session boundaries (all UTC).

Scope: this is a bar and session clock. Sessions come in two forms: the fixed-UTC
``SessionConfig`` (kept for compatibility) and the DST-aware ``LocalSessionConfig`` (decision P9),
whose windows follow each market's local wall clock and are converted to UTC per date
(``sx_core/local_sessions.py``, re-exported here). It does not know market holidays or the weekend
close; gaps are detected from data in ``sx_data/quality.py``.

The ``D`` timeframe is a 24h UTC day starting at 00:00 UTC (decision X10). Broker daily bars
that align to a New York close are not used; ``sx_data.resample`` builds D from M1 instead.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

from sx_core.local_sessions import (
    DEFAULT_LOCAL_SESSIONS,
    DISPLAY_TZ,
    LocalSession,
    LocalSessionConfig,
    to_display_time,
)

TF_SECONDS: dict[str, int] = {
    "M1": 60, "M5": 300, "M15": 900, "M30": 1800, "H1": 3600, "H4": 14400, "D": 86400,
}


def _require_utc(t: datetime, name: str = "time") -> datetime:
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return t.astimezone(UTC)


def tf_delta(tf: str) -> timedelta:
    try:
        return timedelta(seconds=TF_SECONDS[tf])
    except KeyError:
        raise ValueError(f"unknown timeframe {tf!r}") from None


def bar_close(bar_open: datetime, tf: str) -> datetime:
    """The instant a bar opening at ``bar_open`` is complete."""
    return _require_utc(bar_open, "bar_open") + tf_delta(tf)


def available_at(bar_open: datetime, tf: str, latency: timedelta = timedelta(0)) -> datetime:
    """When a live system can first use the bar: its close plus any feed latency."""
    return bar_close(bar_open, tf) + latency


def is_closed(bar_open: datetime, tf: str, now: datetime) -> bool:
    """True when ``now`` is at or after the bar's close. Only closed bars enter analysis."""
    return _require_utc(now, "now") >= bar_close(bar_open, tf)


def known_at_after_bars(bar_open: datetime, tf: str, confirm_bars: int,
                        latency: timedelta = timedelta(0)) -> datetime:
    """``known_at`` for a signal anchored on a bar that needs ``confirm_bars`` more bars.

    A swing high needing 2 lower highs to its right is known when the 2nd of those bars
    closes: ``known_at_after_bars(swing_bar_open, tf, 2)``.
    """
    if confirm_bars < 0:
        raise ValueError("confirm_bars must be >= 0")
    return available_at(bar_open + confirm_bars * tf_delta(tf), tf, latency)


class _HasKnownAt(Protocol):
    known_at: datetime


def is_known(known_at: datetime, t: datetime) -> bool:
    """Principle 1: an object may be shown or used at ``t`` only if ``known_at <= t``."""
    return _require_utc(known_at, "known_at") <= _require_utc(t, "t")


def filter_known[T: _HasKnownAt](objects: Iterable[T], t: datetime) -> list[T]:
    return [o for o in objects if is_known(o.known_at, t)]


@dataclass(frozen=True)
class SessionConfig:
    """Named, non-overlapping sessions as minutes since 00:00 UTC (end exclusive, max 1440)."""

    sessions: tuple[tuple[str, int, int], ...] = (
        ("asia", 0, 7 * 60), ("london", 7 * 60, 12 * 60), ("ny", 12 * 60, 17 * 60),
    )

    def __post_init__(self) -> None:
        names = [n for n, _, _ in self.sessions]
        if len(set(names)) != len(names):
            raise ValueError("duplicate session names")
        spans = sorted((s, e, n) for n, s, e in self.sessions)
        for s, e, n in spans:
            if not 0 <= s < e <= 1440:
                raise ValueError(f"session {n!r}: need 0 <= start < end <= 1440")
        for (_, e1, n1), (s2, _, n2) in zip(spans, spans[1:], strict=False):
            if s2 < e1:
                raise ValueError(f"sessions {n1!r} and {n2!r} overlap")

    @classmethod
    def from_hours(cls, hours: dict[str, tuple[float, float]]) -> SessionConfig:
        return cls(tuple((n, round(s * 60), round(e * 60)) for n, (s, e) in hours.items()))

    def names(self) -> list[str]:
        return [n for n, _, _ in self.sessions]


DEFAULT_SESSIONS = SessionConfig()


def utc_day_start(t: datetime) -> datetime:
    t = _require_utc(t)
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def session_bounds(day: date, name: str, cfg: SessionConfig = DEFAULT_SESSIONS
                   ) -> tuple[datetime, datetime]:
    """UTC ``[start, end)`` of a named session on ``day``."""
    for n, s, e in cfg.sessions:
        if n == name:
            base = datetime(day.year, day.month, day.day, tzinfo=UTC)
            return base + timedelta(minutes=s), base + timedelta(minutes=e)
    raise KeyError(f"unknown session {name!r}")


def session_at(t: datetime, cfg: SessionConfig = DEFAULT_SESSIONS) -> str | None:
    """Name of the session containing ``t`` (start inclusive, end exclusive), else None."""
    t = _require_utc(t)
    minute = t.hour * 60 + t.minute
    for n, s, e in cfg.sessions:
        if s <= minute < e:
            return n
    return None


def previous_day(t: datetime) -> date:
    return (utc_day_start(t) - timedelta(days=1)).date()


__all__ = [
    "DEFAULT_LOCAL_SESSIONS", "DEFAULT_SESSIONS", "DISPLAY_TZ", "LocalSession",
    "LocalSessionConfig", "SessionConfig", "TF_SECONDS", "available_at",
    "bar_close", "filter_known", "is_closed", "is_known", "known_at_after_bars",
    "previous_day", "session_at", "session_bounds", "tf_delta", "to_display_time",
    "utc_day_start",
]
