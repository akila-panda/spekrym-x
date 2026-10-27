"""Purged k-fold cross-check (Phase 7B) on train + validation rows only (never the holdout).

Contiguous time blocks are the test folds; training rows within ``purge`` rows of a test block
(both sides) are removed so overlapping target windows cannot leak. This is a CROSS-CHECK of
the single validation split: it asks whether the ordering of models agrees, nothing more.
Models are refitted on stitched (non-contiguous) training rows; for GARCH this distorts the
recursion at the joins (known issue L-8).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import numpy as np
import pandas as pd

from sx_lab.baselines.base import Baseline
from sx_lab.evaluation.metrics import qlike


def purged_kfold(n: int, k: int, purge: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    if k < 2 or n < 2 * k or purge < 0:
        raise ValueError("need k >= 2, n >= 2k and purge >= 0")
    edges = np.linspace(0, n, k + 1).astype(int)
    idx = np.arange(n)
    for a, b in zip(edges[:-1], edges[1:], strict=True):
        test = idx[a:b]
        train = idx[(idx < a - purge) | (idx >= b + purge)]
        if len(train) == 0:
            raise ValueError("purge removed every training row")
        yield train, test


def purged_cv_scores(make_baseline: Callable[[], Baseline], frame: pd.DataFrame, *, k: int = 5,
                     purge: int = 24) -> list[float]:
    out = []
    for tr, te in purged_kfold(len(frame), k, purge):
        model = make_baseline().fit(frame.iloc[tr])
        test = frame.iloc[te]
        out.append(qlike(model.predict(test), test["target"]))
    return out


@dataclass(frozen=True)
class CrossCheck:
    cv_mean_qlike: dict[str, float]
    validation_qlike: dict[str, float]
    cv_order: list[str]
    validation_order: list[str]

    @property
    def agrees(self) -> bool:
        return self.cv_order == self.validation_order


def crosscheck(factories: dict[str, Callable[[], Baseline]], frame: pd.DataFrame,
               validation_qlike: dict[str, float], *, k: int = 5, purge: int = 24
               ) -> CrossCheck:
    cv = {n: float(np.mean(purged_cv_scores(f, frame, k=k, purge=purge)))
          for n, f in factories.items()}
    return CrossCheck(cv, dict(validation_qlike), sorted(cv, key=cv.__getitem__),
                      sorted(validation_qlike, key=validation_qlike.__getitem__))
