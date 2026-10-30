"""GET /lab/exp001 reads stored result files, whitelists fields and refuses mixed specs."""

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from sx_api.main import create_app

FIX = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "lab" / "exp001"
PAPER = {"SX_TRADING_MODE": "paper"}


def _client(tmp_path, files=()):
    out = tmp_path / "outputs"
    (out / "exp001").mkdir(parents=True)
    for f in files:
        shutil.copy(FIX / f, out / "exp001" / f)
    return TestClient(create_app(env=PAPER, data_dir=out / "data"))


def test_not_run_when_no_files(tmp_path):
    r = _client(tmp_path).get("/lab/exp001").json()
    assert r["status"] == "not_run" and r["validation"] is None and r["holdout"] is None


def test_validated_then_complete_and_environment_is_dropped(tmp_path):
    r = _client(tmp_path, ["validation_results.json"]).get("/lab/exp001").json()
    assert r["status"] == "validated" and r["validation"]["outcome"] == "loss"
    both = ["validation_results.json", "holdout_results.json"]
    r = _client(tmp_path / "b", both).get("/lab/exp001").json()
    assert r["status"] == "complete" and r["holdout"]["outcome"] == "tie"
    assert "environment" not in json.dumps(r) and "SECRET-HOST" not in json.dumps(r)


def test_mixed_spec_hashes_and_orphan_holdout_are_refused(tmp_path):
    c = _client(tmp_path, ["validation_results.json", "holdout_results.json"])
    p = tmp_path / "outputs" / "exp001" / "holdout_results.json"
    d = json.loads(p.read_text())
    d["spec_hash"] = "other"
    p.write_text(json.dumps(d))
    assert c.get("/lab/exp001").status_code == 500
    c2 = _client(tmp_path / "c", ["holdout_results.json"])
    assert c2.get("/lab/exp001").status_code == 500
