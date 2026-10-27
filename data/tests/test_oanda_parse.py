from datetime import UTC, datetime

import pytest

from sx_data.errors import ParseError
from sx_data.oanda_parse import parse_candle, parse_candles, parse_oanda_time


def test_nanosecond_time_is_truncated_and_utc():
    t = parse_oanda_time("2026-10-19T06:01:00.123456789Z")
    assert t == datetime(2026, 10, 19, 6, 1, 0, 123456, tzinfo=UTC)
    assert parse_oanda_time("2026-10-19T06:01:00Z").microsecond == 0


@pytest.mark.parametrize("bad", ["2026-10-19 06:01:00", "2026-10-19T06:01:00+01:00", "x"])
def test_bad_time_is_rejected(bad):
    with pytest.raises(ParseError):
        parse_oanda_time(bad)


def test_fixture_parses_with_bid_ask_and_incomplete_last(m1_all):
    assert len(m1_all) == 176  # 181 minutes minus 5 quiet minutes
    assert m1_all[-1].complete is False and all(c.complete for c in m1_all[:-1])
    first = m1_all[0]
    assert (first.instrument, first.tf) == ("EUR_USD", "M1")
    assert first.bid_close is not None and first.ask_close is not None
    assert first.bid_close < first.close < first.ask_close  # mid sits between bid and ask


def test_ohlc_comes_from_mid(m1_payload):
    raw = m1_payload["candles"][3]
    c = parse_candle(raw, "EUR_USD", "M1")
    assert (c.open, c.high, c.low, c.close) == tuple(float(raw["mid"][k]) for k in "ohlc")
    assert c.bid_close == float(raw["bid"]["c"]) and c.ask_close == float(raw["ask"]["c"])


def test_missing_field_and_bad_shapes_raise_parse_error(m1_payload):
    raw = dict(m1_payload["candles"][0])
    del raw["ask"]
    with pytest.raises(ParseError):
        parse_candle(raw, "EUR_USD", "M1")
    with pytest.raises(ParseError):
        parse_candles({"candles": "nope"}, "EUR_USD", "M1")
    with pytest.raises(ParseError):
        parse_candle({**m1_payload["candles"][0], "complete": "yes"}, "EUR_USD", "M1")


def test_inconsistent_ohlc_is_a_parse_error(m1_payload):
    raw = {**m1_payload["candles"][0], "mid": {"o": "1.1", "h": "1.0", "l": "0.9", "c": "1.0"}}
    with pytest.raises(ParseError):
        parse_candle(raw, "EUR_USD", "M1")
