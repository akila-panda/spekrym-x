from datetime import timedelta

import pytest

from sx_assistant.ta.causal_wrapper import replay_first_seen
from sx_assistant.ta.common import check_series, fmt_price, to_frame
from sx_core.clock import available_at


def test_check_series_rejects_bad_input(day):
    with pytest.raises(ValueError, match="empty"):
        check_series([])
    with pytest.raises(ValueError, match="single instrument"):
        check_series([day[0], day[1].model_copy(update={"tf": "H1"})])
    with pytest.raises(ValueError, match="complete"):
        check_series([day[0], day[1].model_copy(update={"complete": False})])
    with pytest.raises(ValueError, match="increasing"):
        check_series([day[1], day[0]])
    with pytest.raises(ValueError, match="increasing"):
        check_series([day[0], day[0]])
    assert check_series(day) == ("EUR_USD", "M15")


def test_to_frame_is_zero_based_float(day):
    df = to_frame(day)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert list(df.index) == list(range(len(day)))
    assert df["high"].iloc[22] == day[22].high


def test_fmt_price():
    assert fmt_price(1.08, "EUR_USD") == "1.08000"
    assert fmt_price(150.1234, "USD_JPY") == "150.123"


def test_replay_freezes_first_sight_and_stamps_bar_close(day):
    calls = []

    def extract(view):
        calls.append(view.k)
        # 'a' appears from prefix 5 on, with a value that keeps changing; 'b' only at 8
        out = [("a", {"v": view.k})] if view.k >= 5 else []
        return out + ([("b", {"v": view.k})] if view.k == 8 else [])

    seen = {s.key: s for s in replay_first_seen(day, extract)}
    assert calls == list(range(1, len(day) + 1))
    assert seen["a"].data == {"v": 5} and seen["a"].first_k == 5
    assert seen["a"].known_at == available_at(day[4].time, "M15")
    assert seen["b"].known_at == available_at(day[7].time, "M15") == day[7].time + timedelta(
        minutes=15)


def test_replay_never_shows_the_extractor_more_than_the_prefix(day):
    def extract(view):
        assert len(view.df) == view.k
        assert view.df["high"].iloc[-1] == day[view.k - 1].high
        return []

    replay_first_seen(day, extract)


def test_replay_min_bars(day):
    ks = []
    replay_first_seen(day, lambda v: ks.append(v.k) or [], min_bars=10)
    assert ks[0] == 10
