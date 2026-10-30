"""LightGBM adapter (native ``lgb.train``, one thread, deterministic) and ranking metrics.

Nothing here is a probability: the booster's raw margin is only used to RANK setups. Metrics are
rank-based (AUC) plus the share of historical setups whose target barrier came first among the
top-scored fifth, always with counts.
"""

from __future__ import annotations

import hashlib

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import rankdata

BASE = {"objective": "binary", "learning_rate": 0.05, "feature_fraction": 1.0,
        "bagging_fraction": 1.0, "deterministic": True, "force_row_wise": True,
        "num_threads": 1, "verbosity": -1}


def fit(X: pd.DataFrame, y: np.ndarray, params: dict, seed: int) -> lgb.Booster:
    p = {**BASE, **{k: v for k, v in params.items() if k != "num_boost_round"}, "seed": seed}
    return lgb.train(p, lgb.Dataset(X.to_numpy(float), np.asarray(y, int),
                                    feature_name=list(X.columns)),
                     num_boost_round=int(params["num_boost_round"]))


def margin(model: lgb.Booster, X: pd.DataFrame) -> np.ndarray:
    """Raw score (log-odds scale) used ONLY for ranking."""
    return np.asarray(model.predict(X[model.feature_name()].to_numpy(float), raw_score=True))


def auc(y: np.ndarray, s: np.ndarray) -> float:
    """Rank AUC (ties averaged). NaN when only one class is present."""
    y = np.asarray(y, int)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def rank_metrics(y: np.ndarray, s: np.ndarray, seed: int = 0, n_boot: int = 200) -> dict:
    y, s = np.asarray(y, int), np.asarray(s, float)
    k = max(1, len(y) // 5)
    top = np.argsort(-s, kind="stable")[:k]
    rng = np.random.default_rng(seed)
    boots = [auc(y[i], s[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(n_boot))]
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return {"n": int(len(y)), "target_first_share_all": float(y.mean()),
            "auc": auc(y, s), "auc_ci95_iid": [float(lo), float(hi)],
            "top_fifth_n": int(k), "top_fifth_target_first_share": float(y[top].mean()),
            "note": "CI assumes independent rows; overlapping label windows make it optimistic"}


def model_hash(model: lgb.Booster) -> str:
    return hashlib.sha256(model.model_to_string().encode()).hexdigest()
