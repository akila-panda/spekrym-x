"""SHAP reasons through an adapter. Verified on shap 0.54.1 + lightgbm 4.7.0 (binary booster):
``TreeExplainer.shap_values`` returns an (n, features) array on the raw-margin scale and
base + sum(contributions) equals the booster's raw score. The adapter re-checks that on every
call and raises if it does not hold, instead of trusting the library.
"""

from __future__ import annotations

import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap

from sx_assistant.model.features import FEATURE_TEXT


class ShapReasons:
    def __init__(self, model: lgb.Booster):
        self._model = model
        self._ex = shap.TreeExplainer(model)

    def contributions(self, X: pd.DataFrame) -> tuple[np.ndarray, float]:
        arr = X[self._model.feature_name()].to_numpy(float)
        with warnings.catch_warnings():  # shap 0.54.1 warns about a list that it does not return
            warnings.filterwarnings("ignore", message="LightGBM binary classifier")
            sv = self._ex.shap_values(arr, check_additivity=False)
        if isinstance(sv, list):  # older shap versions return one array per class
            sv = sv[-1]
        sv = np.asarray(sv)
        base = float(np.ravel(self._ex.expected_value)[-1])
        if sv.shape != arr.shape:
            raise RuntimeError(f"unexpected SHAP shape {sv.shape} for input {arr.shape}")
        raw = np.asarray(self._model.predict(arr, raw_score=True))
        if not np.allclose(base + sv.sum(axis=1), raw, atol=1e-4):
            raise RuntimeError("SHAP additivity failed: contributions do not sum to the score")
        return sv, base


def reason_text(feature: str, value: float, contribution: float) -> str:
    what = FEATURE_TEXT.get(feature, feature)
    way = "raised" if contribution > 0 else "lowered"
    return f"{what} = {value:.3g} {way} the ranking score"
