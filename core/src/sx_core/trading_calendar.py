"""Trading calendars and the "previous completed trading day" rule (decision P10 / X14).

A *trading day* is a UTC calendar day (decision X10: days and D bars start at 00:00 UTC) on
which the instrument's calendar says the market trades. Its *trading window* is the part of
that UTC day that is open:

- Monday to Thursday: the whole UTC day.
- Friday: from 00:00 UTC to the weekly close, 17:00 on ``close_tz`` (default America/New_York),
  converted to UTC **for that date**, so it is 21:00 UTC in US summer time and 22:00 in winter.
- Saturday, Sunday and listed holidays: not trading days. The short Sunday-evening stub after
  the weekly reopen belongs to no trading day and is never used for a level.

A trading day is *complete* only when every bar slot of its trading window is present (that is
checked by the caller, which has the bars). ``reference_day`` picks the day whose levels apply
on a given date: the nearest earlier trading day that is complete, looking back at most
``max_lookback`` trading days. It never returns a day with missing data.

Assumptions (owner to review): the weekly close time, no daily maintenance break, and an empty
holiday list by default. The calendar is per instrument; a calendar must be registered for an
instrument or passed explicitly, because not every instrument trades Monday to Friday.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

DEFAULT_MAX_LOOKBACK = 5


@dataclass(frozen=True)
class TradingCalendar:
    name: str
    weekdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})        # Monday = 0
    close_weekday: int = 4                                        # the day with a weekly close
    close_tz: str = "America/New_York"
    close_time: time = time(17, 0)
    holidays: frozenset[date] = field(default_factory=frozenset)  # full-day closures (UTC dates)

    def __post_init__(self) -> None:
        if not self.weekdays or not self.weekdays <= set(range(7)):
            raise ValueError("weekdays must be a non-empty subset of 0..6")
        ZoneInfo(self.close_tz)                                   # raises on an unknown zone

    def is_trading_day(self, day: date) -> bool:
        return day.weekday() in self.weekdays and day not in self.holidays

    def trading_window(self, day: date) -> tuple[datetime, datetime] | None:
        """UTC ``[start, end)`` of the open part of ``day``, or ``None`` if it is not traded."""
        if not self.is_trading_day(day):
            return None
        start = datetime(day.year, day.month, day.day, tzinfo=UTC)
        end = start + timedelta(days=1)
        if day.weekday() == self.close_weekday:
            local = datetime.combine(day, self.close_time, tzinfo=ZoneInfo(self.close_tz))
            end = local.astimezone(UTC)
        return start, end

    def previous_trading_days(self, day: date, limit: int) -> list[date]:
        """Up to ``limit`` trading days strictly before ``day``, nearest first."""
        out: list[date] = []
        d = day
        for _ in range(limit * 7 + 14):                           # far more than enough
            d -= timedelta(days=1)
            if self.is_trading_day(d):
                out.append(d)
                if len(out) == limit:
                    break
        return out


FX_CALENDAR = TradingCalendar("fx_24x5")
CALENDARS: dict[str, TradingCalendar] = {
    i: FX_CALENDAR for i in ("EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD",
                             "USD_CHF", "NZD_USD")
}


def calendar_for(instrument: str) -> TradingCalendar:
    try:
        return CALENDARS[instrument]
    except KeyError:
        raise ValueError(f"no trading calendar registered for {instrument!r}; "
                         "pass one explicitly") from None


def reference_day(on: date, complete_days: Collection[date], calendar: TradingCalendar,
                  max_lookback: int = DEFAULT_MAX_LOOKBACK) -> date | None:
    """The completed trading day whose levels apply on ``on`` (nearest earlier one).

    Only trading days count toward ``max_lookback``; a trading day with missing data counts
    (it was examined and rejected), a weekend or holiday does not. ``None`` if none qualifies.
    """
    if max_lookback < 1:
        raise ValueError("max_lookback must be >= 1")
    have = set(complete_days)
    for d in calendar.previous_trading_days(on, max_lookback):
        if d in have:
            return d
    return None
