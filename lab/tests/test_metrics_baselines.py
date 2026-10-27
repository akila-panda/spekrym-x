import numpy as np
import pytest

from sx_lab.baselines import HistoricalMean, NotFittedError, Persistence
from sx_lab.evaluation import metrics as m
from sx_lab.partition import LabPartition
from lab_fixtures import _dataset  # noqa: F401


def test_qlike_zero_at_truth_and_hand_value():
    assert m.qlike([2.0, 3.0], [2.0, 3.0]) == pytest.approx(0.0)
    # y/f = 2 -> 2 - ln2 - 1
    assert m.qlike([1.0], [2.0]) == pytest.approx(1 - np.log(2))


def test_qlike_penalises_underforecast_more_than_overforecast():
    assert m.qlike([0.5], [1.0]) > m.qlike([2.0], [1.0])


def test_metrics_refuse_bad_input():
    with pytest.raises(m.MetricInputError):
        m.qlike([0.0], [1.0])
    with pytest.raises(m.MetricInputError):
        m.rmse([1.0, np.nan], [1.0, 2.0])
    with pytest.raises(m.MetricInputError):
        m.rmse([1.0], [1.0, 2.0])
    with pytest.raises(m.MetricInputError):
        m.interval_coverage([2.0], [1.0], [1.5])


def test_rmse_and_coverage_hand_values():
    assert m.rmse([1.0, 3.0], [2.0, 5.0]) == pytest.approx(np.sqrt((1 + 4) / 2))
    assert m.interval_coverage([0, 0, 0, 0], [1, 1, 1, 1], [0.5, 1.0, 1.5, -0.1]) == 0.5


def test_persistence_reads_only_past_columns(dataset):
    b = Persistence(24).fit(dataset)
    pred = b.predict(dataset.drop(columns=["target", "target_known_at"]))
    assert (pred == dataset["rv_24"]).all()
    with pytest.raises(KeyError):
        Persistence(12).predict(dataset)


def test_historical_mean_uses_train_only(dataset):
    p = LabPartition(dataset, horizon=24)
    b = HistoricalMean()
    with pytest.raises(NotFittedError):
        b.predict(p.validation())
    b.fit(p.train())
    assert b.predict(p.validation()).iloc[0] == pytest.approx(p.train()["target"].mean())


def test_baselines_score_on_validation(dataset):
    """Smoke: both baselines produce finite scores on the validation split (no ranking claim)."""
    p = LabPartition(dataset, horizon=24)
    va = p.validation()
    for b in (Persistence(24), HistoricalMean().fit(p.train())):
        s = m.score(b.predict(va), va["target"])
        assert s["n"] == len(va) and np.isfinite(s["qlike"]) and np.isfinite(s["rmse"])
