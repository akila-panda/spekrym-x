import sys

import pytest

pytest.importorskip("trendln", reason='install the extra: pip install -e "assistant[retro]"')

from sx_assistant.ta.levels_trendln import trendline_setups  # noqa: E402
from sx_assistant.ta.normalize import require_causal  # noqa: E402
from sx_core.clock import available_at  # noqa: E402


def test_lines_are_tagged_retrospective_and_known_at_the_window_end(m15_candles):
    out = trendline_setups(m15_candles)
    assert {s.direction for s in out} == {"bullish", "bearish"}      # support and resistance
    assert 0 < len(out) <= 6
    end = available_at(m15_candles[-1].time, "M15")
    for s in out:
        assert s.status == "retrospective" and s.kind == "support_resistance"
        assert s.known_at == end and s.event_time <= s.known_at
        assert s.geometry.t_end == m15_candles[-1].time
        assert "Retrospective" in s.plain_text and s.source.library == "trendln"


def test_output_is_deterministic(m15_candles):
    assert trendline_setups(m15_candles) == trendline_setups(m15_candles)


def test_the_harness_flags_trendlines_as_non_causal(m15_candles, check_prefix_equality):
    """This is why they are labelled Retrospective and kept out of models and paper."""
    found = check_prefix_equality(trendline_setups, m15_candles, prefix_lengths=[30, 60, 96])
    assert found


def test_retrospective_setups_cannot_feed_models(m15_candles):
    with pytest.raises(ValueError, match="non-causal"):
        require_causal(trendline_setups(m15_candles))


def test_needs_enough_bars(m15_candles):
    with pytest.raises(ValueError, match="10 bars"):
        trendline_setups(m15_candles[:9])


def test_missing_library_gives_a_clear_error(m15_candles, monkeypatch):
    monkeypatch.setitem(sys.modules, "trendln", None)
    with pytest.raises(ImportError, match=r"assistant\[retro\]"):
        trendline_setups(m15_candles)
