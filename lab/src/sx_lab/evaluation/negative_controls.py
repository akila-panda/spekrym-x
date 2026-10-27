"""Negative controls (Phase 7B). ``passed`` means the control did what a control must do, not that
a model is good. A FAILED shuffled-label control means "no measurable skill here", which is an
honest and expected outcome on small or noisy splits.

1. Shuffled labels: a model refitted on permuted training labels must lose to the honest fit.
2. Leaked feature: a deliberately look-ahead feature must be flagged by the prefix-equality
   guard, and the real features must not be flagged.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from sx_core.contracts import Candle
from sx_lab.baselines.base import Baseline
from sx_lab.evaluation.metrics import qlike
from sx_lab.features import build_features, forward_target

Builder = Callable[[Sequence[Candle]], pd.DataFrame]


@dataclass(frozen=True)
class ControlResult:
    name: str
    passed: bool
    detail: str
    values: dict[str, float | list[str]] = field(default_factory=dict)


def shuffled_label_control(make_baseline: Callable[[], Baseline], train: pd.DataFrame,
                           val: pd.DataFrame, *, seed: int = 0, n_shuffles: int = 20
                           ) -> ControlResult:
    honest = qlike(make_baseline().fit(train).predict(val), val["target"])
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n_shuffles):
        shuf = train.copy()
        shuf["target"] = rng.permutation(train["target"].to_numpy())
        scores.append(qlike(make_baseline().fit(shuf).predict(val), val["target"]))
    med = float(np.median(scores))
    vals: dict[str, float | list[str]] = {"honest_qlike": honest, "shuffled_median_qlike": med}
    if all(abs(s - honest) < 1e-12 for s in scores):
        return ControlResult("shuffled_labels", False,
                             "model ignores training labels; control is uninformative", vals)
    ok = med > honest
    return ControlResult("shuffled_labels", ok,
                         "shuffled-label fit is worse than honest" if ok else
                         "shuffled-label fit is NOT worse: the model shows no measurable skill "
                         "on this split (or the pipeline is suspect); do not read it as skill",
                         vals)


def find_noncausal_columns(builder: Builder, candles: Sequence[Candle],
                           lengths: Sequence[int]) -> list[str]:
    """Columns whose value at an early row changes when later candles are added."""
    full = builder(candles)
    bad: set[str] = set()
    for n in lengths:
        part = builder(candles[:n])
        for col in full.columns:
            if col in part.columns and not part[col].equals(full[col].iloc[:n]):
                bad.add(col)
            elif col not in part.columns:
                bad.add(col)
    return sorted(bad)


def real_builder(horizon: int, windows: Sequence[int]) -> Builder:
    return lambda c: build_features(c, windows)


def leaked_builder(horizon: int, windows: Sequence[int]) -> Builder:
    """Deliberately wrong: adds the future target as a 'feature'."""
    def build(c: Sequence[Candle]) -> pd.DataFrame:
        leak = forward_target(c, horizon)["target"].rename("leak")
        return build_features(c, windows).join(leak)
    return build


def leaked_feature_control(candles: Sequence[Candle], horizon: int, windows: Sequence[int],
                           lengths: Sequence[int] = (200, 300, 400)) -> ControlResult:
    clean = find_noncausal_columns(real_builder(horizon, windows), candles, lengths)
    flagged = find_noncausal_columns(leaked_builder(horizon, windows), candles, lengths)
    ok = clean == [] and flagged == ["leak"]
    return ControlResult("leaked_feature", ok,
                         "guard flagged only the leaked column" if ok else
                         "guard FAILED: real columns flagged or leak missed",
                         {"real_flagged": clean, "leaked_flagged": flagged})
