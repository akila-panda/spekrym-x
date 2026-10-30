"""Phase 9C-2: persisted provider state, daily cap, brief reuse, routing log (fake providers)."""

import json
import threading

from analyst_helpers import sample_packet

from sx_assistant.analyst.config import ProviderSetup
from sx_assistant.analyst.errors import AuthError, RateLimited, Transient
from sx_assistant.analyst.providers.fake import FakeProvider, echo_reply
from sx_assistant.analyst.router import Router
from sx_assistant.analyst.service import AnalystService
from sx_assistant.analyst.state import MemoryState, SqliteState

P = sample_packet()
GOOD = echo_reply(P)
DAY = 86_400.0


class Clock:
    def __init__(self, t=1_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def route(providers, state, clock, caps=None):
    r = Router(providers, state=state, clock=clock, daily_caps=caps)
    return r.run("s", "u", lambda text: text)


def test_cooldown_survives_a_restart(tmp_path):
    clock, db = Clock(), tmp_path / "state.db"
    a = FakeProvider("a", [RateLimited("x", retry_after=300.0)])
    route([a], SqliteState(db), clock)
    a2 = FakeProvider("a", [GOOD])                       # "restart": new objects, same file
    r = route([a2], SqliteState(db), clock)
    assert r.status == "deferred" and not a2.calls
    assert r.attempts[0].detail == "cooling down"
    clock.t += 301
    assert route([a2], SqliteState(db), clock).status == "ok"


def test_counters_include_timeouts_and_tokens(tmp_path):
    st, clock = SqliteState(tmp_path / "s.db"), Clock()
    route([FakeProvider("a", [Transient("timeout")])], st, clock)
    clock.t += 60
    route([FakeProvider("a", ["ok"])], st, clock)
    row = st.load("a", "fake")
    assert row.requests_today == 2 and row.tokens_today == 150
    assert row.last_error is None and row.health(clock.t) == "healthy"


def test_daily_cap_skips_before_any_call_and_rolls_over(tmp_path):
    st, clock = SqliteState(tmp_path / "s.db"), Clock()
    a = FakeProvider("a", ["1", "2", "3"])
    for _ in range(2):
        assert route([a], st, clock, {"a": 2}).status == "ok"
    r = route([a], st, clock, {"a": 2})
    assert r.status == "deferred" and len(a.calls) == 2 and "daily cap" in r.attempts[0].detail
    clock.t += DAY
    assert route([a], st, clock, {"a": 2}).status == "ok"
    assert st.load("a", "fake").requests_today == 1


def test_cap_fails_over_to_the_next_provider():
    st, clock = MemoryState(), Clock()
    a, b = FakeProvider("a", ["x"]), FakeProvider("b", ["y"])
    assert route([a, b], st, clock, {"a": 1}).provider == "a"
    assert route([a, b], st, clock, {"a": 1}).provider == "b"


def test_auth_disable_persists_until_the_key_changes_or_reset(tmp_path):
    st, clock = SqliteState(tmp_path / "s.db"), Clock()
    route([FakeProvider("a", [AuthError("no")])], st, clock)
    assert st.load("a", "fake").health(clock.t) == "disabled"
    same = FakeProvider("a", ["ok"])
    assert route([same], st, clock).status == "deferred" and not same.calls
    new_key = FakeProvider("a", ["ok"])
    new_key.key_fingerprint = "rotated"
    assert route([new_key], st, clock).status == "ok"          # rotated key clears it
    route([FakeProvider("a", [AuthError("no")])], st, clock)
    assert st.reset("a") >= 1 and st.load("a", "fake").disabled_reason is None


def test_health_values():
    from sx_assistant.analyst.state import ProviderState
    s = ProviderState("a", "m")
    assert s.health(10) == "unknown"
    s.last_error = "transient"
    assert s.health(10) == "degraded"
    s.cooldown_until = 20
    assert s.health(10) == "cooling_down"


def factory(provider, caps=None, confirmed=True):
    from sx_assistant.analyst.config import ApprovalError

    def make(require_confirmed):
        if require_confirmed and not confirmed:
            raise ApprovalError("not confirmed free")
        return ProviderSetup([provider] if provider else [], {}, caps or {})
    return make


def test_saved_brief_is_reused_without_calling_and_force_calls_again(tmp_path):
    p = FakeProvider("a", [GOOD, GOOD])
    svc = AnalystService(tmp_path, factory(p), Clock())
    first = svc.generate(P)
    again = svc.generate(P)
    forced = svc.generate(P, force=True)
    assert first["status"] == "published" and first["reused"] is False
    assert again["reused"] is True and again["brief"] == first["brief"]
    assert forced["reused"] is False and len(p.calls) == 2
    assert svc.latest()["brief"]["packet_hash"] == P.hash()


def test_unavailable_when_unconfirmed_or_no_provider(tmp_path):
    p = FakeProvider("a", [GOOD])
    r = AnalystService(tmp_path / "x", factory(p, confirmed=False), Clock()).generate(P)
    assert r["status"] == "unavailable" and "not confirmed" in r["reason"] and not p.calls
    r2 = AnalystService(tmp_path / "y", factory(None), Clock()).generate(P)
    assert r2["status"] == "unavailable"


def test_deferred_writes_nothing_and_logs_the_failover_trail(tmp_path):
    a = FakeProvider("a", [RateLimited("x")])
    b = FakeProvider("b", [Transient("x")])
    svc = AnalystService(tmp_path, lambda c: ProviderSetup([a, b], {}, {}), Clock())
    r = svc.generate(P)
    assert r["status"] == "deferred" and svc.latest() is None
    lines = [json.loads(x) for x in (tmp_path / "routing.jsonl").read_text().splitlines()]
    assert [x["outcome"] for x in lines] == ["rate_limited", "transient"]
    assert len({x["route_id"] for x in lines}) == 1 and [x["seq"] for x in lines] == [0, 1]
    assert "Evidence packet" not in json.dumps(lines)


def test_second_request_during_generation_is_busy_not_duplicated(tmp_path):
    gate, started = threading.Event(), threading.Event()

    class Slow(FakeProvider):
        def complete(self, system, user):
            started.set()
            gate.wait(5)
            return super().complete(system, user)

    p = Slow("a", [GOOD])
    svc = AnalystService(tmp_path, factory(p), Clock())
    out = {}
    t = threading.Thread(target=lambda: out.update(svc.generate(P)))
    t.start()
    assert started.wait(5)
    assert svc.generate(P)["status"] == "busy"
    gate.set()
    t.join()
    assert out["status"] == "published" and len(p.calls) == 1


def test_status_makes_no_call_and_exposes_no_secrets(tmp_path):
    p = FakeProvider("a", [GOOD])
    svc = AnalystService(tmp_path, factory(p, {"a": 50}), Clock())
    svc.generate(P)
    st = svc.status()
    row = st["providers"][0]
    assert len(p.calls) == 1 and row["requests_today_estimate"] == 1 and row["daily_cap"] == 50
    assert row["health"] == "healthy" and "fake" not in json.dumps(st).replace('"fake"', "")
    assert "key_fp" not in json.dumps(st) and "key_fingerprint" not in json.dumps(st)


def test_old_layout_and_fake_briefs_are_not_reused(tmp_path):
    """A 9C-1 file (no 'brief' key) or a fake-provider brief must not stand in for a real one."""
    old = tmp_path / f"brief_{P.hash()}.json"
    old.write_text('{"kind": "analyst_brief"}')
    p = FakeProvider("a", [GOOD])
    svc = AnalystService(tmp_path, factory(p), Clock())
    assert svc.latest() is None
    r = svc.generate(P)
    assert r["status"] == "published" and r["reused"] is False and len(p.calls) == 1
    fake_file = svc.dir / f"brief_{P.hash()}.json"
    data = json.loads(fake_file.read_text())
    data["brief"]["writer"]["provider"] = "fake"
    fake_file.write_text(json.dumps(data))
    assert svc.latest() is None
