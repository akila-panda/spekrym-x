"""Analyst routes (Phase 9C-2) with fake providers: no network, no real keys."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "assistant" / "tests"))

from analyst_helpers import sample_packet  # noqa: E402

from sx_api.main import create_app  # noqa: E402
from sx_assistant.analyst.config import ProviderSetup  # noqa: E402
from sx_assistant.analyst.errors import RateLimited  # noqa: E402
from sx_assistant.analyst.providers.fake import FakeProvider, echo_reply  # noqa: E402

PAPER = {"SX_TRADING_MODE": "paper"}


def client(tmp_path, provider):
    app = create_app(env=PAPER, analyst_dir=tmp_path / "an",
                     analyst_setup=lambda _c: ProviderSetup([provider], {}, {"fake": 50}))
    return TestClient(app)


def test_status_and_empty_brief_make_no_call(tmp_path):
    p = FakeProvider("fake", [])
    c = client(tmp_path, p)
    s = c.get("/analyst/status").json()
    assert s["status"] == "ok" and s["providers"][0]["health"] == "unknown"
    b = c.get("/analyst/brief").json()
    assert b["status"] == "none" and "Not validated" in b["labels"] and not p.calls


def test_post_generates_then_reuses_and_get_returns_it(tmp_path):
    p = FakeProvider("fake", [echo_reply(sample_packet())])
    c = client(tmp_path, p)
    r = c.post("/analyst/brief").json()
    assert r["status"] == "published" and r["reused"] is False
    assert r["source_label"].startswith("SAMPLE") and r["brief"]["labels"] == [
        "Exploratory", "Not validated"]
    assert c.post("/analyst/brief").json()["reused"] is True and len(p.calls) == 1
    g = c.get("/analyst/brief").json()
    assert g["status"] == "ready" and g["brief"] == r["brief"]
    assert c.get("/analyst/status").json()["providers"][0]["requests_today_estimate"] == 1


def test_all_providers_down_is_deferred_with_a_reason(tmp_path):
    c = client(tmp_path, FakeProvider("fake", [RateLimited("x", retry_after=60.0)]))
    r = c.post("/analyst/brief").json()
    assert r["status"] == "deferred" and "Nothing was invented" in r["reason"]
    assert c.get("/analyst/brief").json()["status"] == "none"
    assert c.get("/analyst/status").json()["providers"][0]["health"] == "cooling_down"


def test_default_app_without_settings_reports_unavailable_not_an_error(tmp_path):
    app = create_app(env=PAPER, analyst_dir=tmp_path / "an")
    r = TestClient(app).post("/analyst/brief").json()
    assert r["status"] == "unavailable" and r["attempts"] == []


def test_unknown_instrument_is_404(tmp_path):
    assert client(tmp_path, FakeProvider("fake", [])).post(
        "/analyst/brief?instrument=XXX_YYY").status_code == 404
