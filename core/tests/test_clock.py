from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from sx_core.clock import (
    SessionConfig,
    available_at,
    bar_close,
    filter_known,
    is_closed,
    is_known,
    known_at_after_bars,
    previous_day,
    session_at,
    session_bounds,
    tf_delta,
)

T0 = datetime(2026, 10, 19, 6, 45, tzinfo=UTC)


def test_bar_close_and_availability():
    assert bar_close(T0, "M15") == datetime(2026, 10, 19, 7, 0, tzinfo=UTC)
    late = available_at(T0, "M15", timedelta(seconds=2))
    assert late == datetime(2026, 10, 19, 7, 0, 2, tzinfo=UTC)
    assert tf_delta("H4") == timedelta(hours=4)
    with pytest.raises(ValueError):
        tf_delta("M3")


def test_is_closed_boundary_is_inclusive():
    assert not is_closed(T0, "M15", datetime(2026, 10, 19, 6, 59, 59, tzinfo=UTC))
    assert is_closed(T0, "M15", datetime(2026, 10, 19, 7, 0, tzinfo=UTC))


def test_known_at_after_bars_waits_for_confirming_bars():
    assert known_at_after_bars(T0, "M15", 0) == bar_close(T0, "M15")
    assert known_at_after_bars(T0, "M15", 2) == datetime(2026, 10, 19, 7, 30, tzinfo=UTC)
    with pytest.raises(ValueError):
        known_at_after_bars(T0, "M15", -1)


def test_naive_times_refused():
    with pytest.raises(ValueError, match="timezone"):
        bar_close(datetime(2026, 10, 19), "M15")


def test_is_known_and_filter_known():
    class Obj:
        def __init__(self, k):
            self.known_at = k

    objs = [Obj(T0), Obj(T0 + timedelta(minutes=1))]
    assert is_known(T0, T0)
    assert filter_known(objs, T0) == objs[:1]
    plus2 = timezone(timedelta(hours=2))
    assert is_known(T0, T0.astimezone(plus2))


@pytest.mark.parametrize("hhmm,expected", [
    ((0, 0), "asia"), ((6, 59), "asia"), ((7, 0), "london"), ((11, 59), "london"),
    ((12, 0), "ny"), ((16, 59), "ny"), ((17, 0), None), ((23, 0), None),
])
def test_default_sessions(hhmm, expected):
    t = datetime(2026, 10, 19, *hhmm, tzinfo=UTC)
    assert session_at(t) == expected


def test_session_bounds():
    start, end = session_bounds(date(2026, 10, 19), "london")
    assert (start.hour, end.hour) == (7, 12) and start.tzinfo is UTC
    with pytest.raises(KeyError):
        session_bounds(date(2026, 10, 19), "tokyo")


def test_sessions_are_configurable():
    cfg = SessionConfig.from_hours({"asia": (22, 24), "london": (8, 12)})
    assert session_at(datetime(2026, 10, 19, 23, 0, tzinfo=UTC), cfg) == "asia"
    assert session_at(datetime(2026, 10, 19, 3, 0, tzinfo=UTC), cfg) is None


def test_invalid_session_configs_refused():
    with pytest.raises(ValueError, match="overlap"):
        SessionConfig.from_hours({"a": (0, 8), "b": (7, 12)})
    with pytest.raises(ValueError):
        SessionConfig.from_hours({"a": (5, 5)})
    with pytest.raises(ValueError):
        SessionConfig.from_hours({"a": (0, 25)})
    with pytest.raises(ValueError, match="duplicate"):
        SessionConfig((("a", 0, 60), ("a", 120, 180)))


def test_previous_day():
    assert previous_day(datetime(2026, 10, 19, 0, 5, tzinfo=UTC)) == date(2026, 10, 18)
