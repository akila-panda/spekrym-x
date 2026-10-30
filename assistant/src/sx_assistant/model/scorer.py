"""Score + reasons. A SCORE IS A RANK against reference scores, never a probability.

``rank_score`` (0 to 100) = share of reference setups (the validation-period scores, saved with
the model) whose raw score is not above this one. Every score carries reasons and the honesty
labels; ``ScoredSetup`` refuses to exist without them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from sx_assistant.model.explain_shap import ShapReasons, reason_text
from sx_assistant.model.train_lgbm import margin, model_hash

LABELS = ("Exploratory", "Not validated", "Retrospective")
SCORE_NOTE = ("Rank against validation-period scores. A ranking only; it says nothing about "
              "how often a setup works. Exploratory, not validated.")


@dataclass(frozen=True)
class Reason:
    feature: str
    value: float
    contribution: float
    text: str


@dataclass(frozen=True)
class ScoredSetup:
    setup_id: str
    rank_score: float
    raw_margin: float
    reasons: tuple[Reason, ...]
    labels: tuple[str, ...]
    model_version: str
    note: str = SCORE_NOTE

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("a score must carry at least one reason")
        if not set(LABELS) <= set(self.labels):
            raise ValueError(f"a score must carry the labels {LABELS}")
        if not 0.0 <= self.rank_score <= 100.0:
            raise ValueError("rank_score outside 0..100")


class Scorer:
    def __init__(self, model: lgb.Booster, reference_margins: np.ndarray, top_k: int = 3):
        if len(reference_margins) < 50:
            raise ValueError("need at least 50 reference scores")
        self.model, self.top_k = model, top_k
        self.reference = np.sort(np.asarray(reference_margins, float))
        self.version = "m:" + model_hash(model)[:12]
        self._shap = ShapReasons(model)

    def score(self, X: pd.DataFrame, setup_ids: list[str]) -> list[ScoredSetup]:
        if len(X) != len(setup_ids):
            raise ValueError("one setup id per row")
        marg = margin(self.model, X)
        contrib, _ = self._shap.contributions(X)
        names = self.model.feature_name()
        out = []
        for r in range(len(X)):
            rank = 100.0 * np.searchsorted(self.reference, marg[r], side="right") \
                / len(self.reference)
            order = np.argsort(-np.abs(contrib[r]), kind="stable")[:self.top_k]
            reasons = tuple(Reason(names[j], float(X.iloc[r][names[j]]), float(contrib[r, j]),
                                   reason_text(names[j], float(X.iloc[r][names[j]]),
                                               float(contrib[r, j]))) for j in order)
            out.append(ScoredSetup(setup_ids[r], float(rank), float(marg[r]), reasons, LABELS,
                                   self.version))
        return out

    def save(self, directory: str | Path) -> str:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        self.model.save_model(str(d / "scorer.lgb"))
        (d / "scorer_reference.json").write_text(json.dumps(self.reference.tolist()))
        return model_hash(self.model)

    @classmethod
    def load(cls, directory: str | Path, expect_hash: str | None = None) -> Scorer:
        d = Path(directory)
        model = lgb.Booster(model_file=str(d / "scorer.lgb"))
        if expect_hash is not None and model_hash(model) != expect_hash:
            raise ValueError("saved model does not match the locked hash")
        ref = np.array(json.loads((d / "scorer_reference.json").read_text()), float)
        return cls(model, ref)
