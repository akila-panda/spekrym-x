import numpy as np
import pytest

from sx_assistant.ta.common import to_frame
from sx_assistant.ta.smc_adapter import smc, smc_setups
from sx_core.clock import available_at
from sx_core.contracts import Setup, setup_id
from sx_core.contracts.setup import Geometry, Source


def stamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_labelled_day_matches_hand_derived_setups(day, day_expected):
    """The labels in labelled_day_expected.json were worked out by hand before any run."""
    from sx_assistant.ta.sessions import session_setups

    got = sorted(smc_setups(day, swing_length=2) + session_setups(day),
                 key=lambda s: (s.known_at, s.kind, s.direction, s.event_time))
    want = sorted(day_expected, key=lambda e: (e["known"], e["kind"], e["direction"], e["event"]))
    assert [(s.kind, s.direction, stamp(s.event_time), stamp(s.known_at)) for s in got] == [
        (e["kind"], e["direction"], e["event"], e["known"]) for e in want]
    for s, e in zip(got, want, strict=True):
        assert s.geometry.price_low == pytest.approx(e["low"])
        assert s.geometry.price_high == pytest.approx(e["high"])
        assert s.status == "causal" and s.lifecycle == "fresh"


def test_bos_is_known_only_after_the_next_swing_is_confirmed(day):
    bos = next(s for s in smc_setups(day, swing_length=2) if s.kind == "bos")
    break_close = available_at(bos.event_time, "M15")          # bar 20 closes at 05:15
    assert bos.known_at > break_close                           # library needs swing 22 first
    assert (bos.geometry.t_start.hour, bos.geometry.t_start.minute) == (2, 45)   # swing 11
    assert bos.geometry.t_end == bos.event_time


def test_every_setup_validates_and_round_trips(day):
    for s in smc_setups(day, swing_length=2):
        assert Setup.model_validate(s.to_wire()) == s
        assert s.source.library == "smartmoneyconcepts" and s.source.version == "0.0.27"
        assert s.plain_text and s.invalidation


def test_liquidity_sweep_of_equal_highs(liq):
    sweeps = [s for s in smc_setups(liq["candles"], swing_length=2) if s.kind == "liquidity_sweep"]
    assert len(sweeps) == 1
    s, e = sweeps[0], liq["expected"]
    assert (stamp(s.event_time), stamp(s.known_at)) == (e["event"], e["known"])
    assert s.geometry.price_low == s.geometry.price_high == pytest.approx(e["level"])
    assert s.direction == "neutral" and "does not predict" in s.invalidation


def test_forced_edge_swings_are_never_emitted(day):
    raw = smc.swing_highs_lows(to_frame(day), swing_length=2)["HighLow"].to_numpy()
    assert not np.isnan(raw[0]) and not np.isnan(raw[-1])       # the library forces both
    swings = [s for s in smc_setups(day, swing_length=2) if s.kind == "swing"]
    assert day[0].time not in {s.event_time for s in swings}
    assert day[-1].time not in {s.event_time for s in swings}


def test_a_swing_needs_its_right_side_before_it_is_known(day):
    first = next(s for s in smc_setups(day, swing_length=2) if s.kind == "swing")
    assert first.known_at == available_at(first.event_time, "M15") + 2 * (
        day[1].time - day[0].time)


def test_naive_one_shot_library_use_is_caught_by_the_harness(day, check_prefix_equality):
    """Why the replay wrapper exists: stamping library swings at the swing bar leaks."""
    def naive(cs):
        sw = smc.swing_highs_lows(to_frame(cs), swing_length=2)
        out = []
        for i in np.flatnonzero(~np.isnan(sw["HighLow"].to_numpy())):
            c = cs[i]
            hl = str(int(sw["HighLow"][i]))
            sid = setup_id("swing", c.instrument, c.tf, "neutral", c.time, hl)
            out.append(Setup(
                id=sid,
                kind="swing", instrument=c.instrument, tf=c.tf, direction="neutral",
                geometry=Geometry(price_low=float(sw["Level"][i]), price_high=float(sw["Level"][i]),
                                  t_start=c.time), event_time=c.time,
                known_at=available_at(c.time, c.tf), lifecycle="fresh",
                source=Source(library="smartmoneyconcepts", version="0.0.27", adapter="naive"),
                plain_text="x", invalidation="x", status="causal"))
        return out
    assert check_prefix_equality(naive, day)          # non-empty list = violations found


def test_adapter_is_causal_on_the_labelled_day(assert_causal, day):
    assert_causal(lambda cs: smc_setups(cs, swing_length=2), day)


def test_adapter_is_causal_on_random_looking_data(assert_causal, m15_candles):
    assert_causal(lambda cs: smc_setups(cs, swing_length=3), m15_candles[:40])


def test_adapter_is_causal_on_the_liquidity_day(assert_causal, liq):
    assert_causal(lambda cs: smc_setups(cs, swing_length=2), liq["candles"])


def test_ids_survive_a_parallel_price_shift(day):
    shifted = [c.model_copy(update={k: getattr(c, k) + 0.001
                                    for k in ("open", "high", "low", "close")}) for c in day]
    a, b = smc_setups(day, swing_length=2), smc_setups(shifted, swing_length=2)
    assert {s.id for s in a} == {s.id for s in b}
    assert a[0].geometry.price_low != b[0].geometry.price_low


def test_bad_parameters_and_inputs(day):
    with pytest.raises(ValueError, match="swing_length"):
        smc_setups(day, swing_length=0)
    with pytest.raises(ValueError, match="empty"):
        smc_setups([])
    with pytest.raises(ValueError, match="complete"):
        smc_setups([day[0].model_copy(update={"complete": False})])
    assert smc_setups(day[:3], swing_length=2) == []            # too short for any structure
