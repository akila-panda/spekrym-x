"""Two-regime Markov switching on log realized variance, FILTERED probabilities only (8A).

Causality is the whole point, so the design is narrow:
  * ``fit`` estimates the parameters on the TRAINING series only.
  * ``filtered`` runs the fixed parameters over any later series with
    ``MarkovRegression.filter(params)``. A filtered probability at t uses observations <= t.
    Smoothed probabilities (which use the future) are never returned.
  * Fitting on a series and reading its probabilities would leak through the parameters, so a
    series passed to ``filtered`` is never used to change them.
Facts checked by running statsmodels 0.15.0 (not just read): ``MarkovRegressionResults`` has no
``apply``; ``MarkovRegression(new_endog).filter(params)`` gives filtered marginal probabilities
that match on every prefix (tested with the Phase 2 harness). Start values are derived
deterministically from the data (no global RNG), and a non-converged fit raises.
Labels: regime 1 is the one with the higher mean of the series ("high"). Status: Exploratory.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

STATUS = "exploratory"


class RegimeFitError(RuntimeError):
    pass


def _model(y: pd.Series) -> MarkovRegression:
    return MarkovRegression(y, k_regimes=2, trend="c", switching_variance=True)


@dataclass(frozen=True)
class RegimeModel:
    params: np.ndarray
    names: tuple[str, ...]
    high_is: int          # index (0 or 1) of the high-mean regime in the library's ordering

    @classmethod
    def fit(cls, train: pd.Series) -> RegimeModel:
        y = pd.Series(train, dtype="float64")
        if len(y) < 100 or not np.isfinite(y).all():
            raise RegimeFitError("need at least 100 finite training observations")
        med = y.median()
        lo, hi = y[y <= med], y[y > med]
        start = np.array([0.95, 0.05, lo.mean(), hi.mean(), lo.var(), hi.var()])
        m = _model(y)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = m.fit(start_params=start, disp=False)
        if not res.mle_retvals.get("converged", False):
            raise RegimeFitError("optimizer did not converge")
        p = np.asarray(res.params, dtype="float64")
        if not np.isfinite(p).all():
            raise RegimeFitError("non-finite parameters")
        return cls(p, tuple(m.param_names), int(p[3] > p[2]))

    def filtered(self, series: pd.Series) -> pd.DataFrame:
        """Columns ``p_low`` and ``p_high``, same index as ``series``. Uses data <= t only."""
        y = pd.Series(series, dtype="float64")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = _model(y).filter(self.params)
        fp = np.asarray(out.filtered_marginal_probabilities)
        high = fp[:, self.high_is]
        return pd.DataFrame({"p_low": 1.0 - high, "p_high": high}, index=y.index)
