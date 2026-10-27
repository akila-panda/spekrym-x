"""``sx-lab run | evaluate | search | report`` (Phase 7B). Validation split only: the holdout
is never opened here (it needs ``LabPartition.lock_evaluation`` / ``open_holdout``, Phase 8).

Example: python -m sx_lab.cli evaluate --candles tests/fixtures/lab/eurusd_h1_synth_1000.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from sx_core.config import load_settings
from sx_core.contracts import Candle
from sx_core.ledger import Ledger
from sx_core.storage import frame_to_candles, read_parquet
from sx_lab.baselines import HAR, Garch, GarchFitError, HistoricalMean, Persistence
from sx_lab.evaluation import metrics
from sx_lab.evaluation.negative_controls import leaked_feature_control, shuffled_label_control
from sx_lab.evaluation.purged_cv_crosscheck import crosscheck
from sx_lab.features import make_dataset
from sx_lab.partition import LabPartition
from sx_lab.records import make_forecasts
from sx_lab.search import SEARCH_WINDOWS, run_har_search, variants_tried

LABELS = "Exploratory · Not validated · Retrospective (validation split)"


def _load(path: str) -> list[Candle]:
    if path.endswith(".parquet"):
        return frame_to_candles(read_parquet(path))
    return [Candle.model_validate(r) for r in json.loads(Path(path).read_text())]


def _setup(a: argparse.Namespace) -> tuple[list[Candle], LabPartition, Ledger, Path]:
    candles = _load(a.candles)
    part = LabPartition(make_dataset(candles, a.horizon, SEARCH_WINDOWS), horizon=a.horizon)
    out = Path(a.out) / part.data_version.removeprefix("dv:")
    out.mkdir(parents=True, exist_ok=True)
    return candles, part, Ledger(a.ledger), out


def _factories(h: int) -> dict:
    return {"historical_mean": HistoricalMean, "persistence": lambda: Persistence(h),
            "har": HAR, "garch11": lambda: Garch(h)}


def cmd_run(a: argparse.Namespace) -> int:
    candles, part, ledger, out = _setup(a)
    train, val = part.train(), part.validation()
    models = {n: f().fit(train) for n, f in _factories(a.horizon).items()}
    preds = pd.DataFrame({n: m.predict(val) for n, m in models.items()})
    preds["target"] = val["target"]
    preds.to_parquet(out / "predictions.parquet")
    fc = make_forecasts(models["har"], models["historical_mean"], train, val,
                        instrument=candles[0].instrument, tf=candles[0].tf,
                        variants_tried=variants_tried(ledger)["trials"])
    (out / "forecasts_har.json").write_text(
        json.dumps([f.to_wire() for f in fc], indent=1) + "\n")
    print(f"wrote {out}/predictions.parquet and forecasts_har.json ({len(fc)} records)")
    print(LABELS)
    return 0


def cmd_evaluate(a: argparse.Namespace) -> int:
    candles, part, ledger, out = _setup(a)
    train, val = part.train(), part.validation()
    scores, errors = {}, {}
    for n, f in _factories(a.horizon).items():
        try:
            m = f().fit(train)
            scores[n] = metrics.score(m.predict(val), val["target"])
            if n == "har":
                scores[n]["n_floored"] = m.n_floored
        except GarchFitError as e:
            errors[n] = str(e)
    result: dict = {"labels": LABELS, "data_label": a.data_label, "horizon": a.horizon,
                    "n": {"train": len(train), "validation": len(val)},
                    "holdout": part.holdout_status(Ledger(a.ledger)), "scores": scores,
                    "errors": errors, "variants": variants_tried(ledger)}
    fac = {n: f for n, f in _factories(a.horizon).items() if n in scores}
    try:
        cc = crosscheck(fac, pd.concat([train, val]), {n: s["qlike"] for n, s in scores.items()},
                        purge=part.embargo)
        result["purged_cv"] = {"cv_mean_qlike": cc.cv_mean_qlike, "cv_order": cc.cv_order,
                               "validation_order": cc.validation_order, "agrees": cc.agrees}
    except GarchFitError as e:
        result["purged_cv"] = {"error": str(e)}
    ctr = [shuffled_label_control(HAR, train, val),
           leaked_feature_control(candles, a.horizon, SEARCH_WINDOWS)]
    result["controls"] = [{"name": c.name, "passed": c.passed, "detail": c.detail,
                           "values": c.values} for c in ctr]
    (out / "evaluation.json").write_text(json.dumps(result, indent=1) + "\n")
    _print(result)
    # a failed shuffled-label control is a finding; a failed leak guard is an integrity error
    return 0 if ctr[1].passed else 1


def cmd_search(a: argparse.Namespace) -> int:
    _, part, ledger, _ = _setup(a)
    r = run_har_search(part, ledger, study=a.study, n_trials=a.trials)
    v = variants_tried(ledger)
    print(f"best {r.best_params} validation QLIKE {r.best_value:.6f}")
    print(f"variants tried (ledger, all studies): {v['trials']} trials, {v['distinct']} distinct")
    print(LABELS)
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    _, _, ledger, out = _setup(a)
    path = out / "evaluation.json"
    if not path.exists():
        print(f"no evaluation at {path}; run `evaluate` first")
        return 1
    result = json.loads(path.read_text())
    result["variants"] = variants_tried(ledger)
    _print(result)
    return 0


def _print(r: dict) -> None:
    print(f"{r['labels']} | data: {r['data_label']} | horizon {r['horizon']} bars")
    print(f"rows: {r['n']} | holdout: {r['holdout']} | variants: {r['variants']}")
    for n, s in r["scores"].items():
        extra = f" floored={s['n_floored']}" if "n_floored" in s else ""
        print(f"  {n:16s} QLIKE {s['qlike']:.5f}  RMSE {s['rmse']:.3e}  n={s['n']}{extra}")
    for n, e in r["errors"].items():
        print(f"  {n:16s} FAILED: {e}")
    print(f"purged CV: {r.get('purged_cv')}")
    for c in r["controls"]:
        print(f"  control {c['name']}: {'PASS' if c['passed'] else 'FAIL'} - {c['detail']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sx-lab")
    ap.add_argument("command", choices=["run", "evaluate", "search", "report"])
    ap.add_argument("--candles", required=True, help=".json (Candle list) or .parquet")
    ap.add_argument("--horizon", type=int, default=24)
    ap.add_argument("--out", default="lab/outputs")
    ap.add_argument("--ledger", default="lab/outputs/ledger.jsonl")
    ap.add_argument("--dotenv", default=str(Path.cwd() / ".env"))
    ap.add_argument("--data-label", default="SAMPLE DATA — NOT LIVE")
    ap.add_argument("--study", default="har_windows")
    ap.add_argument("--trials", type=int, default=12)
    a = ap.parse_args(argv)
    load_settings(dotenv_path=a.dotenv)  # paper-mode guard: refuses to start unless paper
    return {"run": cmd_run, "evaluate": cmd_evaluate, "search": cmd_search,
            "report": cmd_report}[a.command](a)


if __name__ == "__main__":
    raise SystemExit(main())
