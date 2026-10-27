"""P9: DST-aware sessions. UK clocks change on the last Sunday of March/October, US clocks on
the second Sunday of March and the first Sunday of November, so the two differ for weeks."""

from datetime import UTC, date, datetime, time, timedelta

import pytest

from sx_core.clock import (
    DEFAULT_LOCAL_SESSIONS as CFG,
)
from sx_core.clock import (
    DEFAULT_SESSIONS,
    LocalSession,
    LocalSessionConfig,
    session_bounds,
    to_display_time,
)


def hours(day: date, name: str) -> tuple[int, int]:
    a, b = CFG.window(day, name)
    assert a.minute == b.minute == 0
    return a.hour, b.hour


# --- Asia is explicit and never moves ---------------------------------------------------

@pytest.mark.parametrize("day", [date(2026, 1, 15), date(2026, 3, 9), date(2026, 3, 30),
                                 date(2026, 7, 1), date(2026, 10, 26), date(2026, 11, 2)])
def test_asia_is_00_to_07_utc_all_year(day):
    assert hours(day, "asia") == (0, 7)


# --- normal winter and summer weeks -----------------------------------------------------

def test_winter_matches_old_fixed_sessions():
    day = date(2026, 1, 14)
    for name in ("asia", "london", "ny"):
        old = session_bounds(day, name, DEFAULT_SESSIONS)
        assert CFG.window(day, name) == old


def test_summer_both_shifted_one_hour_earlier():
    day = date(2026, 7, 15)
    assert hours(day, "london") == (6, 11)
    assert hours(day, "ny") == (11, 16)


# --- the clock-change weeks, which are different for the UK and the US -------------------

@pytest.mark.parametrize(("day", "london", "ny"), [
    (date(2026, 3, 6), (7, 12), (12, 17)),     # both on winter time
    (date(2026, 3, 8), (7, 12), (11, 16)),     # US changes this Sunday; NY already EDT
    (date(2026, 3, 9), (7, 12), (11, 16)),     # US summer, UK still winter
    (date(2026, 3, 27), (7, 12), (11, 16)),    # last Friday before the UK change
    (date(2026, 3, 29), (6, 11), (11, 16)),    # UK changes this Sunday; London already BST
    (date(2026, 3, 30), (6, 11), (11, 16)),    # both on summer time
    (date(2026, 10, 23), (6, 11), (11, 16)),   # both on summer time
    (date(2026, 10, 25), (7, 12), (11, 16)),   # UK changes back this Sunday
    (date(2026, 10, 26), (7, 12), (11, 16)),   # UK winter, US still summer
    (date(2026, 10, 30), (7, 12), (11, 16)),
    (date(2026, 11, 1), (7, 12), (12, 17)),    # US changes back this Sunday
    (date(2026, 11, 2), (7, 12), (12, 17)),    # both on winter time
])
def test_transition_weeks(day, london, ny):
    assert hours(day, "london") == london
    assert hours(day, "ny") == ny


def test_uk_and_us_change_on_different_dates():
    # the NY window moves between 3-6 and 3-9, the London window between 3-27 and 3-30
    assert hours(date(2026, 3, 6), "ny") != hours(date(2026, 3, 9), "ny")
    assert hours(date(2026, 3, 6), "london") == hours(date(2026, 3, 9), "london")
    assert hours(date(2026, 3, 27), "ny") == hours(date(2026, 3, 30), "ny")
    assert hours(date(2026, 3, 27), "london") != hours(date(2026, 3, 30), "london")


def test_session_lengths_are_constant_in_utc_hours():
    day = date(2026, 3, 1)
    while day < date(2026, 12, 1):
        for name, n in (("asia", 7), ("london", 5), ("ny", 5)):
            a, b = CFG.window(day, name)
            assert b - a == timedelta(hours=n), (day, name)
        day += timedelta(days=1)


def test_overlap_only_in_mismatch_weeks():
    in_mismatch = datetime(2026, 3, 10, 11, 30, tzinfo=UTC)   # London 07-12, NY 11-16
    assert CFG.sessions_at(in_mismatch) == ["london", "ny"]
    assert CFG.session_at(in_mismatch) == "ny"                # NY opened more recently
    same_week_later = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
    assert CFG.sessions_at(same_week_later) == ["ny"]
    both_summer = datetime(2026, 7, 15, 11, 0, tzinfo=UTC)
    assert CFG.sessions_at(both_summer) == ["ny"]             # London ended 11:00 exclusive
    both_winter = datetime(2026, 1, 14, 12, 0, tzinfo=UTC)
    assert CFG.sessions_at(both_winter) == ["ny"]


def test_session_at_boundaries_start_inclusive_end_exclusive():
    assert CFG.session_at(datetime(2026, 10, 26, 6, 59, tzinfo=UTC)) == "asia"
    assert CFG.session_at(datetime(2026, 10, 26, 7, 0, tzinfo=UTC)) == "london"
    assert CFG.session_at(datetime(2026, 10, 26, 10, 59, tzinfo=UTC)) == "london"
    assert CFG.session_at(datetime(2026, 10, 26, 11, 0, tzinfo=UTC)) == "ny"   # London to 12
    assert CFG.session_at(datetime(2026, 10, 26, 16, 0, tzinfo=UTC)) is None


def test_transition_day_boundary_uses_that_days_offset():
    # UK spring forward 2026-03-29 01:00 UTC: London 07:00 local is 06:00 UTC that day
    assert CFG.session_at(datetime(2026, 3, 29, 6, 0, tzinfo=UTC)) == "london"
    assert CFG.session_at(datetime(2026, 3, 28, 6, 0, tzinfo=UTC)) == "asia"
    # UK fall back 2026-10-25 01:00 UTC: London 07:00 local is 07:00 UTC
    assert CFG.session_at(datetime(2026, 10, 25, 6, 0, tzinfo=UTC)) == "asia"
    assert CFG.session_at(datetime(2026, 10, 25, 7, 0, tzinfo=UTC)) == "london"


# --- guards -----------------------------------------------------------------------------

def test_nonexistent_local_time_raises():
    s = LocalSession("x", "America/New_York", time(2, 30), time(3, 30))
    with pytest.raises(ValueError, match="does not exist"):
        s.window(date(2026, 3, 8))


def test_ambiguous_local_time_raises():
    s = LocalSession("x", "America/New_York", time(1, 30), time(3, 0))
    with pytest.raises(ValueError, match="ambiguous"):
        s.window(date(2026, 11, 1))


def test_bad_config_rejected():
    with pytest.raises(ValueError):
        LocalSession("x", "Mars/Olympus", time(1), time(2))
    with pytest.raises(ValueError, match="before end"):
        LocalSession("x", "UTC", time(5), time(5))
    with pytest.raises(ValueError, match="duplicate"):
        LocalSessionConfig((LocalSession("a", "UTC", time(1), time(2)),
                            LocalSession("a", "UTC", time(3), time(4))))
    with pytest.raises(KeyError):
        CFG.window(date(2026, 1, 1), "tokyo")
    with pytest.raises(ValueError, match="timezone-aware"):
        CFG.sessions_at(datetime(2026, 1, 1, 7, 0))


def test_utc_equivalent_reproduces_fixed_sessions_all_year():
    fixed = LocalSessionConfig.utc_equivalent(
        {"asia": (0, 7), "london": (7, 12), "ny": (12, 17)})
    day = date(2026, 1, 1)
    while day < date(2027, 1, 1):
        for name in ("asia", "london", "ny"):
            assert fixed.window(day, name) == session_bounds(day, name, DEFAULT_SESSIONS)
        day += timedelta(days=7)


def test_display_zone_is_colombo_and_does_not_change_the_instant():
    t = datetime(2026, 10, 26, 7, 0, tzinfo=UTC)
    shown = to_display_time(t)
    assert shown == t
    assert shown.utcoffset() == timedelta(hours=5, minutes=30)
    assert shown.hour == 12 and shown.minute == 30
    with pytest.raises(ValueError):
        to_display_time(datetime(2026, 10, 26, 7, 0))


def test_default_sessions_are_the_approved_i10_hours():
    """Owner approved 2026-10-27: strategy-defined windows, IANA zones, [start, end)."""
    from datetime import time

    from sx_core.local_sessions import DEFAULT_LOCAL_SESSIONS

    got = {s.name: (s.tz, s.start, s.end) for s in DEFAULT_LOCAL_SESSIONS.sessions}
    assert got == {
        "asia": ("Asia/Tokyo", time(9), time(16)),
        "london": ("Europe/London", time(7), time(12)),
        "ny": ("America/New_York", time(7), time(12)),
    }
