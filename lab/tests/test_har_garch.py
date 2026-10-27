import numpy as np
import pandas as pd
import pytest
from arch import arch_model

from sx_lab.baselines import HAR, Garch, NotFittedError
from sx_lab.baselines.garch import SCALE, horizon_mean
from sx_lab.partition import LabPartition
from lab_fixtures import _dataset  # noqa: F401


def _har_frame(n=300, seed=1):
    rng = np.random.default_rng(seed)
    f = pd.DataFrame({c: rng.uniform(1e-7, 1e-6, n) for c in ("rv_6", "rv_24", "rv_120")})
    f["target"] = 1e-8 + 0.5 * f["rv_6"] + 0.3 * f["rv_24"] + 0.2 * f["rv_120"]
    return f


def test_har_recovers_exact_coefficients():
    f = _har_frame()
    har = HAR().fit(f)
    assert har.coef == pytest.approx([1e-8, 0.5, 0.3, 0.2], rel=1e-6)
    assert har.predict(f).to_numpy() == pytest.approx(f["target"].to_numpy(), rel=1e-6)
    assert har.n_floored == 0


def test_har_floors_and_counts_nonpositive_predictions():
    f = _har_frame()
    har = HAR().fit(f)
    weird = f.copy()
    weird[["rv_6", "rv_24", "rv_120"]] = -1.0
    pred = har.predict(weird)
    assert har.n_floored == len(weird) and (pred >= har.floor).all() and (pred > 0).all()


def test_har_errors():
    with pytest.raises(NotFittedError):
        HAR().predict(_har_frame())
    with pytest.raises(KeyError):
        HAR(("rv_6", "nope")).fit(_har_frame())


def test_horizon_mean_limits():
    s = np.array([2.0, 5.0])
    assert horizon_mean(s, 0.1, 0.2, 0.3, 1) == pytest.approx(s)
    far = horizon_mean(s, 0.1, 0.2, 0.3, 10**7)
    assert far == pytest.approx(0.1 / 0.5 * np.ones(2), rel=1e-5)


def test_garch_matches_arch_own_forecast(dataset):
    """Our recursion with fixed parameters equals arch's forecast (mean over 1..h steps)."""
    train = LabPartition(dataset, horizon=24).train()
    g = Garch(24).fit(train)
    am = arch_model(train["ret"] * SCALE, mean="Zero", vol="GARCH", p=1, q=1, rescale=False)
    res = am.fix([g.omega, g.alpha, g.beta])
    fc = res.forecast(horizon=24, start=200, method="analytic", reindex=False).variance
    theirs = fc.mean(axis=1).to_numpy() / SCALE**2
    ours = g.predict(train).to_numpy()[200:]
    assert len(theirs) == len(ours)
    assert ours == pytest.approx(theirs, rel=1e-6)


def test_garch_prediction_is_causal(dataset):
    val = LabPartition(dataset, horizon=24)
    g = Garch(24).fit(val.train())
    f = val.validation()
    base = g.predict(f)
    changed = f.copy()
    changed.iloc[100:, changed.columns.get_loc("ret")] *= 5
    after = g.predict(changed)
    assert (after.iloc[:100] == base.iloc[:100]).all()
    assert not (after.iloc[100:] == base.iloc[100:]).all()
