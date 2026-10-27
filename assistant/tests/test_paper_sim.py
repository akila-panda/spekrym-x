"""Phase 6A: simulator, kill switch, idempotency, tracker, deterministic replay."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sx_assistant.paper.broker import BrokerError, OrderRequest, Quote
from sx_assistant.paper.orders import KillSwitch, validate_request
from sx_assistant.paper.replay import quotes_from_candles, replay
from sx_assistant.paper.sim_broker import SimBroker
from sx_assistant.paper.tracker import Tracker, summarize
from sx_core.config import TradingModeError
from sx_core.contracts import Candle
from sx_core.ledger import Ledger

ENV = {"SX_TRADING_MODE": "paper"}
FIX = json.loads((Path(__file__).parents[2] / "tests/fixtures/paper/scripted_day.json").read_text())
T0 = datetime(2026, 10, 26, 7, tzinfo=UTC)


def _t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _req(r):
    return OrderRequest(r["suggestion_id"], r["side"], r["units"], r["entry"], r["stop"],
                        r["target"], r["rules_version"])


def _quotes():
    return [Quote(_t(q["time"]), q["bid"], q["ask"]) for q in FIX["quotes"]]


def _run(**kw):
    broker = SimBroker(env=ENV, **kw)
    sched = {}
    for r in FIX["requests"]:
        sched.setdefault(r["submit_index"], []).append(_req(r))
    replay(broker, _quotes(), sched)
    by = {o.suggestion_id: o for o in broker.orders()}
    return broker, by


def test_scripted_day_matches_hand_computed_fixture():
    _, by = _run()
    for name, exp in FIX["expected"].items():
        o = by["sug:" + name]
        assert o.state == exp["state"]
        if exp["state"] == "closed":
            assert o.actual_fill == pytest.approx(exp["actual_fill"])
            assert o.slippage == pytest.approx(exp["slippage"])
            assert o.pnl == pytest.approx(exp["pnl"])
            assert o.closed_at == _t(exp["closed_at"])
        else:
            assert o.actual_fill is None and o.pnl is None


def test_replay_twice_gives_identical_orders():
    a, _ = _run()
    b, _ = _run()
    assert [o.to_wire() for o in a.orders()] == [o.to_wire() for o in b.orders()]


def test_live_mode_is_refused():
    with pytest.raises(TradingModeError):
        SimBroker(env={"SX_TRADING_MODE": "live"})
    with pytest.raises(TradingModeError):
        SimBroker(env={})


def test_resubmit_is_idempotent():
    b = SimBroker(env=ENV)
    q = Quote(T0, 1.0849, 1.0850)
    r = _req(FIX["requests"][0])
    first = b.submit(r, q)
    assert b.submit(r, q) == first
    assert len(b.orders()) == 1


def test_kill_switch_rejects_until_reset():
    ks = KillSwitch()
    b = SimBroker(env=ENV, kill_switch=ks)
    q = Quote(T0, 1.0849, 1.0850)
    ks.trip("manual")
    assert b.submit(_req(FIX["requests"][0]), q).state == "rejected"
    ks.reset()
    other = OrderRequest("sug:other", "long", 1000, 1.0845, 1.0835, 1.086, "rules-test")
    assert b.submit(other, q).state == "pending"


def test_invalid_requests_are_rejected():
    bad = [OrderRequest("s", "long", 0, 1.0, 0.9, 1.1, "r"),
           OrderRequest("s", "long", 1, 1.0, 1.1, 0.9, "r"),
           OrderRequest("s", "short", 1, 1.0, 0.9, 1.1, "r"),
           OrderRequest("s", "long", float("nan"), 1.0, 0.9, 1.1, "r")]
    assert all(validate_request(r) for r in bad)
    assert SimBroker(env=ENV).submit(bad[0], Quote(T0, 1.0849, 1.0850)).state == "rejected"


def test_gate_can_reject_every_order():
    class NoGate:
        name = "no"

        def check(self, req, quote, open_orders):
            return "blocked"

    b = SimBroker(env=ENV, gates=[NoGate()])
    assert b.submit(_req(FIX["requests"][0]), Quote(T0, 1.0849, 1.0850)).state == "rejected"


def test_quotes_must_not_go_back_in_time():
    b = SimBroker(env=ENV)
    b.on_quote(Quote(T0, 1.0849, 1.0850))
    with pytest.raises(BrokerError):
        b.on_quote(Quote(datetime(2026, 10, 26, 6, tzinfo=UTC), 1.0849, 1.0850))


def test_no_exit_on_the_quote_that_filled():
    b = SimBroker(env=ENV)
    r = OrderRequest("s", "long", 1000, 1.0850, 1.0849, 1.0900, "r")
    o = b.submit(r, Quote(T0, 1.0840, 1.0850))  # fills at once; bid is below the stop
    assert o.state == "filled"
    assert b.on_quote(Quote(T0, 1.0840, 1.0850)) == []


def test_cancel_pending_and_close_all():
    b = SimBroker(env=ENV)
    q = Quote(T0, 1.0849, 1.0850)
    p = b.submit(OrderRequest("p", "long", 1000, 1.0800, 1.0790, 1.0900, "r"), q)
    f = b.submit(OrderRequest("f", "long", 1000, 1.0850, 1.0800, 1.0900, "r"), q)
    assert b.cancel(p.id, q).state == "cancelled"
    closed = b.close_all(Quote(datetime(2026, 10, 26, 7, 15, tzinfo=UTC), 1.0860, 1.0861))
    assert [c.id for c in closed] == [f.id] and closed[0].pnl == pytest.approx(
        (1.08598 - 1.08502) * 1000)


def test_tracker_summary_and_ledger(tmp_path):
    ledger = Ledger(tmp_path / "paper.jsonl")
    tr = Tracker(ledger, data_version="sim-fixture")
    _, by = _run(listener=tr.record)
    s = summarize(list(by.values()))
    assert (s.submitted, s.filled, s.closed, s.rejected) == (4, 3, 3, 0)
    assert s.total_pnl == pytest.approx(14.8 + 9.9 - 8.4)
    assert s.mean_slippage == pytest.approx(0.00002)
    assert "Not validated" in s.label
    assert ledger.verify() == len(tr.events) == len(ledger.read())
    assert {e.kind for e in ledger.read()} >= {"order_submitted", "order_filled", "order_closed"}


def test_quotes_from_candles_use_closed_bars_known_at_close():
    c = [Candle(instrument="EUR_USD", tf="M15", time=T0, open=1.08, high=1.09, low=1.07,
                close=1.085, volume=1, bid_close=1.0849, ask_close=1.0851, complete=True),
         Candle(instrument="EUR_USD", tf="M15", time=datetime(2026, 10, 26, 7, 15, tzinfo=UTC),
                open=1.08, high=1.09, low=1.07, close=1.085, volume=1, bid_close=1.0849,
                ask_close=1.0851, complete=False)]
    qs = quotes_from_candles(c)
    assert len(qs) == 1 and qs[0].time == datetime(2026, 10, 26, 7, 15, tzinfo=UTC)
