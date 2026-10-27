"""Phase 6B: gates on every order, frozen rules, runner refusals, determinism."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from sx_assistant.paper.broker import OrderRequest, Quote
from sx_assistant.paper.replay import replay
from sx_assistant.paper.runner import PaperRunner
from sx_assistant.rules.ruleset import RulesError, freeze, load_rules, rules_hash, verify_frozen
from sx_core.config import TradingModeError
from sx_core.ledger import Ledger

ROOT = Path(__file__).parents[2]
SHIPPED = ROOT / "assistant/src/sx_assistant/rules/frozen/paper_v1.json"
FIX = json.loads((ROOT / "tests/fixtures/paper/scripted_day.json").read_text())
ENV = {"SX_TRADING_MODE": "paper"}
BASE = {"version": "t1", "max_open_trades": 2, "daily_loss_limit": 100.0, "blackouts": []}


def _t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _rules(tmp_path, name="r.json", **over):
    p = tmp_path / name
    p.write_text(json.dumps({**BASE, **over}))
    freeze(p)
    return p


def _req(r):
    return OrderRequest(r["suggestion_id"], r["side"], r["units"], r["entry"], r["stop"],
                        r["target"], "ignored")


def _day(runner):
    quotes = [Quote(_t(q["time"]), q["bid"], q["ask"]) for q in FIX["quotes"]]
    sched = {}
    for r in FIX["requests"]:
        sched.setdefault(r["submit_index"], []).append(_req(r))
    replay(runner, quotes, sched)
    return {o.suggestion_id: o for o in runner.orders()}


def test_shipped_rules_match_their_lock():
    rules, h = verify_frozen(SHIPPED)
    assert rules.version == "paper-v1" and rules_hash(rules) == h


def test_scripted_day_with_cap_two(tmp_path):
    by = _day(PaperRunner(_rules(tmp_path), env=ENV))
    assert by["sug:A"].state == "closed" and by["sug:A"].pnl == pytest.approx(14.8)
    assert by["sug:C"].state == "pending"
    assert by["sug:D"].state == "rejected"  # third open order at index 0
    assert by["sug:B"].state == "rejected"  # A and C still count at index 4


def test_scripted_day_with_wide_cap_matches_6a_results(tmp_path):
    by = _day(PaperRunner(_rules(tmp_path, max_open_trades=10), env=ENV))
    assert [by["sug:" + n].pnl for n in "ABD"] == pytest.approx([14.8, 9.9, -8.4])


def test_gated_replay_twice_is_identical(tmp_path):
    p = _rules(tmp_path)
    a, b = PaperRunner(p, env=ENV), PaperRunner(p, env=ENV)
    _day(a)
    _day(b)
    assert [o.to_wire() for o in a.orders()] == [o.to_wire() for o in b.orders()]


def test_daily_loss_halt_then_next_day_ok(tmp_path):
    r = PaperRunner(_rules(tmp_path, daily_loss_limit=10.0), env=ENV)
    long = OrderRequest("s1", "long", 10000, 1.0850, 1.0840, 1.0900, "x")
    r.submit(long, Quote(datetime(2026, 10, 26, 7, tzinfo=UTC), 1.0849, 1.0850))
    q1 = Quote(datetime(2026, 10, 26, 7, 15, tzinfo=UTC), 1.0838, 1.0839)
    r.on_quote(q1)  # stop at 1.08378 -> pnl -12.4
    nxt = OrderRequest("s2", "long", 1000, 1.0839, 1.0830, 1.0900, "x")
    assert r.submit(nxt, q1).state == "rejected"
    q2 = Quote(datetime(2026, 10, 27, 7, tzinfo=UTC), 1.0838, 1.0839)
    assert r.submit(OrderRequest("s3", "long", 1000, 1.0839, 1.0830, 1.0900, "x"),
                    q2).state != "rejected"  # new UTC day, loss no longer counts


def test_news_blackout_rejects_inside_window_only(tmp_path):
    bo = [{"label": "NFP", "start": "2026-10-26T12:00:00Z", "end": "2026-10-26T14:00:00Z"}]
    r = PaperRunner(_rules(tmp_path, blackouts=bo), env=ENV)
    req = OrderRequest("s", "long", 1000, 1.0800, 1.0790, 1.0900, "x")
    inside = Quote(datetime(2026, 10, 26, 12, 30, tzinfo=UTC), 1.0849, 1.0850)
    assert r.submit(req, inside).state == "rejected"
    after = Quote(datetime(2026, 10, 26, 14, tzinfo=UTC), 1.0849, 1.0850)  # end is exclusive
    assert r.submit(OrderRequest("s9", "long", 1000, 1.0800, 1.0790, 1.0900, "x"),
                    after).state == "pending"


def test_runner_stamps_rules_version_and_logs_ledger(tmp_path):
    ledger = Ledger(tmp_path / "l.jsonl")
    r = PaperRunner(_rules(tmp_path), ledger=ledger, data_version="fx1", env=ENV)
    o = r.submit(OrderRequest("s", "long", 1000, 1.0800, 1.0790, 1.0900, "caller-value"),
                 Quote(datetime(2026, 10, 26, 7, tzinfo=UTC), 1.0849, 1.0850))
    assert o.rules_version == r.rules_version != "caller-value"
    assert r.rules_version.startswith("t1-") and ledger.verify() == 2
    kinds = [e.kind for e in ledger.read()]
    assert kinds == ["run_started", "order_submitted"]
    assert ledger.read()[1].rules_version == r.rules_version


def test_kill_switch_through_runner(tmp_path):
    r = PaperRunner(_rules(tmp_path), env=ENV)
    r.kill("test")
    o = r.submit(OrderRequest("s", "long", 1000, 1.0800, 1.0790, 1.0900, "x"),
                 Quote(datetime(2026, 10, 26, 7, tzinfo=UTC), 1.0849, 1.0850))
    assert o.state == "rejected"


def test_changed_rules_are_refused(tmp_path):
    p = _rules(tmp_path)
    p.write_text(json.dumps({**BASE, "max_open_trades": 9}))
    with pytest.raises(RulesError, match="changed"):
        PaperRunner(p, env=ENV)


def test_unfrozen_rules_are_refused(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps(BASE))
    with pytest.raises(RulesError, match="not frozen"):
        PaperRunner(p, env=ENV)


def test_whitespace_does_not_change_hash_but_values_do(tmp_path):
    p = _rules(tmp_path)
    p.write_text(json.dumps({**BASE}, indent=4))
    verify_frozen(p)  # same content, different layout: still fine
    h = rules_hash(load_rules(p))
    p2 = tmp_path / "r2.json"
    p2.write_text(json.dumps({**BASE, "daily_loss_limit": 100.5}))
    assert rules_hash(load_rules(p2)) != h


def test_freeze_will_not_overwrite_a_different_lock(tmp_path):
    p = _rules(tmp_path)
    p.write_text(json.dumps({**BASE, "max_open_trades": 3}))
    with pytest.raises(RulesError, match="new version"):
        freeze(p)


def test_invalid_rules_rejected(tmp_path):
    for bad in ({"max_open_trades": 0}, {"daily_loss_limit": 0}, {"surprise": 1},
                {"blackouts": [{"label": "x", "start": "2026-10-26T12:00:00Z",
                                "end": "2026-10-26T11:00:00Z"}]}):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({**BASE, **bad}))
        with pytest.raises(RulesError):
            load_rules(p)


def test_live_mode_refused_by_runner(tmp_path):
    p = _rules(tmp_path)
    for env in ({"SX_TRADING_MODE": "live"}, {}, {"SX_TRADING_MODE": "paper",
                                                   "OANDA_ENV": "live"}):
        with pytest.raises(TradingModeError):
            PaperRunner(p, env=env)
