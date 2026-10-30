"""GET /suggestions service (Phase 9B). Read-only: it never places an order and never trains.

It reads the 9A result files (``assistant/outputs/model``), loads the saved scorer if the files
match their hash, builds H1 setups from the active data source and asks the engine for
suggestions. With no 9A result it returns an empty list and says so. Every payload carries the
data source label and the honesty labels.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sx_assistant.model.windowed import windowed_setups
from sx_assistant.premarket.data_source import MarketDataSource
from sx_assistant.suggestions.engine import SCORER_TF, build_suggestions

LABELS = ["Exploratory", "Not validated", "Retrospective"]
SHOWN_BARS = 72
VAL_KEEP = ("stage", "spec_hash", "data_version", "model_sha256", "variants_tried", "split_rows",
            "metrics", "chosen_params")
HOLD_KEEP = ("stage", "spec_hash", "data_version", "metrics", "verdict")


def _read(path: Path, keep: tuple[str, ...]) -> dict | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise ValueError(f"{path.name} is not valid JSON: {e}") from e
    return {k: raw[k] for k in keep if k in raw}


def scorer_status(model_dir: Path) -> dict:
    """What the 9A files say, whitelisted. Computes nothing new except the plain reading."""
    val_raw = model_dir / "validation_results.json"
    val = _read(val_raw, VAL_KEEP)
    hold = _read(model_dir / "holdout_results.json", HOLD_KEEP)
    if hold and not val:
        raise ValueError("holdout_results.json exists without validation_results.json")
    if not val:
        return {"stage": "none", "reading": "No 9A validation result exists yet.",
                "validation": None, "holdout": None}
    ctrl = json.loads(val_raw.read_text()).get("controls", {})
    p95 = ctrl.get("shuffled", {}).get("auc_p95")
    val["shuffled_auc_p95"] = p95
    val["controls_behaved"] = bool(ctrl.get("shuffled", {}).get("behaves_as_expected")
                                   and ctrl.get("leaked", {}).get("behaves_as_expected"))
    if hold:
        reading = hold.get("verdict", "Holdout opened; no verdict recorded.")
    elif p95 is None:
        reading = "Validation only; the shuffled-label range is missing."
    elif val["metrics"]["auc"] > p95:
        reading = ("Validation only: AUC is above the shuffled-label range. The holdout has not "
                   "been opened, so this is not confirmed.")
    else:
        reading = ("Validation only: AUC is NOT above the shuffled-label range, so the rank "
                   "shows no demonstrated skill. The holdout has not been opened.")
    return {"stage": "complete" if hold else "validated", "reading": reading,
            "validation": val, "holdout": hold}


def _load_scorer(model_dir: Path, sha: str, cache: dict):
    key = ("scorer", sha)
    for name in ("scorer.lgb", "scorer_reference.json"):
        if not (model_dir / name).exists():
            raise FileNotFoundError(f"{name} is missing from {model_dir}")
    if key not in cache:
        from sx_assistant.model.scorer import Scorer  # lazy: needs lightgbm and libomp
        cache[key] = Scorer.load(model_dir, expect_hash=sha)
    return cache[key]


def build_payload(source: MarketDataSource, instrument: str, as_of: datetime, model_dir: Path,
                  rules_path: Path, cache: dict) -> dict:
    status = scorer_status(model_dir)
    head = {"instrument": instrument, "tf": SCORER_TF, "as_of": as_of.isoformat().replace(
        "+00:00", "Z"), "source": {"id": source.info.id, "name": source.info.name,
                                  "label": source.info.label, "live": source.info.live},
            "labels": LABELS, "scorer": status, "items": [], "evidence": [], "candles": [],
            "rejected": []}
    if status["stage"] == "none":
        return {**head, "status": "no_result", "note": "No suggestions: run the 9A validation "
                "first (python -m sx_assistant.model.run validate)."}
    sha = status["validation"]["model_sha256"]
    try:
        scorer = _load_scorer(model_dir, sha, cache)
    except Exception as e:  # reported to the user below, never hidden (lightgbm raises its own)
        return {**head, "status": "model_unavailable",
                "note": f"The saved scorer could not be loaded ({type(e).__name__}: {e})."}
    bars = source.candles(instrument, SCORER_TF, as_of)
    res = build_suggestions(windowed_setups(bars), bars, scorer, rules_path, as_of=as_of) \
        if bars else None
    shown = bars[-SHOWN_BARS:]
    items = [] if res is None else [
        {"suggestion": s.to_wire(), "labels": list(res.scored[s.id].labels),
         "model_version": res.scored[s.id].model_version, "note": res.scored[s.id].note}
        for s in res.suggestions]
    return {**head, "status": "ok", "items": items,
            "evidence": [] if res is None else [e.to_wire()
                                                for e in res.evidence.values()],
            "candles": [{"time": c.time.isoformat().replace("+00:00", "Z"), "open": c.open,
                         "high": c.high, "low": c.low, "close": c.close} for c in shown],
            "rejected": [] if res is None else [{"setup_id": r.setup_id, "why": r.why}
                                                for r in res.rejected],
            "note": "Levels use the 9A barrier multiples; no costs; advice only, no order placed."
            if items else "No setup passed the freshness and lifecycle filters at this time."}
