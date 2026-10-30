"""Client tests against ``httpx.MockTransport``. The mock emulates OANDA's documented paging
(``from`` + ``count`` + ``includeFirst``) as recalled; it is NOT proof against the live API."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr

from sx_core.config import TradingModeError
from sx_data.errors import OandaError
from sx_data.oanda_parse import parse_oanda_time
from sx_data.oanda_rest import PRACTICE_HOST, OandaClient

ENV = {"SX_TRADING_MODE": "paper", "OANDA_ENV": "practice"}
TOKEN = "super-secret-token-123"
T0 = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
END = datetime(2026, 10, 19, 9, 1, tzinfo=UTC)
NOW = datetime(2026, 10, 19, 9, 1, tzinfo=UTC)


class Server:
    """Serves the fixture the way the practice API pages candles; records every request."""

    def __init__(self, payload):
        self.rows = payload["candles"]
        self.requests: list[httpx.Request] = []
        self.script: list[httpx.Response] = []  # canned responses served first

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.requests.append(req)
        if self.script:
            return self.script.pop(0)
        q = req.url.params
        start = parse_oanda_time(q["from"].replace("Z", ".000000000Z"))
        rows = [r for r in self.rows
                if (parse_oanda_time(r["time"]) >= start if q["includeFirst"] == "true"
                    else parse_oanda_time(r["time"]) > start)]
        return httpx.Response(200, json={"instrument": "EUR_USD", "granularity": q["granularity"],
                                         "candles": rows[: int(q["count"])]})


def client(server, **kw):
    kw.setdefault("sleep", lambda s: None)
    kw.setdefault("now", lambda: NOW)
    kw.setdefault("min_interval", 0.0)
    return OandaClient(SecretStr(TOKEN), env=ENV, transport=httpx.MockTransport(server), **kw)


def test_pages_through_the_fixture_and_drops_the_forming_bar(m1_payload, m1_closed):
    srv = Server(m1_payload)
    got = client(srv, page_size=50).fetch_candles("EUR_USD", "M1", T0, END)
    assert got == m1_closed and len(got) == 175
    assert len(srv.requests) >= 4  # 176 rows served 50 at a time


def test_request_shape(m1_payload):
    srv = Server(m1_payload)
    client(srv, page_size=50).fetch_candles("EUR_USD", "M1", T0, END)
    first, second = srv.requests[0], srv.requests[1]
    assert first.url.host == "api-fxpractice.oanda.com"
    assert first.url.path == "/v3/instruments/EUR_USD/candles"
    assert dict(first.url.params) == {"price": "MBA", "granularity": "M1",
                                      "from": "2026-10-19T06:00:00Z", "count": "50",
                                      "includeFirst": "true"}
    assert second.url.params["includeFirst"] == "false"
    assert all("to" not in r.url.params for r in srv.requests)  # never `to` with `count`
    assert first.headers["Authorization"] == f"Bearer {TOKEN}"


def test_window_is_clipped_to_start_and_end(m1_payload):
    srv = Server(m1_payload)
    s, e = T0 + timedelta(minutes=30), T0 + timedelta(minutes=60)
    got = client(srv, page_size=1000).fetch_candles("EUR_USD", "M1", s, e)
    assert got and got[0].time >= s and got[-1].time < e


def test_end_is_clamped_to_now(m1_payload):
    srv = Server(m1_payload)
    got = client(srv, now=lambda: T0 + timedelta(minutes=10)).fetch_candles(
        "EUR_USD", "M1", T0, T0 + timedelta(days=3))
    assert got[-1].time < T0 + timedelta(minutes=10)


def test_start_not_before_end_returns_nothing(m1_payload):
    srv = Server(m1_payload)
    assert client(srv).fetch_candles("EUR_USD", "M1", END, END) == []
    assert srv.requests == []


@pytest.mark.parametrize("tf", ["H4", "D"])
def test_h4_and_daily_are_not_fetched(m1_payload, tf):
    with pytest.raises(ValueError, match="resample"):
        client(Server(m1_payload)).fetch_candles("EUR_USD", tf, T0, END)


def test_naive_datetimes_are_rejected(m1_payload):
    with pytest.raises(ValueError):
        client(Server(m1_payload)).fetch_candles("EUR_USD", "M1", datetime(2026, 10, 19), END)


def test_rate_limit_retries_honour_retry_after(m1_payload):
    srv = Server(m1_payload)
    srv.script = [httpx.Response(429, headers={"Retry-After": "3"}), httpx.Response(503)]
    sleeps: list[float] = []
    got = client(srv, sleep=sleeps.append, page_size=1000).fetch_candles("EUR_USD", "M1", T0, END)
    assert len(got) == 175
    assert 3.0 in sleeps  # waited what the server asked
    assert len(srv.requests) == 4  # 2 failures, the data page, then one empty page that ends it


def test_gives_up_after_max_retries(m1_payload):
    srv = Server(m1_payload)
    srv.script = [httpx.Response(500)] * 10
    with pytest.raises(OandaError) as err:
        client(srv, max_retries=2).fetch_candles("EUR_USD", "M1", T0, END)
    assert err.value.status == 500 and len(srv.requests) == 3


def test_auth_failure_is_not_retried_and_never_leaks_the_token(m1_payload):
    srv = Server(m1_payload)
    srv.script = [httpx.Response(401, json={"errorMessage": "Insufficient authorization"})]
    c = client(srv)
    with pytest.raises(OandaError) as err:
        c.fetch_candles("EUR_USD", "M1", T0, END)
    assert err.value.status == 401 and len(srv.requests) == 1
    assert TOKEN not in str(err.value) and TOKEN not in repr(c)
    assert "Insufficient authorization" in str(err.value)


def test_network_errors_are_retried_then_reported_without_details(m1_payload):
    def boom(req):
        raise httpx.ConnectError("dns failure for host", request=req)

    c = OandaClient(SecretStr(TOKEN), env=ENV, transport=httpx.MockTransport(boom),
                    sleep=lambda s: None, now=lambda: NOW, max_retries=1, min_interval=0.0)
    with pytest.raises(OandaError, match="ConnectError"):
        c.fetch_candles("EUR_USD", "M1", T0, END)


def test_pagination_without_progress_is_an_error(m1_payload):
    row = m1_payload["candles"][0]
    srv = Server(m1_payload)
    srv.script = [httpx.Response(200, json={"candles": [row] * 2}),
                  httpx.Response(200, json={"candles": [row] * 2})]
    with pytest.raises(OandaError, match="progress"):
        client(srv, page_size=2).fetch_candles("EUR_USD", "M1", T0, END)


def test_construction_guards(m1_payload):
    srv = httpx.MockTransport(Server(m1_payload))
    with pytest.raises(TradingModeError):
        OandaClient(SecretStr(TOKEN), env={"SX_TRADING_MODE": "live"}, transport=srv)
    with pytest.raises(TradingModeError):
        OandaClient(SecretStr(TOKEN), env={**ENV, "OANDA_ENV": "live"}, transport=srv)
    with pytest.raises(TradingModeError):
        OandaClient(SecretStr(TOKEN), env=ENV, base_url="https://api-fxtrade.oanda.com",
                    transport=srv)
    with pytest.raises(OandaError):
        OandaClient(SecretStr(""), env=ENV, transport=srv)
    assert PRACTICE_HOST == "https://api-fxpractice.oanda.com"


def test_body_that_is_not_an_object_is_rejected(m1_payload):
    srv = Server(m1_payload)
    srv.script = [httpx.Response(200, content=json.dumps([1, 2]))]
    with pytest.raises(OandaError):
        client(srv).fetch_candles("EUR_USD", "M1", T0, END)


def test_a_short_follow_up_page_does_not_end_the_download(m1_payload, m1_closed):
    """Real-API regression: a follow-up page one candle short must not stop paging."""
    class ShortPages(Server):
        def __call__(self, req):
            resp = super().__call__(req)
            if req.url.params["includeFirst"] == "false":
                body = resp.json()
                body["candles"] = body["candles"][:-1] if len(body["candles"]) > 1 else []
                return httpx.Response(200, json=body)
            return resp
    srv = ShortPages(m1_payload)
    got = client(srv, page_size=50).fetch_candles("EUR_USD", "M1", T0, END)
    assert [c.time for c in got][:3] == [c.time for c in m1_closed][:3]
    assert len(got) >= 150 and len(srv.requests) >= 4
