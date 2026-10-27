"""Resample tests. Expected values come from a plain-Python oracle written independently of
the pandas implementation, plus hand-checked boundary cases on the frozen fixtures."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

import pytest

from sx_core.clock import TF_SECONDS, bar_close
from sx_data.errors import ResampleError
from sx_data.resample import resample


def oracle(cs, to_tf, as_of):
    secs = TF_SECONDS[to_tf]
    buckets = defaultdict(list)
    for c in cs:
        if c.complete:
            ts = int(c.time.timestamp())
            buckets[ts - ts % secs].append(c)
    out = []
    for start in sorted(buckets):
        if datetime.fromtimestamp(start + secs, UTC) > as_of:
            continue
        g = buckets[start]
        out.append((datetime.fromtimestamp(start, UTC), g[0].open, max(c.high for c in g),
                    min(c.low for c in g), g[-1].close, sum(c.volume for c in g),
                    g[-1].bid_close, g[-1].ask_close))
    return out


def tup(c):
    return (c.time, c.open, c.high, c.low, c.close, c.volume, c.bid_close, c.ask_close)


@pytest.mark.parametrize("to_tf", ["M5", "M15", "H1"])
def test_m1_matches_oracle(m1_closed, to_tf):
    as_of = bar_close(m1_closed[-1].time, "M1")
    assert [tup(c) for c in resample(m1_closed, to_tf)] == oracle(m1_closed, to_tf, as_of)


def test_incomplete_source_bar_is_dropped_and_forming_bucket_not_returned(m1_all):
    out = resample(m1_all, "M15")  # last source bar (09:00) is incomplete
    assert out[-1].time == datetime(2026, 10, 19, 8, 45, tzinfo=UTC)
    assert all(c.complete and c.tf == "M15" for c in out)


def test_explicit_as_of_hides_buckets_that_have_not_closed(m1_closed):
    as_of = datetime(2026, 10, 19, 7, 10, tzinfo=UTC)
    out = resample(m1_closed, "H1", as_of)
    assert [c.time.hour for c in out] == [6]  # 07:00-08:00 is still forming at 07:10
    # the 06:45 bucket closed at 07:00; the 07:00 bucket closes at 07:15, after as_of
    assert resample(m1_closed, "M15", as_of)[-1].time == datetime(2026, 10, 19, 6, 45, tzinfo=UTC)


def test_quiet_minutes_are_not_filled_with_fake_bars(m1_closed):
    # minutes 17 and 18 after 06:00 have no source bar; the 06:15 bucket has 13 of 15
    b = next(c for c in resample(m1_closed, "M15") if c.time.minute == 15 and c.time.hour == 6)
    members = [c for c in m1_closed if b.time <= c.time < b.time + timedelta(minutes=15)]
    assert len(members) == 13
    assert b.volume == sum(c.volume for c in members)


def test_ohlc_bid_ask_come_from_first_extremes_and_last(m1_closed):
    b = resample(m1_closed, "H1")[0]
    members = [c for c in m1_closed if c.time.hour == 6]
    assert b.open == members[0].open and b.close == members[-1].close
    assert b.high == max(c.high for c in members) and b.low == min(c.low for c in members)
    assert b.bid_close == members[-1].bid_close and b.ask_close == members[-1].ask_close


def test_missing_quote_on_last_bar_gives_none_not_an_older_quote(m1_closed):
    cs = [c for c in m1_closed if c.time < datetime(2026, 10, 19, 7, 0, tzinfo=UTC)]
    cs[-1] = cs[-1].model_copy(update={"bid_close": None, "ask_close": None})
    b = resample(cs, "M5")[-1]
    assert b.time == datetime(2026, 10, 19, 6, 55, tzinfo=UTC)
    assert b.bid_close is None and b.ask_close is None


def test_daily_bars_open_at_00_utc_and_weekend_is_not_filled(h1_week):
    daily = resample(h1_week, "D")
    assert [c.time for c in daily] == [
        datetime(2026, 10, 22, tzinfo=UTC), datetime(2026, 10, 23, tzinfo=UTC),
        datetime(2026, 10, 25, tzinfo=UTC)]  # no Saturday; Monday is still forming
    thu = daily[0]
    members = [c for c in h1_week if c.time.date() == thu.time.date()]
    assert len(members) == 24 and thu.volume == sum(c.volume for c in members)
    sunday = daily[2]
    assert sunday.volume == sum(c.volume for c in h1_week if c.time.day == 25)  # 22:00, 23:00 only


def test_h4_buckets_are_00_04_08_12_16_20_utc(h1_week):
    h4 = resample(h1_week, "H4")
    assert {c.time.hour for c in h4} == {0, 4, 8, 12, 16, 20}
    assert [tup(c) for c in h4] == oracle(h1_week, "H4", bar_close(h1_week[-1].time, "H1"))
    # Monday 04:00-08:00 has bars at 04 and 05 only and is not closed at 06:00 -> absent
    assert datetime(2026, 10, 26, 4, tzinfo=UTC) not in [c.time for c in h4]
    assert datetime(2026, 10, 26, 0, tzinfo=UTC) in [c.time for c in h4]


def test_input_is_not_mutated_and_result_is_stable(m1_closed):
    before = list(m1_closed)
    assert resample(m1_closed, "M15") == resample(m1_closed, "M15")
    assert m1_closed == before


def test_dirty_or_impossible_input_is_refused(m1_closed, h1_week):
    with pytest.raises(ResampleError):
        resample([], "M15")
    with pytest.raises(ResampleError, match="duplicate"):
        resample(m1_closed[:3] + m1_closed[2:4], "M5")
    with pytest.raises(ResampleError, match="order"):
        resample([m1_closed[1], m1_closed[0]], "M5")
    with pytest.raises(ResampleError, match="cannot resample"):
        resample(h1_week, "M15")
    with pytest.raises(ResampleError, match="cannot resample"):
        resample(h1_week, "H1")
    with pytest.raises(ResampleError, match="single"):
        resample([m1_closed[0], h1_week[0]], "H4")
    with pytest.raises(ResampleError):
        resample(m1_closed[:5], "M3")  # type: ignore[arg-type]


def test_resampling_is_causal(assert_causal, m1_closed, h1_week):
    """Prefix equality (Phase 2 harness): a bar known at t is identical on prefix and full run."""
    def producer(tf):
        def run(cs):
            return [{"id": f"{tf}:{b.time.isoformat()}", "event_time": b.time,
                     "known_at": bar_close(b.time, tf), "bar": b.model_dump()}
                    for b in resample(cs, tf)] if len(cs) else []
        return run

    assert_causal(producer("M15"), m1_closed[:120])
    assert_causal(producer("H4"), h1_week)
    assert_causal(producer("D"), h1_week)


def test_a_forward_looking_resampler_is_caught_by_the_harness(check_prefix_equality, h1_week):
    """Negative control: emitting the still-forming bucket (as_of far in the future) must fail."""
    far = datetime(2100, 1, 1, tzinfo=UTC)

    def leaky(cs):
        return [{"id": b.time.isoformat(), "event_time": b.time, "known_at": b.time,
                 "bar": b.model_dump()} for b in resample(cs, "D", as_of=far)]

    assert check_prefix_equality(leaky, h1_week)


def test_incomplete_source_bar_never_counts_even_when_its_bucket_has_ended(m1_all):
    late = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)  # long after the 09:00 bucket would end
    out = resample(m1_all, "M15", late)
    assert out[-1].time == datetime(2026, 10, 19, 8, 45, tzinfo=UTC)  # no bucket from 09:00
    mid = list(m1_all[:30])
    mid[10] = mid[10].model_copy(update={"complete": False})
    b = resample(mid, "M15", late)
    assert sum(c.volume for c in b) == sum(c.volume for c in mid if c.complete)
