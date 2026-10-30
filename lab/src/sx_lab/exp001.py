"""EXP-001 stages (8B): ``validate`` (train, score validation) then ``holdout`` (one shot).

Needs torch + minimamba (imported lazily by the CLI). Weights are saved after ``validate`` and
their hashes go into the ledger, so ``holdout`` scores the SAME models. Every check runs BEFORE
the holdout is opened; the holdout frame is written to disk the moment it is opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from sx_data.importer import read_provenance
from sx_lab.evaluation import metrics
from sx_lab.exp001_core import (KIND_SCORED, KIND_VALIDATED, LABELS, SEEDS, STUDY, Exp001Refused,
                                check_pins, conformal_block, environment, make_baselines,
                                prepare, score_all, variants_for)
from sx_lab.models.minimamba_vol import (MiniMambaEnsemble, MiniMambaVol, TrainConfig,
                                         sha256_bytes)


def _cfg(spec) -> TrainConfig:
    s = next(m for m in spec.models if m.name == "minimamba").settings
    return TrainConfig(d_model=int(s["d_model"]), n_layer=int(s["n_layer"]),
                       context_bars=int(s["context_bars"]))


def _write(path: Path, obj: dict) -> str:
    blob = (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode()
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def run_validate(a: argparse.Namespace, log=print) -> dict:
    spec, h, part, ledger = prepare(a)
    out = Path(a.out) / "exp001"
    if part.holdout_status(ledger) == "opened":
        raise Exp001Refused("holdout already opened; EXP-001 is finished")
    if any(e.kind == KIND_VALIDATED and e.payload["spec_hash"] == h for e in ledger.read()):
        raise Exp001Refused("EXP-001 validation already ran (one run only, locked spec)")
    if variants_for(ledger) + len(SEEDS) > spec.max_variants:
        raise Exp001Refused(f"would exceed max_variants {spec.max_variants}")
    pins = check_pins(spec)
    (out / "models").mkdir(parents=True, exist_ok=True)
    train, val = part.train(), part.validation()
    cfg = _cfg(spec)
    base = make_baselines(spec, train)
    hist = train.iloc[-(cfg.context_bars - 1):]
    members, weights, t0 = [], {}, time.time()
    for i, seed in enumerate(SEEDS):
        m = MiniMambaVol(TrainConfig(**{**cfg.__dict__, "seed": seed})).fit(train, log=log)
        q = metrics.qlike(m.predict(val, hist), val["target"])
        blob = m.state_bytes()
        (out / "models" / f"minimamba_seed{seed}.pt").write_bytes(blob)
        weights[seed] = sha256_bytes(blob)
        ledger.append("lab.trial", {"study": STUDY, "number": i, "split": "validation",
                                    "params": {"model": "minimamba", "seed": seed,
                                               "epochs": cfg.epochs, "d_model": cfg.d_model},
                                    "value": q}, part.data_version)
        members.append(m)
        log(f"seed {seed} done: validation QLIKE {q:.5f} ({time.time() - t0:.0f}s elapsed)")
    ens = MiniMambaEnsemble(members)
    preds = pd.DataFrame({n: b.predict(val) for n, b in base.items()})
    preds["minimamba"] = ens.predict(val, hist)
    res = score_all(preds[[m.name for m in spec.models if m.name in preds.columns]],
                    val["target"], spec)
    half = len(val) // 2
    ev = slice(half + part.embargo, None)
    conf = {n: conformal_block(spec, preds[n].iloc[:half], val["target"].iloc[:half],
                               preds[n].iloc[ev], val["target"].iloc[ev])
            for n in ("minimamba", "har")}
    seeds_q = {f"seed{m.cfg.seed}": metrics.qlike(m.predict(val, hist), val["target"])
               for m in members}
    preds.assign(target=val["target"]).to_parquet(out / "predictions_validation.parquet")
    result = {"experiment": STUDY, "stage": "validation", "labels": LABELS, "spec_hash": h,
              "data_version": part.data_version, "n_validation": len(val),
              "data_label": read_provenance(a.candles)["label"], **res,
              "conformal": conf, "per_seed_qlike_diagnostic": seeds_q,
              "train_loss_by_epoch": {f"seed{m.cfg.seed}": m.loss_by_epoch for m in members},
              "har_n_floored": base["har"].n_floored, "pins": pins,
              "environment": environment(), "variants_tried": variants_for(ledger),
              "train_config": cfg.__dict__, "train_seconds": round(time.time() - t0)}
    digest = _write(out / "validation_results.json", result)
    ledger.append(KIND_VALIDATED, {"spec_hash": h, "results_sha256": digest,
                                   "weights_sha256": {str(k): v for k, v in weights.items()},
                                   "model_choice": f"minimamba = mean log-variance of seeds "
                                                   f"{list(SEEDS)}; no seed selection",
                                   "outcome_validation": res["outcome"]}, part.data_version)
    return result


def run_holdout(a: argparse.Namespace, log=print) -> dict:
    if not a.confirm_spend_holdout or not (a.reason or "").strip():
        raise Exp001Refused("needs --reason and --confirm-spend-holdout (one-shot)")
    spec, h, part, ledger = prepare(a)
    out = Path(a.out) / "exp001"
    ent = [e for e in ledger.read() if e.kind == KIND_VALIDATED and e.payload["spec_hash"] == h]
    if not ent:
        raise Exp001Refused("run exp001-validate first (no validated entry in the ledger)")
    rec = ent[-1].payload
    vpath = out / "validation_results.json"
    if hashlib.sha256(vpath.read_bytes()).hexdigest() != rec["results_sha256"]:
        raise Exp001Refused("validation_results.json changed since it was logged")
    check_pins(spec)
    members = []
    for seed in SEEDS:
        blob = (out / "models" / f"minimamba_seed{seed}.pt").read_bytes()
        if sha256_bytes(blob) != rec["weights_sha256"][str(seed)]:
            raise Exp001Refused(f"weights for seed {seed} differ from the ledger")
        members.append(MiniMambaVol.from_state_bytes(blob))
    ens = MiniMambaEnsemble(members)
    train, val = part.train(), part.validation()
    cfg = _cfg(spec)
    base = make_baselines(spec, train)
    stored = json.loads(vpath.read_text())["scores"]
    for n, b in base.items():                      # baselines must reproduce the logged scores
        q = metrics.qlike(b.predict(val), val["target"])
        if abs(q - stored[n]["qlike"]) > 1e-9:
            raise Exp001Refused(f"{n} no longer reproduces its validation QLIKE")
    hist = val.iloc[-(cfg.context_bars - 1):]
    saved = pd.read_parquet(out / "predictions_validation.parquet")
    frame = part.open_holdout(ledger, h, a.reason)            # logs the access, once
    frame.to_parquet(out / "holdout_frame.parquet")           # keep it if scoring crashes
    preds = pd.DataFrame({n: b.predict(frame) for n, b in base.items()})
    preds["minimamba"] = ens.predict(frame, hist)
    res = score_all(preds[[m.name for m in spec.models if m.name in preds.columns]],
                    frame["target"], spec)
    half = len(val) // 2
    conf = {n: conformal_block(spec, saved[n].iloc[:half], saved["target"].iloc[:half],
                               preds[n], frame["target"]) for n in ("minimamba", "har")}
    preds.assign(target=frame["target"]).to_parquet(out / "predictions_holdout.parquet")
    result = {"experiment": STUDY, "stage": "holdout", "labels": LABELS, "spec_hash": h,
              "data_version": part.data_version, "n_holdout": len(frame),
              "data_label": read_provenance(a.candles)["label"], **res,
              "conformal": conf, "variants_tried": variants_for(ledger),
              "environment": environment(), "reason": a.reason.strip()}
    digest = _write(out / "holdout_results.json", result)
    ledger.append(KIND_SCORED, {"spec_hash": h, "results_sha256": digest,
                                "outcome_holdout": res["outcome"]}, part.data_version)
    return result
