from datetime import timedelta

import pytest
from conftest import D0, make_level

from sx_assistant.ta.candles_talib import candle_pattern_setups
from sx_core.clock import available_at

M15 = timedelta(minutes=15)


def level_for(cd, known_after_bars=1):
    return make_level(cd["level_price"], D0 + known_after_bars * M15)


def test_labelled_candle_day_has_exactly_the_expected_pattern(candle_day):
    out = candle_pattern_setups(candle_day["candles"], [level_for(candle_day)])
    assert [(s.direction, s.event_time, s.known_at) for s in out] == [
        ("bullish", candle_day["candles"][17].time, available_at(
            candle_day["candles"][17].time, "M15"))]
    s = out[0]
    assert s.kind == "candle_pattern" and s.status == "causal"
    assert s.source.library == "TA-Lib" and s.source.version == "0.8.2"
    assert "not a signal" in s.plain_text and "engulfing" in s.plain_text


def test_without_a_nearby_level_nothing_is_counted(candle_day):
    assert candle_pattern_setups(candle_day["candles"], []) == []
    far = make_level(candle_day["level_price"] + 0.0100, D0 + M15)
    assert candle_pattern_setups(candle_day["candles"], [far]) == []


def test_proximity_is_measured_in_atr(candle_day):
    cs, lv = candle_day["candles"], [level_for(candle_day)]
    assert candle_pattern_setups(cs, lv, proximity_atr=0.1) == []
    wide = candle_pattern_setups(cs, lv, proximity_atr=100)
    assert {s.event_time for s in wide} == {cs[16].time, cs[17].time, cs[21].time}


def test_a_level_known_only_after_the_bar_does_not_count(candle_day):
    cs = candle_day["candles"]
    late = make_level(candle_day["level_price"], available_at(cs[17].time, "M15") + M15)
    assert candle_pattern_setups(cs, [late]) == []
    on_time = make_level(candle_day["level_price"], available_at(cs[17].time, "M15"))
    assert len(candle_pattern_setups(cs, [on_time])) == 1


def test_only_zone_and_level_kinds_count(candle_day):
    other = make_level(candle_day["level_price"], D0 + M15, kind="bos")
    assert candle_pattern_setups(candle_day["candles"], [other]) == []


def test_retrospective_levels_are_refused(candle_day):
    bad = make_level(candle_day["level_price"], D0 + M15, status="retrospective")
    with pytest.raises(ValueError, match="causal levels"):
        candle_pattern_setups(candle_day["candles"], [bad])


def test_no_pattern_before_atr_exists(candle_day):
    pair = candle_day["candles"][16:18]            # the engulfing pair alone: no ATR(14)
    rebased = [c.model_copy(update={"time": D0 + i * M15}) for i, c in enumerate(pair)]
    assert candle_pattern_setups(rebased, [make_level(0.0, D0)], proximity_atr=1e6) == []


def test_pattern_adapter_is_causal(assert_causal, candle_day):
    lv = [level_for(candle_day)]
    assert_causal(lambda cs: candle_pattern_setups(cs, lv, proximity_atr=100),
                  candle_day["candles"])
    assert_causal(lambda cs: candle_pattern_setups(cs, lv), candle_day["candles"])


def test_invalidation_names_the_pattern_bar_extreme(candle_day):
    s = candle_pattern_setups(candle_day["candles"], [level_for(candle_day)])[0]
    assert "below the pattern bar's low 1.08070" in s.invalidation
