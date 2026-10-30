"""Delete, trash, restore and the in-use protection for Lab datasets."""

import json
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from sx_api.main import create_app
from sx_core.contracts import Candle

PAPER = {"SX_TRADING_MODE": "paper"}


class FakeClient:
    def __init__(self, candles):
        self.candles = candles

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def fetch_candles(self, instrument, tf, start, end):
        return [c for c in self.candles if start <= c.time < end]


def req_for(candles):
    a = candles[0].time.date()
    return {"instrument": "EUR_USD", "tf": "H1", "start": str(a),
            "end": str(a + timedelta(days=20))}


def wait(client, job_id):
    for _ in range(100):
        j = client.get(f"/lab/datasets/jobs/{job_id}").json()
        if j["state"] != "running":
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


@pytest.fixture
def candles(fixtures_dir):
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return [Candle.model_validate(r) for r in raw]


def setup(tmp_path, candles):
    data, exp, model = tmp_path / "data", tmp_path / "exp", tmp_path / "model"
    for d in (data, exp, model):
        d.mkdir()
    c = TestClient(create_app(env=PAPER, client_factory=lambda: FakeClient(candles), data_dir=data,
                              experiments_dir=exp, model_dir=model))
    body = req_for(candles)
    wait(c, c.post("/lab/datasets/oanda", json=body).json()["id"])
    row = c.get("/lab/datasets").json()["items"][0]
    return c, data, exp, model, row


def test_delete_moves_to_trash_and_frees_the_name(tmp_path, candles):
    c, data, _, _, row = setup(tmp_path, candles)
    assert row["in_use"] == []
    r = c.delete(f"/lab/datasets/{row['file']}")
    assert r.status_code == 200
    body = c.get("/lab/datasets").json()
    assert body["items"] == [] and body["trash"][0]["file"] == row["file"]
    assert (data / ".trash" / r.json()["trashed"]).exists()
    # the name is free again, so the same range can be downloaded afresh
    assert c.post("/lab/datasets/oanda", json=req_for(candles)).status_code == 202


def test_a_dataset_named_by_a_locked_experiment_is_refused(tmp_path, candles):
    c, data, exp, _, row = setup(tmp_path, candles)
    (exp / "EXP-009.yaml").write_text(f'data:\n  data_version: "{row["data_version"]}"\n')
    listed = c.get("/lab/datasets").json()["items"][0]
    assert listed["in_use"] == ["exp/EXP-009.yaml"]
    r = c.delete(f"/lab/datasets/{row['file']}")
    assert r.status_code == 409 and "EXP-009.yaml" in r.json()["detail"]
    assert (data / row["file"]).exists()


def test_a_saved_model_file_also_protects_the_data(tmp_path, candles):
    c, data, _, model, row = setup(tmp_path, candles)
    blob = json.dumps({"data_version": row["data_version"]})
    (model / "validation_results.json").write_text(blob)
    assert c.delete(f"/lab/datasets/{row['file']}").status_code == 409


def test_unknown_or_path_like_names_are_refused(tmp_path, candles):
    c, *_ = setup(tmp_path, candles)
    assert c.delete("/lab/datasets/nope.parquet").status_code == 404
    assert c.delete("/lab/datasets/..%2F..%2Fsecret.parquet").status_code in (404, 405)
    assert c.post("/lab/datasets/trash/..%2Fx/restore").status_code in (404, 409)
    assert c.delete("/lab/datasets/trash/not-a-trash-id").status_code == 404


def test_restore_brings_back_file_and_provenance(tmp_path, candles):
    c, data, _, _, row = setup(tmp_path, candles)
    tid = c.delete(f"/lab/datasets/{row['file']}").json()["trashed"]
    assert c.post(f"/lab/datasets/trash/{tid}/restore").json() == {"restored": row["file"]}
    again = c.get("/lab/datasets").json()["items"][0]
    assert again["integrity"] == "ok" and again["data_version"] == row["data_version"]


def test_restore_never_overwrites_a_file_that_came_back(tmp_path, candles):
    c, data, _, _, row = setup(tmp_path, candles)
    tid = c.delete(f"/lab/datasets/{row['file']}").json()["trashed"]
    wait(c, c.post("/lab/datasets/oanda", json=req_for(candles)).json()["id"])
    assert c.post(f"/lab/datasets/trash/{tid}/restore").status_code == 409


def test_purge_removes_the_trash_item_for_good(tmp_path, candles):
    c, data, _, _, row = setup(tmp_path, candles)
    tid = c.delete(f"/lab/datasets/{row['file']}").json()["trashed"]
    assert c.delete(f"/lab/datasets/trash/{tid}").status_code == 200
    assert c.get("/lab/datasets").json()["trash"] == [] and list((data / ".trash").iterdir()) == []


def test_cors_allows_delete_from_the_dev_origin(tmp_path, candles):
    c, *_ = setup(tmp_path, candles)
    r = c.options("/lab/datasets/x.parquet", headers={"Origin": "http://localhost:5175",
                  "Access-Control-Request-Method": "DELETE"})
    assert "DELETE" in r.headers.get("access-control-allow-methods", "")
