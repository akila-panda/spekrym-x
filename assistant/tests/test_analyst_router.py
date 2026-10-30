"""Phase 9C-1: routing, failover, repair bounds and the deferred state (fake providers)."""

import json

from analyst_helpers import reply, sample_packet

from sx_assistant.analyst.brief import generate_brief
from sx_assistant.analyst.errors import AuthError, BadRequest, RateLimited, Transient
from sx_assistant.analyst.providers.fake import FakeProvider, echo_reply
from sx_assistant.analyst.router import Router

P = sample_packet()
GOOD = echo_reply(P)
BAD_ID = reply([{"text": "A level exists.", "evidence_ids": ["setup:nope"]}])


class Clock:
    t = 0.0

    def __call__(self):
        return self.t


def test_first_valid_answer_wins_and_others_are_not_called():
    a, b = FakeProvider("a", [GOOD]), FakeProvider("b", [GOOD])
    r = generate_brief(P, Router([a, b]))
    assert r.status == "published" and r.brief.writer.provider == "a"
    assert len(a.calls) == 1 and not b.calls
    assert r.brief.labels == ["Exploratory", "Not validated"]


def test_rate_limit_cools_down_and_fails_over_then_recovers():
    clock = Clock()
    a = FakeProvider("a", [RateLimited("x", retry_after=120.0), GOOD])
    b = FakeProvider("b", [GOOD, GOOD])
    router = Router([a, b], clock=clock)
    assert generate_brief(P, router).brief.writer.provider == "b"
    assert generate_brief(P, router).brief.writer.provider == "b"      # a still cooling
    assert len(a.calls) == 1
    clock.t = 121.0
    assert generate_brief(P, router).brief.writer.provider == "a"


def test_timeout_is_not_retried_on_the_same_provider():
    a, b = FakeProvider("a", [Transient("timeout")]), FakeProvider("b", [GOOD])
    r = generate_brief(P, Router([a, b]))
    assert len(a.calls) == 1 and r.brief.writer.provider == "b"


def test_auth_and_bad_request_disable_the_provider():
    a = FakeProvider("a", [AuthError("no"), GOOD])
    b = FakeProvider("b", [GOOD, GOOD])
    router = Router([a, b])
    generate_brief(P, router)
    generate_brief(P, router)
    assert len(a.calls) == 1
    c = FakeProvider("c", [BadRequest("bad")])
    assert generate_brief(P, Router([c])).status == "deferred"


def test_one_repair_then_ok_and_the_repair_mentions_the_problem():
    a = FakeProvider("a", [BAD_ID, GOOD])
    r = generate_brief(P, Router([a]))
    assert r.status == "published" and len(a.calls) == 2
    assert "rejected" in a.calls[1][1] and "setup:nope" in a.calls[1][1]


def test_failed_repair_moves_on_and_total_calls_are_bounded():
    a, b = FakeProvider("a", [BAD_ID, BAD_ID]), FakeProvider("b", [BAD_ID, BAD_ID])
    r = generate_brief(P, Router([a, b]))
    assert r.status == "deferred" and r.brief is None
    assert len(a.calls) + len(b.calls) <= 3
    assert "Nothing was invented" in r.reason


def test_all_unavailable_is_deferred_not_fabricated():
    r = generate_brief(P, Router([FakeProvider("a", [RateLimited("x")]),
                                  FakeProvider("b", [Transient("x")])]))
    assert r.status == "deferred" and r.brief is None
    assert [a.outcome for a in r.route.attempts] == ["rate_limited", "transient"]


def test_attempt_log_has_no_prompt_text():
    r = generate_brief(P, Router([FakeProvider("a", [GOOD])]))
    blob = json.dumps([a.__dict__ for a in r.route.attempts])
    assert "Evidence packet" not in blob and "[ctx:last_close]" not in blob
