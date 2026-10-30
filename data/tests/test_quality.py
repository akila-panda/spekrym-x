from datetime import UTC, datetime, timedelta

import pytest

from sx_core.storage import candles_to_frame
from sx_data.quality import GapRules, check_quality
from sx_data.resample import resample


def frame(cs):
    return candles_to_frame(cs)


def test_clean_fixture_has_only_tolerated_quiet_minutes(m1_closed):
    r = check_quality(frame(m1_closed), "M1")
    assert (r.duplicates, r.out_of_order, r.off_grid, r.crossed_quotes, r.incomplete) == (0,) * 5
    assert [g.missing_bars for g in r.unexpected_gaps] == [2, 2, 1] and r.expected_gaps == ()
    assert not r.feed_degraded and r.reasons == ()


def test_weekend_gap_is_expected_not_degraded(h1_week):
    r = check_quality(frame(h1_week), "H1")
    assert len(r.expected_gaps) == 1 and r.unexpected_gaps == ()
    g = r.expected_gaps[0]
    assert (g.after, g.before) == (datetime(2026, 10, 23, 20, tzinfo=UTC),
                                   datetime(2026, 10, 25, 22, tzinfo=UTC))
    assert not r.feed_degraded


def test_midweek_gap_longer_than_tolerance_degrades_feed(h1_week):
    cs = [c for c in h1_week if not (datetime(2026, 10, 22, 10, tzinfo=UTC) <= c.time
                                     < datetime(2026, 10, 22, 16, tzinfo=UTC))]
    r = check_quality(frame(cs), "H1")
    assert r.unexpected_gaps[0].missing_bars == 6
    assert r.feed_degraded and "unexpected gap" in r.reasons[0]


def test_gap_tolerance_is_configurable(h1_week):
    cs = [c for c in h1_week if c.time != datetime(2026, 10, 22, 10, tzinfo=UTC)
          and c.time != datetime(2026, 10, 22, 11, tzinfo=UTC)]
    assert not check_quality(frame(cs), "H1").feed_degraded  # 2 missing <= default 3
    assert check_quality(frame(cs), "H1", rules=GapRules(max_gap_bars=1)).feed_degraded


def test_duplicates_disorder_off_grid_crossed_and_incomplete_are_each_reported(m1_all):
    base = list(m1_all[:10])
    dup = frame(base + [base[3]])
    assert check_quality(dup, "M1").duplicates == 1 and check_quality(dup, "M1").feed_degraded
    order = frame([base[1], base[0], *base[2:]])
    assert check_quality(order, "M1").out_of_order == 1
    off = frame([base[0].model_copy(update={"time": base[0].time + timedelta(seconds=7)})])
    assert check_quality(off, "M1").off_grid == 1
    cross = frame([base[0].model_copy(update={"bid_close": 1.2, "ask_close": 1.1})])
    assert check_quality(cross, "M1").crossed_quotes == 1
    inc = check_quality(frame(m1_all), "M1")  # the fixture ends with a forming bar
    assert inc.incomplete == 1 and inc.feed_degraded


def test_missing_quotes_are_not_counted_as_crossed(m1_closed):
    cs = [c.model_copy(update={"bid_close": None, "ask_close": None}) for c in m1_closed[:5]]
    assert check_quality(frame(cs), "M1").crossed_quotes == 0


def test_stale_feed_only_when_market_should_be_open(m1_closed):
    last_close = datetime(2026, 10, 19, 8, 59, tzinfo=UTC) + timedelta(minutes=1)
    df = frame(m1_closed)
    assert not check_quality(df, "M1", now=last_close + timedelta(minutes=2)).stale
    assert check_quality(df, "M1", now=last_close + timedelta(minutes=10)).stale
    saturday = datetime(2026, 10, 24, 12, tzinfo=UTC)
    assert not check_quality(df, "M1", now=saturday).stale  # inside the weekly closure window


def test_empty_frame_is_degraded(m1_closed):
    r = check_quality(frame(m1_closed).iloc[0:0], "M1")
    assert r.n_bars == 0 and r.feed_degraded and r.reasons == ("no bars",)


def test_does_not_mutate_input(m1_closed):
    df = frame(m1_closed)
    before = df.copy()
    check_quality(df, "M1", now=datetime(2026, 10, 19, 9, 5, tzinfo=UTC))
    assert df.equals(before)


def test_resampled_bars_pass_their_own_grid_check(m1_closed):
    for tf in ("M15", "H1"):
        r = check_quality(frame(resample(m1_closed, tf)), tf)
        assert r.off_grid == 0 and not r.feed_degraded


@pytest.mark.parametrize("tf", ["H4", "D"])
def test_week_fixture_resamples_onto_the_utc_grid(h1_week, tf):
    r = check_quality(frame(resample(h1_week, tf)), tf)
    assert r.off_grid == 0 and r.duplicates == 0


def test_daily_bars_weekend_gap_is_expected_too(h1_week):
    r = check_quality(frame(resample(h1_week, "D")), "D")
    assert len(r.expected_gaps) == 1 and r.unexpected_gaps == ()  # Sat is the missing day


def _hourly(*spans):
    import pandas as pd
    times = [t for a, b in spans for t in pd.date_range(a, b, freq="h", tz="UTC")]
    return pd.DataFrame({"time": times, "bid_close": 1.0, "ask_close": 1.1, "complete": True})


def test_christmas_and_new_year_closures_are_expected_gaps():
    f = _hourly(("2025-12-22 00:00", "2025-12-24 21:00"), ("2025-12-25 22:00", "2025-12-26 10:00"))
    r = check_quality(f, "H1")
    assert len(r.expected_gaps) == 1 and r.unexpected_gaps == () and not r.feed_degraded
    f = _hourly(("2025-12-29 00:00", "2025-12-31 21:00"), ("2026-01-01 22:00", "2026-01-02 10:00"))
    assert not check_quality(f, "H1").feed_degraded


def test_other_long_gaps_and_the_switch_stay_unexpected():
    f = _hourly(("2026-03-02 00:00", "2026-03-03 21:00"), ("2026-03-04 22:00", "2026-03-05 10:00"))
    assert check_quality(f, "H1").feed_degraded
    f = _hourly(("2025-12-22 00:00", "2025-12-24 21:00"), ("2025-12-25 22:00", "2025-12-26 10:00"))
    assert check_quality(f, "H1", rules=GapRules(holiday_closures=False)).feed_degraded
