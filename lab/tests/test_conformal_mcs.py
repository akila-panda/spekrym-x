import numpy as np
import pandas as pd
import pytest

from sx_lab.calibration.conformal import ConformalError, SplitConformal, coverage_report
from sx_lab.evaluation.model_confidence_set import (McsError, model_confidence_set,
                                                    qlike_loss_frame)


def test_quantile_ranks_hand_computed():
    # n=19, alpha=0.2: k_lo=floor(20*0.1)=2, k_hi=ceil(20*0.9)=18 -> 2nd and 18th smallest
    y = np.exp(np.arange(1, 20) / 10)                    # scores ln(y/f) = 0.1 .. 1.9
    c = SplitConformal(0.2).calibrate(np.ones(19), y)
    assert c.q_lo == pytest.approx(0.2) and c.q_hi == pytest.approx(1.8)
    lo, hi = c.interval([2.0])
    assert lo[0] == pytest.approx(2 * np.exp(0.2)) and hi[0] == pytest.approx(2 * np.exp(1.8))


def test_too_few_rows_refused():
    with pytest.raises(ConformalError, match="too few"):
        SplitConformal(0.2).calibrate(np.ones(8), np.ones(8))
    with pytest.raises(ConformalError):
        SplitConformal(0.2).interval([1.0])              # not calibrated
    with pytest.raises(ConformalError):
        SplitConformal(0.2).calibrate([1.0, -1.0] * 10, [1.0] * 20)


def _draw(rng, n, sigma=0.4):
    f = rng.uniform(0.5, 2.0, n)
    return f, f * np.exp(rng.normal(0, sigma, n))


def test_coverage_holds_on_exchangeable_data():
    rng = np.random.default_rng(7)
    covs = []
    for _ in range(60):
        c = SplitConformal(0.2).calibrate(*_draw(rng, 200))
        f, y = _draw(rng, 400)
        lo, hi = c.interval(f)
        covs.append(coverage_report(lo, hi, f, y, nominal=0.8).empirical)
    assert np.mean(covs) >= 0.78                          # guarantee: >= 0.8 on average


def test_coverage_degrades_under_variance_shift():
    rng = np.random.default_rng(8)
    c = SplitConformal(0.2).calibrate(*_draw(rng, 400, 0.2))
    f, y = _draw(rng, 2000, 0.6)                          # volatility regime changed
    lo, hi = c.interval(f)
    rep = coverage_report(lo, hi, f, y, nominal=0.8)
    assert rep.empirical < 0.6 and rep.worst_rolling is not None   # the caveat is real


def test_mcs_known_answer_and_determinism():
    rng = np.random.default_rng(1)
    n = 400
    losses = pd.DataFrame({"a": rng.gamma(2, .05, n), "b": rng.gamma(2, .05, n),
                           "bad": rng.gamma(2, .05, n) + 0.2})
    r1 = model_confidence_set(losses, horizon=24, seed=3, reps=300)
    r2 = model_confidence_set(losses, horizon=24, seed=3, reps=300)
    assert r1 == r2 and r1.excluded == ("bad",) and set(r1.included) == {"a", "b"}
    assert r1.block_size == 24 and r1.pvalues["a"] == 1.0


def test_mcs_refuses_bad_input():
    L = pd.DataFrame(np.ones((50, 2)) * 0.1, columns=["a", "b"])
    with pytest.raises(McsError, match="block_size"):
        model_confidence_set(L, horizon=24, block_size=5, seed=1)
    with pytest.raises(McsError, match="two models"):
        model_confidence_set(L[["a"]], horizon=24, seed=1)
    with pytest.raises(McsError, match="index"):
        qlike_loss_frame(pd.DataFrame({"a": [1.0]}, index=[0]), pd.Series([1.0], index=[1]))
