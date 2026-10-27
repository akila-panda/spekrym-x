from datetime import UTC, datetime, timedelta, timezone

import pytest

from sx_core.contracts import make_id, order_id, setup_id, suggestion_id

T = datetime(2026, 10, 19, 6, 45, tzinfo=UTC)


def test_same_inputs_same_id_and_shape():
    a = setup_id("session_level", "EUR_USD", "M15", "neutral", T, "asia_high")
    assert a == setup_id("session_level", "EUR_USD", "M15", "neutral", T, "asia_high")
    prefix, digest = a.split(":")
    assert prefix == "setup" and len(digest) == 16 and int(digest, 16) >= 0


def test_known_value_is_pinned():
    """Pins the hash so an accidental change to id construction is noticed."""
    assert make_id("x", "a", 1, True, None, T) == "x:03e0a9426b1e4af2"


def test_each_semantic_field_changes_the_id():
    base = ("session_level", "EUR_USD", "M15", "neutral", T, "asia_high")
    ids = {setup_id(*base)}
    for i, alt in enumerate(["swing", "GBP_USD", "H1", "bullish", T + timedelta(minutes=15), "x"]):
        changed = list(base)
        changed[i] = alt
        ids.add(setup_id(*changed))
    assert len(ids) == 7


def test_floats_are_refused_so_prices_cannot_enter_ids():
    with pytest.raises(TypeError, match="float"):
        make_id("setup", "EUR_USD", 1.0861)  # type: ignore[arg-type]


def test_equivalent_instants_give_the_same_id():
    plus2 = timezone(timedelta(hours=2))
    assert make_id("x", T) == make_id("x", T.astimezone(plus2))


def test_naive_datetime_refused():
    with pytest.raises(ValueError, match="timezone"):
        make_id("x", datetime(2026, 1, 1))


def test_bad_prefix_refused():
    with pytest.raises(ValueError):
        make_id("a:b")


def test_suggestion_id_ignores_setup_order():
    a = suggestion_id("EUR_USD", "M15", T, "long", ["s2", "s1"], "r1")
    assert a == suggestion_id("EUR_USD", "M15", T, "long", ["s1", "s2"], "r1")


def test_order_id_is_idempotent_and_rules_sensitive():
    a = order_id("sug:1", "sim", "long", "r1")
    assert a == order_id("sug:1", "sim", "long", "r1")
    assert a != order_id("sug:1", "sim", "long", "r2")
