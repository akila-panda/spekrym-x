"""Write ``EXP-001_mamba_vs_har.md`` from the stage JSON files (8B). No number is typed by hand."""

from __future__ import annotations

import json
from pathlib import Path

HEAD = """# EXP-001: MiniMamba vs HAR and GARCH(1,1), H1 EUR/USD volatility

Labels: **Exploratory | Not validated | Retrospective**. This is an evaluation on one
instrument and one period. It is not a trading signal and makes no profit claim.
"""

NOTES = """## What was decided outside the locked spec (read before trusting this)
- **L21** Training hyperparameters were not in the spec; they were fixed in code before any
  validation score was seen and never tuned: {epochs} epochs, batch {batch_size}, AdamW lr {lr},
  weight decay {weight_decay}, gradient clip {grad_clip}, QLIKE training loss, no early
  stopping, no dropout.
- **L21** "MiniMamba" is the mean of the log-variance forecasts of seeds 1, 2, 3 (no seed
  selection). Per-seed scores are diagnostics only.
- **L22** The spec does not say whether win/tie/loss is judged on validation or holdout. This
  report states both; the headline is the HOLDOUT outcome once it exists, because validation
  was scored first and the holdout is the untouched sample.
- Rows without a full 48-bar context use earlier rows' features as history (train tail for
  validation, validation tail for the holdout); the frame is compacted across market gaps.
- Split-conformal intervals assume exchangeability, which volatility does not satisfy, so
  measured coverage is reported, never assumed.
"""


def _table(res: dict) -> list[str]:
    inc = set(res["mcs"]["included"])
    rows = ["| model | QLIKE | RMSE | in MCS | MCS p-value |", "|---|---|---|---|---|"]
    for n, s in sorted(res["scores"].items(), key=lambda kv: kv[1]["qlike"]):
        pv = res["mcs"]["pvalues"].get(n)
        mark = "yes" if n in inc else "no"
        p = "-" if pv is None else f"{pv:.3f}"
        rows.append(f"| {n} | {s['qlike']:.5f} | {s['rmse']:.3e} | {mark} | {p} |")
    return rows


def _stage(title: str, res: dict, n_key: str) -> list[str]:
    k = res["mcs"]
    out = [f"## {title} (n = {res[n_key]})", "", *_table(res), "",
           f"Model confidence set: level {k['level']}, {k['reps']} reps, block {k['block_size']}, "
           f"seed {k['seed']}. Included: {', '.join(k['included'])}. "
           f"Excluded: {', '.join(k['excluded']) or 'none'}.", "",
           f"**Outcome ({res['stage']}): {res['outcome'].upper()}**", "",
           "Interval coverage (split-conformal, nominal 0.80):", ""]
    for n, c in res["conformal"].items():
        wr = c["worst_rolling_50"]
        out.append(f"- {n}: measured {c['empirical']:.3f} on {c['n']} rows "
                   f"(calibrated on {c['n_calibration']}; worst rolling-50 "
                   f"{'n/a' if wr is None else f'{wr:.2f}'}; mean width ratio "
                   f"{c['mean_width_ratio']:.2f})")
    return [*out, ""]


def build_report(out_dir: str | Path) -> str:
    d = Path(out_dir)
    val = json.loads((d / "validation_results.json").read_text())
    hp = d / "holdout_results.json"
    hold = json.loads(hp.read_text()) if hp.exists() else None
    head = hold["outcome"].upper() if hold else "PENDING (holdout not opened yet)"
    lines = [HEAD, f"Spec hash `{val['spec_hash']}`, data `{val['data_version']}`, "
             f"label: **{val['data_label']}**.", "",
             f"## Result: {head}", ""]
    if hold:
        lines += [f"Judged on the holdout (L22). Validation outcome: {val['outcome'].upper()}.", ""]
    lines += _stage("Validation", val, "n_validation")
    if hold:
        lines += _stage("Holdout (opened once)", hold, "n_holdout")
    lines += ["## Variants tried", "",
              f"{(hold or val)['variants_tried']} logged trials for EXP-001 (cap in spec: 20).",
              "Per-seed validation QLIKE (diagnostic only): "
              + ", ".join(f"{k} {v:.5f}" for k, v in val["per_seed_qlike_diagnostic"].items()),
              "", NOTES.format(**val["train_config"]), "## Environment", "",
              "`" + json.dumps(val["environment"]) + "`", ""]
    return "\n".join(lines)
