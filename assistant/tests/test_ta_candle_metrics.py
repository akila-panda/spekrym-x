"""Boundary tests for the I15 candle definitions. Prices are binary-exact (multiples of 0.25)."""

from datetime import UTC, datetime

import pytest

from sx_assistant.ta.candle_metrics import (
    DEFAULT_RULES,
    CandleRules,
    is_doji,
    is_engulfing,
    metrics,
    pin_bar,
)
from sx_core.contracts import Candle


def cd(o, h, lo, c, minute=0):
    t = datetime(2026, 10, 19, 0, minute, tzinfo=UTC)
    return Candle(instrument="EUR_USD", tf="M15", time=t, open=o, high=h, low=lo, close=c,
                  volume=1.0, bid_close=c, ask_close=c, complete=True)


def test_measurements():
    m = metrics(cd(1.25, 2.0, 1.0, 1.75))
    assert (m.range, m.body, m.upper_wick, m.lower_wick) == (1.0, 0.5, 0.25, 0.25)
    assert m.body_to_range == 0.5
    assert metrics(cd(1.5, 1.5, 1.5, 1.5)).body_to_range is None          # zero range


def test_zero_range_candle_has_no_shape():
    flat = cd(1.5, 1.5, 1.5, 1.5)
    assert not is_doji(flat) and pin_bar(flat) is None


@pytest.mark.parametrize("inclusive,expected", [(True, True), (False, False)])
def test_doji_boundary_equality(inclusive, expected):
    c = cd(1.0, 1.75, 0.0, 1.0 + 0.1875)         # body 0.1875 / range 1.75 = 0.107142...
    rules = CandleRules(doji_max_body_to_range=0.25, doji_inclusive=inclusive)
    exact = cd(1.0, 2.0, 0.0, 1.5)               # body 0.5 / range 2 = 0.25 exactly
    assert is_doji(c, rules)                      # clearly below the limit either way
    assert is_doji(exact, rules) is expected


def test_doji_just_above_the_limit_is_not_a_doji():
    assert not is_doji(cd(1.0, 2.0, 0.0, 1.75), CandleRules(doji_max_body_to_range=0.25))
    assert is_doji(cd(1.0, 2.0, 0.0, 1.0))                                # zero body, real range


def test_doji_rules_are_validated():
    with pytest.raises(ValueError):
        CandleRules(doji_max_body_to_range=1.5)
    with pytest.raises(ValueError):
        CandleRules(pin_min_wick_to_body=-1)


def test_bullish_and_bearish_pin_bars():
    rules = CandleRules(pin_max_body_to_range=0.5, pin_min_wick_to_body=2.0)
    assert pin_bar(cd(3.75, 4.0, 0.0, 4.0), rules) == "bullish"     # long lower wick, bull body
    assert pin_bar(cd(4.0, 4.0, 0.0, 3.75), rules) == "bullish"     # long lower wick, bear body
    assert pin_bar(cd(0.25, 4.0, 0.0, 0.0), rules) == "bearish"     # long upper wick, bear body
    assert pin_bar(cd(0.0, 4.0, 0.0, 0.25), rules) == "bearish"     # long upper wick, bull body


def test_pin_wick_to_body_boundary():
    # range 4.0, body 1.0, long (lower) wick 2.0, upper wick 1.0 -> wick/body exactly 2.0
    c = cd(2.0, 4.0, 0.0, 3.0)
    assert metrics(c).lower_wick == 2.0 and metrics(c).body == 1.0
    base = {"pin_max_body_to_range": 0.5, "pin_min_wick_to_body": 2.0}
    assert pin_bar(c, CandleRules(**base, pin_inclusive=True)) == "bullish"
    assert pin_bar(c, CandleRules(**base, pin_inclusive=False)) is None


def test_pin_body_to_range_boundary():
    c = cd(2.0, 4.0, 0.0, 3.0)                    # body/range = 0.25
    base = {"pin_max_body_to_range": 0.25, "pin_min_wick_to_body": 1.0}
    assert pin_bar(c, CandleRules(**base, pin_inclusive=True)) == "bullish"
    assert pin_bar(c, CandleRules(**base, pin_inclusive=False)) is None


def test_pin_bar_needs_one_clearly_longer_wick():
    assert pin_bar(cd(2.0, 3.0, 1.0, 2.0)) is None                    # equal wicks, zero body
    assert pin_bar(cd(1.0, 1.0, 1.0, 1.0)) is None


def test_zero_body_with_a_long_wick_is_a_pin_bar():
    assert pin_bar(cd(3.0, 4.0, 0.0, 3.0), CandleRules(pin_max_body_to_range=0.35)) == "bullish"


def test_pin_bar_with_a_big_body_is_rejected():
    assert pin_bar(cd(1.0, 4.0, 0.0, 3.5)) is None


@pytest.mark.parametrize("inclusive,expected", [(False, None), (True, "bullish")])
def test_bullish_engulfing_equal_edges(inclusive, expected):
    prev = cd(2.0, 2.5, 1.0, 1.0)                # bearish body 1.0..2.0
    cur = cd(1.0, 2.5, 0.5, 2.0)                 # bullish body 1.0..2.0, equal edges
    assert is_engulfing(prev, cur, CandleRules(engulf_inclusive=inclusive)) == expected


@pytest.mark.parametrize("inclusive,expected", [(False, None), (True, "bearish")])
def test_bearish_engulfing_equal_edges(inclusive, expected):
    prev = cd(1.0, 2.5, 0.5, 2.0)
    cur = cd(2.0, 2.5, 0.5, 1.0)
    assert is_engulfing(prev, cur, CandleRules(engulf_inclusive=inclusive)) == expected


def test_strict_engulfing_both_directions():
    assert is_engulfing(cd(2.0, 2.5, 1.0, 1.0), cd(0.75, 3.0, 0.5, 2.25)) == "bullish"
    assert is_engulfing(cd(1.0, 2.5, 0.5, 2.0), cd(2.25, 3.0, 0.5, 0.75)) == "bearish"


def test_partial_overlap_same_colour_and_doji_bodies_do_not_engulf():
    assert is_engulfing(cd(2.0, 2.5, 1.0, 1.0), cd(1.25, 3.0, 1.0, 2.25)) is None   # open inside
    assert is_engulfing(cd(2.0, 2.5, 1.0, 1.0), cd(0.5, 3.0, 0.25, 1.75)) is None   # close inside
    assert is_engulfing(cd(1.0, 2.5, 0.5, 2.0), cd(0.5, 3.0, 0.5, 2.5)) is None      # both bull
    assert is_engulfing(cd(1.5, 2.0, 1.0, 1.5), cd(1.0, 3.0, 0.5, 2.0),
                        CandleRules(engulf_inclusive=True)) is None                   # prev body 0


def test_defaults_are_the_proposed_unapproved_values():
    r = DEFAULT_RULES
    assert (r.doji_max_body_to_range, r.pin_max_body_to_range, r.pin_min_wick_to_body) == (
        0.10, 0.35, 2.0)
    assert (r.doji_inclusive, r.pin_inclusive, r.engulf_inclusive) == (True, True, False)
