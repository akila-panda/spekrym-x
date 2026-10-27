from datetime import timedelta

import pytest
from conftest import at

from sx_assistant.ta.normalize import analyze_causal, as_of, lifecycle_at, require_causal
from sx_assistant.ta.sessions import session_setups
from sx_assistant.ta.smc_adapter import smc_setups

M15 = timedelta(minutes=15)


@pytest.fixture(scope="module")
def setups(day):
    return smc_setups(day, swing_length=2) + session_setups(day)


@pytest.fixture(scope="module")
def full(day, day_tail):
    return day + day_tail


def pick(setups, kind, direction, bar):
    hits = [s for s in setups if s.kind == kind and s.direction == direction
            and s.event_time == at(bar)]
    assert len(hits) == 1
    return hits[0]


# Hand-derived from the tail bars in scripts/make_ta_fixtures.py. Bar i closes at at(i + 1).
# (kind, direction, event bar, t = open time of bar N, i.e. bars < N have closed, expected)
CASES = [
    ("swing", "bearish", 11, 20, "fresh"),        # swing high 16: bar 20 (close 17) not closed yet
    ("swing", "bearish", 11, 21, "broken"),       # bar 20 (close 17 > 16) has now closed
    ("fvg", "bullish", 19, 28, "fresh"),          # zone 10-14, nothing has entered yet
    ("fvg", "bullish", 19, 29, "tested"),         # bar 28 low 14 touches the zone
    ("fvg", "bullish", 19, 30, "tested"),         # bar 29 closes 12, still inside
    ("fvg", "bullish", 19, 31, "mitigated"),      # bar 30 closes 8, below the zone
    ("order_block", "bullish", 16, 30, "fresh"),
    ("order_block", "bullish", 16, 31, "tested"),     # bar 30 low 7 enters 3-9
    ("order_block", "bullish", 16, 32, "mitigated"),  # bar 31 closes 2, below 3
    ("swing", "bullish", 16, 31, "fresh"),
    ("swing", "bullish", 16, 32, "broken"),       # swing low 3: bar 31 closes 2
    ("swing", "bullish", 5, 32, "fresh"),         # swing low 2: closes 2 is not below 2
    ("swing", "bullish", 5, 33, "broken"),        # bar 32 closes 1
    ("session_level", "bullish", 5, 32, "fresh"),
    ("session_level", "bullish", 5, 33, "broken"),
    ("session_level", "bearish", 22, 33, "fresh"),    # Asia high 25 never closed above
    ("swing", "bearish", 22, 33, "fresh"),
    ("bos", "bullish", 20, 33, "fresh"),              # events do not evolve
]


@pytest.mark.parametrize(("kind", "direction", "bar", "t_idx", "expected"), CASES)
def test_lifecycle_as_of(setups, full, kind, direction, bar, t_idx, expected):
    s = pick(setups, kind, direction, bar)
    assert lifecycle_at(s, full, at(t_idx)) == expected


def test_lifecycle_never_uses_bars_that_have_not_closed(setups, full):
    s = pick(setups, "fvg", "bullish", 19)
    # bar 30 (the mitigating bar) opens at at(30) and closes at at(31)
    assert lifecycle_at(s, full, at(31) - timedelta(seconds=1)) == "tested"
    assert lifecycle_at(s, full, at(31)) == "mitigated"


def test_as_of_is_independent_of_later_bars(setups, full):
    for i in range(1, 34):
        t = at(i)
        shown_full = as_of(setups, full, t)
        closed = [c for c in full if c.time + M15 <= t]
        assert shown_full == as_of(setups, closed, t)


def test_as_of_hides_what_was_not_yet_known(setups, full):
    shown = as_of(setups, full, at(21))                 # 05:15
    kinds = {(s.kind, s.event_time) for s in shown}
    assert ("fvg", at(19)) in kinds and ("order_block", at(16)) in kinds
    assert ("bos", at(20)) not in kinds                 # known only at 06:15
    assert not [s for s in shown if s.kind == "session_level"]
    assert all(s.known_at <= at(21) for s in shown)


def test_as_of_does_not_change_the_originals(setups, full):
    before = list(setups)
    as_of(setups, full, at(33))
    assert setups == before and all(s.lifecycle == "fresh" for s in setups)


def test_require_causal(setups):
    assert require_causal(setups) == setups
    bad = setups[0].model_copy(update={"status": "retrospective"})
    with pytest.raises(ValueError, match="non-causal"):
        require_causal([*setups, bad])


def test_analyze_causal_combines_adapters(day, setups):
    out = analyze_causal(day, swing_length=2)
    assert {s.id for s in setups} <= {s.id for s in out}
    assert len({s.id for s in out}) == len(out)
    assert all(s.status == "causal" for s in out)
    assert [(s.known_at, s.event_time, s.id) for s in out] == sorted(
        (s.known_at, s.event_time, s.id) for s in out)


def test_whole_pipeline_is_causal(assert_causal, m15_candles):
    def producer(cs):
        return analyze_causal(cs, swing_length=3)
    assert "candle_pattern" in {s.kind for s in producer(m15_candles[:40])}   # not vacuous
    assert_causal(producer, m15_candles[:40])
