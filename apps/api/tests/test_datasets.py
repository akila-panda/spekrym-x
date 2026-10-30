"""Lab dataset import API: validation, a fake client download, refusals, no token leaks."""

import json
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from sx_api.main import create_app
from sx_core.contracts import Candle

PAPER = {"SX_TRADING_MODE": "paper"}
GOOD = {"instrument": "EUR_USD", "tf": "H1", "start": "2026-01-05", "end": "2026-01-10"}


class FakeClient:
    def __init__(self, candles):
        self.candles = candles

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def fetch_candles(self, instrument, tf, start, end):
        return [c for c in self.candles if start <= c.time < end]


@pytest.fixture
def candles(fixtures_dir):
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return [Candle.model_validate(r) for r in raw]


def make(tmp_path, candles=None, factory=True):
    fac = (lambda: FakeClient(candles)) if factory else None
    return TestClient(create_app(env=PAPER, client_factory=fac, data_dir=tmp_path))


def wait(client, job_id):
    for _ in range(100):
        j = client.get(f"/lab/datasets/jobs/{job_id}").json()
        if j["state"] != "running":
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def req_for(candles):
    a = candles[0].time.date()
    return {"instrument": "EUR_USD", "tf": "H1", "start": str(a),
            "end": str(a + timedelta(days=20))}


def test_empty_folder_lists_nothing_and_offers_options(tmp_path):
    body = make(tmp_path).get("/lab/datasets").json()
    assert body["items"] == [] and "EUR_USD" in body["options"]["instruments"]
    assert body["token_configured"] is True


def test_download_writes_a_labelled_dataset_and_lists_it(tmp_path, candles):
    c = make(tmp_path, candles)
    body = req_for(candles)
    r = c.post("/lab/datasets/oanda", json=body)
    assert r.status_code == 202
    job = wait(c, r.json()["id"])
    assert job["state"] == "done", job
    assert "NOT INDEPENDENTLY VERIFIED" in job["result"]["label"]
    items = c.get("/lab/datasets").json()["items"]
    assert len(items) == 1 and items[0]["integrity"] == "ok" and items[0]["n_bars"] > 100
    assert items[0]["file"].endswith(".parquet") and items[0]["verified"] is False


def test_existing_file_is_not_overwritten(tmp_path, candles):
    c = make(tmp_path, candles)
    body = req_for(candles)
    wait(c, c.post("/lab/datasets/oanda", json=body).json()["id"])
    assert c.post("/lab/datasets/oanda", json=body).status_code == 409


def test_truncated_download_is_refused_not_saved(tmp_path, candles):
    c = make(tmp_path, candles[:30])
    r = c.post("/lab/datasets/oanda", json=req_for(candles))
    job = wait(c, r.json()["id"])
    assert job["state"] == "refused" and "stopped early" in job["message"]
    assert list(tmp_path.glob("*.parquet")) == []


@pytest.mark.parametrize("patch", [
    {"instrument": "../../etc/passwd"}, {"instrument": "BTC_USD"}, {"tf": "D"},
    {"start": "1999-01-01"}, {"end": "2026-01-01"}, {"start": "2030-01-01", "end": "2030-02-01"},
    {"start": "2005-01-01", "end": "2026-01-01", "tf": "M5"},
])
def test_bad_requests_are_rejected_before_any_download(tmp_path, candles, patch):
    c = make(tmp_path, candles)
    assert c.post("/lab/datasets/oanda", json={**GOOD, **patch}).status_code == 422


def test_missing_token_is_a_clear_400(tmp_path):
    c = make(tmp_path, factory=False)
    assert c.get("/lab/datasets").json()["token_configured"] is False
    r = c.post("/lab/datasets/oanda", json=GOOD)
    assert r.status_code == 400 and "OANDA_TOKEN" in r.json()["detail"]


def test_unknown_job_is_404(tmp_path):
    assert make(tmp_path).get("/lab/datasets/jobs/nope").status_code == 404


def test_modified_and_unlabelled_files_are_flagged(tmp_path, candles):
    c = make(tmp_path, candles)
    wait(c, c.post("/lab/datasets/oanda", json=req_for(candles)).json()["id"])
    f = next(tmp_path.glob("*.parquet"))
    (tmp_path / "stray.parquet").write_bytes(b"x")
    f.write_bytes(f.read_bytes() + b"0")
    got = {i["file"]: i["integrity"] for i in c.get("/lab/datasets").json()["items"]}
    assert got[f.name] == "modified" and got["stray.parquet"] == "no_provenance"


def test_unexpected_error_does_not_leak_details(tmp_path):
    class Boom(FakeClient):
        def fetch_candles(self, *a):
            raise RuntimeError("secret-token-abc")
    c = TestClient(create_app(env=PAPER, client_factory=lambda: Boom([]), data_dir=tmp_path))
    job = wait(c, c.post("/lab/datasets/oanda", json=GOOD).json()["id"])
    assert job["state"] == "failed" and "secret-token-abc" not in json.dumps(job)


def test_cors_allows_post_from_the_dev_server(tmp_path):
    r = make(tmp_path).options("/lab/datasets/oanda", headers={
        "Origin": "http://localhost:5175", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 200 and "POST" in r.headers["access-control-allow-methods"]
