import pytest
from producers import causal_swings, early_known_at, edge_swings, value_leak

from sx_core.causality import CausalityViolation, check_prefix_equality


def test_fixture_has_swings(m15_candles):
    """Guard: the tests below are meaningless if the fixture has no swings."""
    assert len(causal_swings(m15_candles)) >= 5


def test_causal_producer_passes(assert_causal, m15_candles):
    assert_causal(causal_swings, m15_candles)


def test_early_known_at_is_caught(m15_candles):
    found = check_prefix_equality(early_known_at, m15_candles)
    assert found, "stamping known_at before the confirming bars must be detected"
    assert {v.kind for v in found} == {"missing_in_prefix"}


def test_value_leak_is_caught(m15_candles):
    found = check_prefix_equality(value_leak, m15_candles)
    assert "changed" in {v.kind for v in found}


def test_edge_lookahead_is_caught(m15_candles):
    found = check_prefix_equality(edge_swings, m15_candles)
    assert "extra_in_prefix" in {v.kind for v in found}


def test_assert_causal_raises_with_readable_message(assert_causal, m15_candles):
    with pytest.raises(CausalityViolation) as err:
        assert_causal(early_known_at, m15_candles)
    assert "missing_in_prefix" in str(err.value)
    assert err.value.violations


def test_explicit_prefix_lengths_can_miss_a_leak(m15_candles):
    """Documents why sampling is not the default: these two prefixes see nothing wrong."""
    assert check_prefix_equality(early_known_at, m15_candles, prefix_lengths=[10, 50]) == []
    assert check_prefix_equality(early_known_at, m15_candles)


def test_bad_prefix_length_is_rejected(m15_candles):
    with pytest.raises(ValueError, match="prefix lengths"):
        check_prefix_equality(causal_swings, m15_candles, prefix_lengths=[0])


def test_rejects_incomplete_candles(m15_candles):
    bad = [m15_candles[0].model_copy(update={"complete": False}), *m15_candles[1:]]
    with pytest.raises(ValueError, match="complete"):
        check_prefix_equality(causal_swings, bad)


def test_rejects_known_before_event(m15_candles):
    def broken(cs):
        s = causal_swings(cs)
        return [x.model_copy(update={"known_at": x.event_time.replace(year=2000)}) for x in s]

    with pytest.raises(ValueError, match="known_at before event_time"):
        check_prefix_equality(broken, m15_candles)


def test_dict_objects_are_supported(m15_candles):
    def as_dicts(cs):
        return [s.model_dump() for s in causal_swings(cs)]

    assert check_prefix_equality(as_dicts, m15_candles) == []
