"""EXP-001 shared pieces (8B): guards, pin check, scoring, outcome rule. No training here."""

from __future__ import annotations

import argparse
import importlib.metadata as md
import platform
import re
import sys

import numpy as np
import pandas as pd

from sx_core.ledger import Ledger
from sx_lab.baselines import HAR, Garch, HistoricalMean, Persistence
from sx_lab.calibration.conformal import SplitConformal, coverage_report
from sx_lab.cli_experiment import _verified
from sx_lab.evaluation import metrics
from sx_lab.evaluation.model_confidence_set import model_confidence_set, qlike_loss_frame
from sx_lab.spec import ExperimentSpec

STUDY = "EXP-001"
SEEDS = (1, 2, 3)                       # locked stopping_rule: "(seeds 1, 2, 3)"
KIND_VALIDATED = "lab.exp001.validated"
KIND_SCORED = "lab.exp001.holdout_scored"
LABELS = "Exploratory | Not validated | Retrospective"


class Exp001Refused(RuntimeError):
    pass


def classify(included: tuple[str, ...]) -> str:
    """Locked outcome rules: win / tie / loss / inconclusive (the last covers every gap)."""
    mm, har, gar = "minimamba" in included, "har" in included, "garch11" in included
    if mm and not har and not gar:
        return "win"
    if mm:
        return "tie"
    return "loss" if (har or gar) else "inconclusive"


def check_pins(spec: ExperimentSpec) -> dict[str, str]:
    """Installed versions must match every ``name==version`` pin written in the spec."""
    seen = {}
    for m in spec.models:
        for name, want in re.findall(r"([A-Za-z][\w-]*)==([\d.]+)", m.pin or ""):
            have = md.version(name)
            if not have.startswith(want):
                raise Exp001Refused(f"{name} {have} installed but the spec pins {want}")
            seen[name] = have
    return seen


def environment() -> dict[str, str]:
    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    for n in ("torch", "minimamba", "arch", "numpy", "pandas", "statsmodels"):
        out[n] = md.version(n)
    return out


def prepare(a: argparse.Namespace):
    spec, h, part, ledger = _verified(a)
    ledger.verify()
    locks = [e for e in ledger.read() if e.kind == "lab.evaluation_locked"]
    if not locks or locks[-1].payload["spec_hash"] != h:
        raise Exp001Refused("the ledger has no lock for this exact spec hash; run sx-lab lock")
    m = next(x for x in spec.models if x.name == "minimamba")
    if m.settings.get("use_fast_path", False):
        raise Exp001Refused("spec asks for use_fast_path; only the CPU path is supported")
    return spec, h, part, ledger


def make_baselines(spec: ExperimentSpec, train: pd.DataFrame) -> dict:
    fac = {"historical_mean": HistoricalMean, "persistence": lambda: Persistence(spec.horizon_bars),
           "har": HAR, "garch11": lambda: Garch(spec.horizon_bars)}
    return {m.name: fac[m.name]().fit(train) for m in spec.models if m.name in fac}


def score_all(preds: pd.DataFrame, target: pd.Series, spec: ExperimentSpec) -> dict:
    scores = {c: metrics.score(preds[c], target) for c in preds.columns}
    k = spec.mcs
    res = model_confidence_set(qlike_loss_frame(preds, target), horizon=spec.horizon_bars,
                               level=k.level, reps=k.reps, block_size=k.block_size, seed=k.seed,
                               method=k.method)
    return {"scores": scores,
            "mcs": {"level": res.level, "included": list(res.included),
                    "excluded": list(res.excluded), "pvalues": res.pvalues, "n": res.n,
                    "block_size": res.block_size, "reps": res.reps, "seed": res.seed},
            "outcome": classify(res.included)}


def conformal_block(spec: ExperimentSpec, cal_f, cal_y, ev_f, ev_y) -> dict:
    conf = SplitConformal(alpha=spec.conformal.alpha).calibrate(cal_f, cal_y)
    lo, hi = conf.interval(np.asarray(ev_f, dtype="float64"))
    cov = coverage_report(lo, hi, ev_f, ev_y, nominal=conf.nominal)
    return {"nominal": cov.nominal, "empirical": cov.empirical, "n": cov.n,
            "n_calibration": conf.n_calibration, "worst_rolling_50": cov.worst_rolling,
            "mean_width_ratio": cov.mean_width_ratio,
            "caveat": "split-conformal needs exchangeability; not guaranteed for volatility"}


def variants_for(ledger: Ledger) -> int:
    return sum(1 for e in ledger.read()
               if e.kind == "lab.trial" and e.payload.get("study") == STUDY)
