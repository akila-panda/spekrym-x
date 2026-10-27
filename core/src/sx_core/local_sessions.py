"""DST-aware sessions (decision P9).

Each session is a window on its own market's local wall clock (an IANA time zone). A window
for a given local calendar date is converted to UTC for that date, so London and New York
shift on their own, different clock-change dates. Internal timestamps stay UTC; the
dashboard and logs display ``Asia/Colombo`` (UTC+5:30, no DST) via ``to_display_time``.

Definitions (assumptions; see I10 in docs/DECISIONS.md):

- ``asia``: 09:00 to 16:00 Asia/Tokyo. Japan has no DST, so this is 00:00 to 07:00 UTC all
  year, identical to the old fixed Asia session.
- ``london``: 07:00 to 12:00 Europe/London (07 to 12 UTC in winter, 06 to 11 UTC in summer).
- ``ny``: 07:00 to 12:00 America/New_York (12 to 17 UTC in winter, 11 to 16 UTC in summer).

In winter these equal the old fixed UTC sessions. Sessions MAY overlap here (real markets do,
and they overlap for an hour in the weeks when only one of UK and US is on summer time), so
``sessions_at`` returns every match; ``session_at`` returns the one that opened most recently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

DISPLAY_TZ = "Asia/Colombo"


def to_display_time(t: datetime) -> datetime:
    """Convert an aware datetime to the owner's display zone. Never use for logic."""
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("time must be timezone-aware")
    return t.astimezone(ZoneInfo(DISPLAY_TZ))


@dataclass(frozen=True)
class LocalSession:
    """A named window on a local wall clock: ``start`` inclusive, ``end`` exclusive."""

    name: str
    tz: str
    start: time
    end: time

    def __post_init__(self) -> None:
        try:
            ZoneInfo(self.tz)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"unknown time zone {self.tz!r}") from exc
        if not self.start < self.end:
            raise ValueError(f"session {self.name!r}: start must be before end on one local day")

    def _to_utc(self, day: date, wall: time) -> datetime:
        zone = ZoneInfo(self.tz)
        first = datetime.combine(day, wall, tzinfo=zone)  # fold=0
        utc = first.astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) != first.replace(tzinfo=None):
            raise ValueError(f"{self.name!r}: {wall} on {day} does not exist in {self.tz}")
        if first.utcoffset() != first.replace(fold=1).utcoffset():
            raise ValueError(f"{self.name!r}: {wall} on {day} is ambiguous in {self.tz}")
        return utc

    def window(self, day: date) -> tuple[datetime, datetime]:
        """UTC ``[start, end)`` for the local calendar date ``day`` in this session's zone."""
        return self._to_utc(day, self.start), self._to_utc(day, self.end)


@dataclass(frozen=True)
class LocalSessionConfig:
    sessions: tuple[LocalSession, ...]

    def __post_init__(self) -> None:
        names = [s.name for s in self.sessions]
        if len(set(names)) != len(names):
            raise ValueError("duplicate session names")

    @classmethod
    def utc_equivalent(cls, fixed: dict[str, tuple[int, int]]) -> LocalSessionConfig:
        """Fixed UTC hour windows (the old behaviour), e.g. ``{"asia": (0, 7)}``."""
        return cls(tuple(LocalSession(n, "UTC", time(s), time(e)) for n, (s, e) in fixed.items()))

    def names(self) -> list[str]:
        return [s.name for s in self.sessions]

    def window(self, day: date, name: str) -> tuple[datetime, datetime]:
        for s in self.sessions:
            if s.name == name:
                return s.window(day)
        raise KeyError(f"unknown session {name!r}")

    def windows_for_day(self, day: date) -> dict[str, tuple[datetime, datetime]]:
        """Every session's UTC window for the local calendar date ``day``."""
        return {s.name: s.window(day) for s in self.sessions}

    def _open_times(self, t: datetime) -> dict[str, datetime]:
        """Open time (UTC) of every session whose window contains ``t``."""
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("t must be timezone-aware")
        t = t.astimezone(UTC)
        opened: dict[str, datetime] = {}
        for s in self.sessions:
            for d in (t.date() - timedelta(days=1), t.date(), t.date() + timedelta(days=1)):
                a, b = s.window(d)
                if a <= t < b:
                    opened[s.name] = a
        return opened

    def sessions_at(self, t: datetime) -> list[str]:
        """Every session containing ``t`` (start inclusive, end exclusive), in config order."""
        opened = self._open_times(t)
        return [n for n in self.names() if n in opened]

    def session_at(self, t: datetime) -> str | None:
        """The containing session that opened most recently (ties: first in config order)."""
        opened = self._open_times(t)
        names = [n for n in self.names() if n in opened]
        return max(names, key=lambda n: (opened[n], -names.index(n))) if names else None


DEFAULT_LOCAL_SESSIONS = LocalSessionConfig((
    LocalSession("asia", "Asia/Tokyo", time(9), time(16)),
    LocalSession("london", "Europe/London", time(7), time(12)),
    LocalSession("ny", "America/New_York", time(7), time(12)),
))
