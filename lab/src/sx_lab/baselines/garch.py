"""GARCH(1,1) baseline (Phase 7B). ``arch`` is used for parameter ESTIMATION only.

Forecasts come from our own recursion with the fitted, fixed parameters, so no library
forecasting behaviour is assumed. A test cross-checks the recursion against
``arch``'s own ``forecast`` (the one-step and multi-step values match).

Returns are scaled by 100 for the optimiser (arch advises this) and variances are scaled back.
State ``s_t`` is the conditional variance of bar t+1 given bars <= t:
``s_t = omega + alpha * r_t^2 + beta * s_{t-1}``; it is started from the causal feature ``rv_120``
of the first row, so no future data and no hidden pre-sample enters.
"""

from __future__ import annotations

from typing import Self

import numpy as np
import pandas as pd
from arch import arch_model

from sx_lab.baselines.naive import NotFittedError

SCALE = 100.0


class GarchFitError(RuntimeError):
    pass


def horizon_mean(state: np.ndarray, omega: float, alpha: float, beta: float, h: int
                 ) -> np.ndarray:
    """Mean of the analytic variance forecasts for steps 1..h ahead, given one-step ``state``."""
    p = alpha + beta
    v = omega / (1.0 - p)
    return v + (state - v) * (1.0 - p ** h) / (h * (1.0 - p))


class Garch:
    name = "garch11"

    def __init__(self, horizon: int):
        self.horizon = horizon
        self.omega = self.alpha = self.beta = None  # type: ignore[assignment]

    def fit(self, train: pd.DataFrame) -> Self:
        am = arch_model(train["ret"] * SCALE, mean="Zero", vol="GARCH", p=1, q=1,
                        rescale=False)
        res = am.fit(disp="off")
        if res.convergence_flag != 0:
            raise GarchFitError(f"optimiser did not converge (flag {res.convergence_flag})")
        w, a, b = (float(res.params[k]) for k in ("omega", "alpha[1]", "beta[1]"))
        if not (w > 0 and a >= 0 and b >= 0 and a + b < 1):
            raise GarchFitError(f"fit is not stationary: omega={w}, alpha={a}, beta={b}")
        self.omega, self.alpha, self.beta = w, a, b
        return self

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        if self.omega is None:
            raise NotFittedError("call fit() first")
        r2 = (frame["ret"].to_numpy(dtype="float64") * SCALE) ** 2
        s = float(frame["rv_120"].iloc[0]) * SCALE**2
        states = np.empty(len(r2))
        for i, x in enumerate(r2):
            s = self.omega + self.alpha * x + self.beta * s
            states[i] = s
        fc = horizon_mean(states, self.omega, self.alpha, self.beta, self.horizon) / SCALE**2
        return pd.Series(fc, index=frame.index, name=self.name)

    def params(self) -> dict[str, object]:
        if self.omega is None:
            raise NotFittedError("call fit() first")
        return {"omega": self.omega, "alpha": self.alpha, "beta": self.beta,
                "horizon": self.horizon}
