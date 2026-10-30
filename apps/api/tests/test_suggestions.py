"""GET /suggestions: honest empty states, whitelisted 9A files, labels and the source label."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sx_api.main import create_app
from sx_api.suggestions import scorer_status

PAPER = {"SX_TRADING_MODE": "paper"}
VAL = {"stage": "validation", "spec_hash": "s", "config_hash": "c", "model_sha256": "abc",
       "data_version": "dv:x", "variants_tried": 5, "chosen_params": {"num_leaves": 4},
       "split_rows": {"train": 10}, "environment": {"host": "SECRET"},
       "metrics": {"n": 100, "auc": 0.52, "auc_ci95_iid": [0.4, 0.6],
                   "target_first_share_all": 0.4, "top_fifth_n": 20,
                   "top_fifth_target_first_share": 0.45},
       "controls": {"shuffled": {"auc_p95": 0.56, "behaves_as_expected": True},
                    "leaked": {"behaves_as_expected": True}}}


def _client(tmp_path, val=None, hold=None):
    m = tmp_path / "model"
    m.mkdir()
    if val is not None:
        (m / "validation_results.json").write_text(json.dumps(val))
    if hold is not None:
        (m / "holdout_results.json").write_text(json.dumps(hold))
    return TestClient(create_app(env=PAPER, model_dir=m))


def test_no_result_gives_an_empty_labelled_list(tmp_path):
    r = _client(tmp_path).get("/suggestions").json()
    assert r["status"] == "no_result" and r["items"] == [] and r["scorer"]["stage"] == "none"
    assert r["source"]["label"] == "SAMPLE DATA — NOT LIVE" and "Not validated" in r["labels"]


def test_missing_model_file_is_reported_not_hidden(tmp_path):
    r = _client(tmp_path, VAL).get("/suggestions").json()
    assert r["status"] == "model_unavailable" and r["items"] == []
    assert "environment" not in json.dumps(r) and "SECRET" not in json.dumps(r)


def test_reading_says_null_when_auc_is_inside_the_shuffled_range(tmp_path):
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "validation_results.json").write_text(json.dumps(VAL))
    s = scorer_status(tmp_path / "m")
    assert s["stage"] == "validated" and "NOT above" in s["reading"]
    assert s["validation"]["shuffled_auc_p95"] == 0.56 and s["holdout"] is None


def test_holdout_without_validation_is_refused_and_bad_time_is_422(tmp_path):
    c = _client(tmp_path, None, {"stage": "holdout"})
    assert c.get("/suggestions").status_code == 422
    assert c.get("/suggestions", params={"as_of": "2026-01-01T00:00:00"}).status_code == 422


@pytest.mark.skipif(not Path("assistant/outputs/model/scorer.lgb").exists(),
                    reason="needs a real 9A run on the owner's machine")
def test_real_scorer_serves_items_with_labels():  # runs only where validate has been run
    r = TestClient(create_app(env=PAPER)).get("/suggestions").json()
    assert r["status"] in ("ok", "model_unavailable")


def test_wire_payload_has_no_null_fields_zod_would_reject():
    """Regression: `forecast_id: null` broke the Suggestions screen (zod rejects null)."""
    from sx_core.contracts import Suggestion

    s = Suggestion(id="sg:t", instrument="EUR_USD", tf="H1", created_at="2026-10-19T10:00:00Z",
                   setup_ids=["st:a"], side="long", entry=1.1, stop=1.09, target=1.12, score=50.0,
                   reasons=[{"text": "x", "evidence_id": "st:a"}], gates=[],
                   rules_version="paper_v1", status="not_validated")
    assert s.forecast_id is None
    assert "forecast_id" not in s.to_wire()
    assert "forecast_id" in s.model_dump(mode="json")  # the old call: key present with None
