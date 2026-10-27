from datetime import UTC, date, datetime, time

import pytest

from sx_core.trading_calendar import (
    CALENDARS,
    FX_CALENDAR,
    TradingCalendar,
    calendar_for,
    reference_day,
)

MON, TUE, WED, THU, FRI = (date(2026, 10, d) for d in (19, 20, 21, 22, 23))


def utc(*a):
    return datetime(*a, tzinfo=UTC)


def test_monday_to_thursday_are_whole_utc_days():
    for d in (MON, TUE, WED, THU):
        assert FX_CALENDAR.trading_window(d) == (
            utc(d.year, d.month, d.day), utc(d.year, d.month, d.day + 1))


def test_friday_ends_at_the_new_york_close_which_moves_with_us_dst():
    assert FX_CALENDAR.trading_window(date(2026, 10, 23))[1] == utc(2026, 10, 23, 21)   # EDT
    assert FX_CALENDAR.trading_window(date(2026, 11, 6))[1] == utc(2026, 11, 6, 22)     # EST
    assert FX_CALENDAR.trading_window(date(2026, 3, 6))[1] == utc(2026, 3, 6, 22)       # EST
    assert FX_CALENDAR.trading_window(date(2026, 3, 13))[1] == utc(2026, 3, 13, 21)     # EDT


def test_weekend_and_holidays_are_not_trading_days():
    assert FX_CALENDAR.trading_window(date(2026, 10, 24)) is None       # Saturday
    assert FX_CALENDAR.trading_window(date(2026, 10, 25)) is None       # Sunday
    cal = TradingCalendar("x", holidays=frozenset({TUE}))
    assert cal.trading_window(TUE) is None and not cal.is_trading_day(TUE)
    assert cal.is_trading_day(WED)


def test_previous_trading_days_skip_weekends_and_holidays():
    mon = date(2026, 10, 26)
    assert FX_CALENDAR.previous_trading_days(mon, 3) == [FRI, THU, WED]
    cal = TradingCalendar("x", holidays=frozenset({FRI}))
    assert cal.previous_trading_days(mon, 2) == [THU, WED]


def test_reference_day_basic_rules():
    mon = date(2026, 10, 26)
    days = {MON, TUE, WED, THU, FRI}
    assert reference_day(mon, days, FX_CALENDAR) == FRI                 # Monday -> Friday
    assert reference_day(date(2026, 10, 27), days | {mon}, FX_CALENDAR) == mon
    assert reference_day(WED, days, FX_CALENDAR) == TUE
    assert reference_day(date(2026, 10, 24), days, FX_CALENDAR) == FRI  # Saturday
    assert reference_day(date(2026, 10, 25), days, FX_CALENDAR) == FRI  # Sunday


def test_reference_day_never_returns_the_day_itself_or_a_later_one():
    assert reference_day(WED, {WED, THU}, FX_CALENDAR) is None


def test_missing_days_count_toward_the_limit_but_holidays_do_not():
    mon = date(2026, 10, 26)
    only_mon_week_ago = {date(2026, 10, 12)}                  # 10 trading days back
    assert reference_day(mon, only_mon_week_ago, FX_CALENDAR, max_lookback=5) is None
    assert reference_day(mon, {THU}, FX_CALENDAR, max_lookback=2) == THU    # Fri missing, Thu ok
    assert reference_day(mon, {THU}, FX_CALENDAR, max_lookback=1) is None   # Fri examined, rejected
    cal = TradingCalendar("x", holidays=frozenset({FRI}))
    assert reference_day(mon, {THU}, cal, max_lookback=1) == THU            # holiday not counted


def test_lookback_must_be_positive():
    with pytest.raises(ValueError, match="max_lookback"):
        reference_day(MON, set(), FX_CALENDAR, max_lookback=0)


def test_calendars_are_per_instrument():
    assert calendar_for("EUR_USD") is FX_CALENDAR and set(CALENDARS) >= {"EUR_USD", "USD_JPY"}
    with pytest.raises(ValueError, match="no trading calendar"):
        calendar_for("BTC_USD")


def test_a_sunday_to_thursday_calendar_is_honoured():
    cal = TradingCalendar("sun_thu", weekdays=frozenset({6, 0, 1, 2, 3}), close_weekday=3,
                          close_tz="UTC", close_time=time(17))
    assert cal.trading_window(date(2026, 10, 25)) is not None             # Sunday trades
    assert cal.trading_window(FRI) is None
    assert cal.trading_window(THU)[1] == utc(2026, 10, 22, 17)
    assert reference_day(date(2026, 10, 25), {THU}, cal) == THU           # Sunday <- Thursday


def test_bad_calendars_are_rejected():
    with pytest.raises(ValueError):
        TradingCalendar("x", weekdays=frozenset())
    with pytest.raises(ValueError):
        TradingCalendar("x", weekdays=frozenset({7}))
    with pytest.raises(Exception, match="No time zone"):
        TradingCalendar("x", close_tz="Mars/Olympus")
