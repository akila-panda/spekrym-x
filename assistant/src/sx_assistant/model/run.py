"""Stages for the scorer evaluation (P11). Two commands, mirroring the Lab's EXP-001 flow:

  python -m sx_assistant.model.run validate --candles FILE.parquet
  python -m sx_assistant.model.run holdout --candles FILE.parquet --reason "..." \
      --confirm-spend-holdout
  python -m sx_assistant.model.run report

Candles come from a Parquet file written by the Lab importer (read through ``sx_core.storage``;
no Lab code is imported). Outputs go to ``assistant/outputs/model/`` (gitignored).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from sx_assistant.model.controls import leaked_feature_control, shuffled_control
from sx_assistant.model.features import build_rows
from sx_assistant.model.labels_triple_barrier import label_rows
from sx_assistant.model.protocol import (KIND_TRIAL, HoldoutRefused, ProtocolError, ProtocolSpec,
                                         ScorerPartition)
from sx_assistant.model.scorer import LABELS, Scorer
from sx_assistant.model.train_lgbm import auc, fit, margin, rank_metrics
from sx_assistant.model.windowed import windowed_setups
from sx_core.contracts import Setup
from sx_core.ledger import Ledger
from sx_core.storage import candles_to_frame, data_version, frame_to_candles, read_parquet

OUT = Path("assistant/outputs/model")


def _load(path: str, spec: ProtocolSpec) -> tuple[ScorerPartition, pd.DataFrame, str]:
    candles = frame_to_candles(read_parquet(path))
    if not candles or candles[0].instrument != spec.instrument or candles[0].tf != spec.tf:
        raise SystemExit(f"refused: file is not {spec.instrument} {spec.tf}")
    dv = data_version(candles_to_frame(candles))
    cache = OUT / f"setups_{dv.replace(':', '_')}.json"
    if cache.exists():
        setups = [Setup.model_validate(d) for d in json.loads(cache.read_text())]
    else:
        print("computing setups on windows (several minutes) ...")
        setups = windowed_setups(candles, progress=lambda a, b: print(f"  {a}/{b}", end="\r"))
        OUT.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([s.model_dump(mode="json") for s in setups]))
    frame = candles_to_frame(candles)
    rows = build_rows(setups, candles, spec.barrier)
    rows = rows.join(label_rows(rows, frame, spec.barrier), how="inner")
    return ScorerPartition(rows, len(candles), spec, dv), rows, dv


def _config_hash(params: dict, model_sha: str, spec: ProtocolSpec) -> str:
    blob = json.dumps({"params": params, "model": model_sha, "spec": spec.hash}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _verdict(val_auc: float, hold_auc: float, v_p95: float, h_p95: float) -> str:
    v, h = val_auc > v_p95, hold_auc > h_p95
    return {(True, True): "Both periods rank above the shuffled-label range (Exploratory only).",
            (False, True): "Holdout above shuffled range but validation was not: inconsistent. "
                           "Treat as null; do not report the holdout alone.",
            (True, False): "Validation above shuffled range but the holdout did not confirm it.",
            (False, False): "NULL: neither period ranks above the shuffled-label range."}[(v, h)]


def validate(path: str) -> None:
    spec, ledger = ProtocolSpec(), Ledger(OUT / "ledger.jsonl")
    part, _, dv = _load(path, spec)
    tr, va, feats = part.train(), part.validation(), list(spec.feature_names)
    print(part, "| spec", spec.hash[:12])
    best = None
    for k, params in enumerate(spec.grid):
        m = fit(tr[feats], tr["label"].to_numpy(), params, spec.seed)
        a = auc(va["label"].to_numpy(), margin(m, va[feats]))
        ledger.append(KIND_TRIAL, {"trial": k, "params": params, "validation_auc": a,
                                   "spec_hash": spec.hash}, dv)
        print(f"trial {k} {params} validation AUC {a:.4f}")
        if best is None or a > best[0]:
            best = (a, params, m)
    _, params, model = best
    marg_va = margin(model, va[feats])
    ctrl = {"shuffled": shuffled_control(tr, va, feats, spec.grid, spec.n_shuffles, spec.seed),
            "leaked": leaked_feature_control(tr, va, feats, params, spec.seed)}
    sha = Scorer(model, marg_va).save(OUT)
    cfg = _config_hash(params, sha, spec)
    part.lock_evaluation(ledger, cfg)
    res = {"stage": "validation", "labels": list(LABELS), "spec_hash": spec.hash,
           "config_hash": cfg, "model_sha256": sha, "chosen_params": params,
           "variants_tried": len(spec.grid), "data_version": dv, "metrics": rank_metrics(
               va["label"].to_numpy(), marg_va), "controls": ctrl,
           "split_rows": {"train": len(tr), "validation": len(va), "purged": part.n_purged}}
    (OUT / "validation_results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res["metrics"], indent=2), "\ncontrols:", json.dumps(ctrl, indent=2))
    print("NEXT: review, then run the holdout stage once.")


def holdout(path: str, reason: str) -> None:
    spec, ledger = ProtocolSpec(), Ledger(OUT / "ledger.jsonl")
    val = json.loads((OUT / "validation_results.json").read_text())
    part, _, dv = _load(path, spec)
    scorer = Scorer.load(OUT, expect_hash=val["model_sha256"])
    if _config_hash(val["chosen_params"], val["model_sha256"], spec) != val["config_hash"]:
        raise SystemExit("refused: validation_results.json was edited")
    feats = list(spec.feature_names)
    ho = part.open_holdout(ledger, val["config_hash"], reason)  # logs the opening FIRST
    m = margin(scorer.model, ho[feats])
    tr = part.train()
    ctrl = shuffled_control(tr, ho, feats, [val["chosen_params"]], spec.n_shuffles,
                            spec.seed)
    res = {"stage": "holdout", "labels": list(LABELS), "spec_hash": spec.hash,
           "config_hash": val["config_hash"], "data_version": dv,
           "metrics": rank_metrics(ho["label"].to_numpy(), m), "shuffled_control": ctrl,
           "verdict": _verdict(val["metrics"]["auc"], auc(ho["label"].to_numpy(), m),
                               val["controls"]["shuffled"]["auc_p95"], ctrl["auc_p95"])}
    (OUT / "holdout_results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


def report() -> None:
    v = json.loads((OUT / "validation_results.json").read_text())
    h = OUT / "holdout_results.json"
    print("VALIDATION (model selection):", json.dumps(v["metrics"]))
    print("  shuffled-label range:", json.dumps(v["controls"]["shuffled"]))
    print("  leak control:", json.dumps(v["controls"]["leaked"]))
    print("HOLDOUT:", "not opened" if not h.exists() else h.read_text())
    print("Labels:", ", ".join(LABELS), "| variants tried:", v["variants_tried"])


def main() -> None:
    p = argparse.ArgumentParser(prog="sx-model")
    p.add_argument("stage", choices=["validate", "holdout", "report"])
    p.add_argument("--candles")
    p.add_argument("--reason", default="")
    p.add_argument("--confirm-spend-holdout", action="store_true")
    a = p.parse_args()
    if a.stage == "report":
        return report()
    if not a.candles:
        raise SystemExit("--candles is required")
    try:
        if a.stage == "validate":
            return validate(a.candles)
        if not a.confirm_spend_holdout:
            raise SystemExit("refused: add --confirm-spend-holdout (the holdout opens once)")
        holdout(a.candles, a.reason)
    except (HoldoutRefused, ProtocolError) as e:
        raise SystemExit(f"refused: {e}") from None


if __name__ == "__main__":
    main()
