"""Phase 5A API: health, premarket, guards, placeholders."""

import pytest
from fastapi.testclient import TestClient

from sx_api.main import create_app
from sx_core.config import TradingModeError
from sx_core.contracts import Candle, Setup

PAPER = {"SX_TRADING_MODE": "paper"}


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(env=PAPER))


def test_refuses_to_start_unless_paper():
    for env in ({}, {"SX_TRADING_MODE": "live"}, {**PAPER, "OANDA_ENV": "live"}):
        with pytest.raises(TradingModeError):
            create_app(env=env)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["trading_mode"] == "paper"
    assert body["source"]["live"] is False and "NOT LIVE" in body["source"]["label"]


def test_premarket_default_is_contract_valid_and_causal(client):
    r = client.get("/premarket")
    assert r.status_code == 200
    p = r.json()
    for c in p["candles"]:
        Candle.model_validate(c)
    setups = [Setup.model_validate(s) for s in p["setups"]]
    assert setups and all(s.known_at.isoformat().replace("+00:00", "Z") <= p["as_of"]
                          for s in setups)
    assert "NOT LIVE" in p["source"]["label"] and p["status_labels"] == ["sample", "causal"]


def test_premarket_earlier_as_of_has_less(client):
    early = client.get("/premarket", params={"as_of": "2026-10-26T04:00:00Z"}).json()
    late = client.get("/premarket").json()
    assert early["as_of"] < late["as_of"] and len(early["candles"]) < len(late["candles"])
    assert all(s["known_at"] <= early["as_of"] for s in early["setups"])


@pytest.mark.parametrize("params,code", [
    ({"as_of": "2026-10-27T12:00:00Z"}, 422),
    ({"as_of": "not-a-time"}, 422),
    ({"as_of": "2026-10-26T12:00:00"}, 422),
    ({"instrument": "GBP_USD"}, 404),
])
def test_premarket_bad_requests(client, params, code):
    assert client.get("/premarket", params=params).status_code == code


@pytest.mark.parametrize("path", ["/suggestions", "/paper", "/lab"])
def test_placeholders_are_empty(client, path):
    assert client.get(path).json()["status"] == "not_built"


def test_cors_allows_vite_dev_port_only(client):
    ok = client.get("/health", headers={"Origin": "http://localhost:5175"})
    bad = client.get("/health", headers={"Origin": "http://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5175"
    assert "access-control-allow-origin" not in bad.headers


def test_root_points_to_the_real_routes(client):
    body = client.get("/").json()
    assert body["paper_only"] is True and "/premarket" in body["try"]


def test_dotenv_is_found_in_a_parent_folder(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("SX_TRADING_MODE=paper\n")
    nested = tmp_path / "apps" / "web"
    nested.mkdir(parents=True)
    monkeypatch.delenv("SX_TRADING_MODE", raising=False)
    monkeypatch.chdir(nested)
    assert create_app() is not None


def test_no_dotenv_and_no_variable_still_refuses(tmp_path, monkeypatch):
    monkeypatch.delenv("SX_TRADING_MODE", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(TradingModeError):
        create_app()
