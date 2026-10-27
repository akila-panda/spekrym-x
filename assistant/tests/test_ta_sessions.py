import re
from datetime import UTC, datetime, time

import pytest

from sx_assistant.ta.sessions import session_setups
from sx_core.clock import LocalSession, LocalSessionConfig
from sx_core.contracts import Candle


def label(s):
    """'Asia', 'London', 'New York' or 'Previous day' from a setup's plain text."""
    return re.match(r"(Asia|London|New York|Previous day) (high|low)", s.plain_text).group(1)


def window(s):
    return re.search(r"(\d\d:\d\d-\d\d:\d\d) UTC", s.plain_text).group(1)


def by_text(setups, text):
    hits = [s for s in setups if s.plain_text.startswith(text)]
    assert len(hits) == 1, [s.plain_text for s in setups]
    return hits[0]


def test_one_bst_day_has_three_sessions_and_the_day_itself_as_previous_day(m15_candles):
    out = session_setups(m15_candles)
    assert sorted(label(s) for s in out) == [
        "Asia", "Asia", "London", "London", "New York", "New York", "Previous day",
        "Previous day"]
    asia = [c for c in m15_candles if c.time.hour < 7]
    assert by_text(out, "Asia high").geometry.price_high == max(c.high for c in asia)
    assert by_text(out, "Asia low").geometry.price_low == min(c.low for c in asia)
    ldn = [c for c in m15_candles if 6 <= c.time.hour < 11]       # BST: 06:00-11:00 UTC
    assert by_text(out, "London high").geometry.price_high == max(c.high for c in ldn)
    ny = [c for c in m15_candles if 11 <= c.time.hour < 16]       # EDT: 11:00-16:00 UTC
    assert by_text(out, "New York low").geometry.price_low == min(c.low for c in ny)


def test_known_at_is_the_window_end_and_never_before_the_event(m15_candles):
    out = session_setups(m15_candles)
    ends = {"Asia": 7, "London": 11, "New York": 16}   # BST/EDT: UTC hours
    for s in out:
        if label(s) in ends:
            assert s.known_at == datetime(2026, 10, 19, ends[label(s)], tzinfo=UTC)
        assert s.event_time <= s.known_at and s.status == "causal"
    pd = by_text(out, "Previous day high")
    assert pd.known_at == datetime(2026, 10, 20, tzinfo=UTC)
    assert pd.geometry.price_high == max(c.high for c in m15_candles)


def test_orientation_high_bearish_low_bullish(m15_candles):
    out = session_setups(m15_candles)
    assert by_text(out, "Asia high").direction == "bearish"
    assert by_text(out, "Asia low").direction == "bullish"


def test_incomplete_session_emits_nothing(m15_candles):
    out = session_setups(m15_candles[:60])       # ends 14:45: London done, New York not
    assert {label(s) for s in out} == {"Asia", "London"}
    assert not [s for s in out if s.plain_text.startswith("Previous")]


def test_one_missing_bar_inside_a_session_drops_that_session(m15_candles):
    gappy = [c for c in m15_candles if c.time != datetime(2026, 10, 19, 3, 0, tzinfo=UTC)]
    out = session_setups(gappy)
    assert not [s for s in out if s.plain_text.startswith("Asia")]
    assert [s for s in out if s.plain_text.startswith("London")]


def test_dst_week_london_window_moves_but_new_york_does_not(dst_h1):
    out = session_setups(dst_h1)
    fri = by_text([s for s in out if "2026-10-23" in s.plain_text], "London high")
    mon = by_text([s for s in out if "2026-10-26" in s.plain_text], "London high")
    assert "06:00-11:00 UTC" in fri.plain_text and "07:00-12:00 UTC" in mon.plain_text
    assert fri.known_at == datetime(2026, 10, 23, 11, tzinfo=UTC)
    assert mon.known_at == datetime(2026, 10, 26, 12, tzinfo=UTC)
    # the 06:00 UTC spike (30 pips) is in Friday's London window and not in Monday's
    assert fri.geometry.price_high == pytest.approx(1.0830)
    assert mon.geometry.price_high < 1.0813
    ny = [s for s in out if s.plain_text.startswith("New York high")]
    assert len(ny) == 3 and {window(s) for s in ny} == {"11:00-16:00"}   # US on EDT all week


def test_previous_day_levels_follow_the_trading_calendar(dst_h1):
    out = session_setups(dst_h1)
    known = {s.known_at for s in out if s.plain_text.startswith("Previous day")}
    assert datetime(2026, 10, 23, tzinfo=UTC) in known                  # Thursday, ends 00:00 Fri
    assert datetime(2026, 10, 23, 21, tzinfo=UTC) in known              # Friday: weekly close (EDT)
    assert datetime(2026, 10, 24, tzinfo=UTC) not in known              # no day ends at Sat 00:00
    assert datetime(2026, 10, 26, tzinfo=UTC) not in known              # Sunday: not traded
    assert datetime(2026, 10, 27, tzinfo=UTC) in known                  # Monday


def test_utc_equivalent_config_reproduces_the_old_fixed_sessions(m15_candles):
    fixed = LocalSessionConfig.utc_equivalent({"asia": (0, 7), "london": (7, 12), "ny": (12, 17)})
    out = session_setups(m15_candles, fixed)
    assert by_text(out, "London high").known_at == datetime(2026, 10, 19, 12, tzinfo=UTC)


def test_timeframe_must_be_intraday_and_divide_the_window(m15_candles, dst_h1):
    h4 = [c.model_copy(update={"tf": "H4"}) for c in m15_candles[:4]]
    with pytest.raises(ValueError, match="intraday"):
        session_setups(h4)
    odd = LocalSessionConfig((LocalSession("x", "UTC", time(7, 30), time(12)),))
    with pytest.raises(ValueError, match="does not divide"):
        session_setups(dst_h1, odd)


def test_sessions_are_causal(assert_causal, m15_candles, dst_h1):
    assert_causal(session_setups, m15_candles)
    assert_causal(session_setups, dst_h1)


def test_ids_do_not_depend_on_prices(m15_candles):
    shifted = [Candle.model_validate({**c.model_dump(), "open": c.open + 0.01,
                                      "high": c.high + 0.01, "low": c.low + 0.01,
                                      "close": c.close + 0.01}) for c in m15_candles]
    assert {s.id for s in session_setups(m15_candles)} == {s.id for s in session_setups(shifted)}


def test_wire_round_trip(m15_candles):
    from sx_core.contracts import Setup
    for s in session_setups(m15_candles):
        assert Setup.model_validate(s.to_wire()) == s
