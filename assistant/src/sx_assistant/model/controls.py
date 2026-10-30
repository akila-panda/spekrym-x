"""Negative controls. They must behave like this, or the pipeline is not trustworthy:

* SHUFFLED LABELS: training labels are permuted ``n_shuffles`` times; the scorer must show no
  skill (mean AUC near 0.5). Each shuffle repeats the SAME model selection (best of the grid on
  the evaluated rows), so the range already includes the luck of picking the best variant. A
  real result only counts as skill if it beats that range.
* LEAKED FEATURE: a feature that contains the future (``fwd_ret_atr``) is added; the scorer must
  look excellent AND ``leak_scan`` must flag it, while the real feature set is not flagged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sx_assistant.model.train_lgbm import auc, fit, margin

LEAK_THRESHOLD = 0.85  # single-feature AUC above this is treated as a suspected leak


def shuffled_control(train: pd.DataFrame, evalf: pd.DataFrame, features: list[str],
                     grid: list[dict] | tuple[dict, ...], n: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    aucs = []
    for k in range(n):
        y = rng.permutation(train["label"].to_numpy())
        aucs.append(max(auc(evalf["label"].to_numpy(),
                            margin(fit(train[features], y, p, seed + k), evalf[features]))
                        for p in grid))  # best-of-grid, as the real selection did
    a = np.array(aucs)
    return {"n_shuffles": n, "grid_size": len(grid), "auc_mean": float(np.nanmean(a)),
            "auc_p95": float(np.nanpercentile(a, 95)), "auc_max": float(np.nanmax(a)),
            "behaves_as_expected": bool(abs(np.nanmean(a) - 0.5) < 0.07)}


def leak_scan(frame: pd.DataFrame, features: list[str]) -> list[str]:
    """Features that alone rank the labels suspiciously well (either direction)."""
    y = frame["label"].to_numpy()
    out = []
    for f in features:
        a = auc(y, frame[f].fillna(0).to_numpy(float))
        if np.isfinite(a) and max(a, 1 - a) > LEAK_THRESHOLD:
            out.append(f)
    return out


def leaked_feature_control(train: pd.DataFrame, evalf: pd.DataFrame, features: list[str],
                           params: dict, seed: int) -> dict:
    leak = "LEAK_fwd_ret_atr"
    tr = train.assign(**{leak: train["fwd_ret_atr"]})
    ev = evalf.assign(**{leak: evalf["fwd_ret_atr"]})
    feats = [*features, leak]
    a = auc(ev["label"].to_numpy(), margin(fit(tr[feats], tr["label"].to_numpy(), params, seed),
                                           ev[feats]))
    flagged_with, flagged_real = leak_scan(ev, feats), leak_scan(ev, features)
    return {"leaked_auc": a, "flagged_with_leak": flagged_with,
            "flagged_real_features": flagged_real,
            "behaves_as_expected": bool(a > 0.8 and leak in flagged_with and not flagged_real)}
