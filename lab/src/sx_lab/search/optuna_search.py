"""Optuna search over HAR lookback choices (Phase 7B). EVERY trial is written to the ledger.

The objective sees ``partition.train()`` and ``partition.validation()`` only. The holdout is
never reachable from here. ``variants_tried`` counts ledger trial entries (repeats included),
so the count cannot be lowered by tidying up the study.
"""

from __future__ import annotations

from dataclasses import dataclass

import optuna

from sx_core.ledger import Ledger
from sx_lab.baselines.har import HAR
from sx_lab.evaluation.metrics import qlike
from sx_lab.partition import LabPartition

SEARCH_WINDOWS = (3, 6, 12, 24, 72, 120)
SHORT, LONG = (3, 6, 12), (72, 120)
KIND_TRIAL = "lab.trial"


@dataclass(frozen=True)
class SearchResult:
    best_params: dict[str, int]
    best_value: float
    n_trials: int


def variants_tried(ledger: Ledger, study: str | None = None) -> dict[str, int]:
    trials = [e.payload for e in ledger.read() if e.kind == KIND_TRIAL
              and (study is None or e.payload.get("study") == study)]
    distinct = {tuple(sorted(t["params"].items())) for t in trials}
    return {"trials": len(trials), "distinct": len(distinct)}


def run_har_search(partition: LabPartition, ledger: Ledger, *, study: str, n_trials: int,
                   seed: int = 0) -> SearchResult:
    train, val = partition.train(), partition.validation()

    def objective(trial: optuna.Trial) -> float:
        params = {"short": trial.suggest_categorical("short", list(SHORT)),
                  "long": trial.suggest_categorical("long", list(LONG))}
        cols = (f"rv_{params['short']}", "rv_24", f"rv_{params['long']}")
        value = qlike(HAR(cols).fit(train).predict(val), val["target"])
        ledger.append(KIND_TRIAL, {"study": study, "number": trial.number, "params": params,
                                   "value": value, "split": "validation"},
                      partition.data_version)
        return value

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    st = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    st.optimize(objective, n_trials=n_trials)
    return SearchResult(dict(st.best_params), float(st.best_value), len(st.trials))
