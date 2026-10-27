import numpy as np
import pandas as pd
import pytest

from sx_core.ledger import Ledger
from sx_lab.baselines import HAR, HistoricalMean, Persistence
from sx_lab.evaluation.negative_controls import (
    find_noncausal_columns, leaked_feature_control, shuffled_label_control)
from sx_lab.evaluation.purged_cv_crosscheck import crosscheck, purged_cv_scores, purged_kfold
from sx_lab.features import build_features, make_dataset
from sx_lab.partition import LabPartition
from sx_lab.search import SEARCH_WINDOWS, run_har_search, variants_tried
from lab_fixtures import _dataset, _synth_candles  # noqa: F401


def _frames(skill: bool, seed=3):
    rng = np.random.default_rng(seed)
    n = 400
    f = pd.DataFrame({c: rng.uniform(1e-7, 1e-6, n) for c in ("rv_6", "rv_24", "rv_120")})
    f["target"] = (0.5 * f["rv_6"] + 0.5 * f["rv_24"] if skill
                   else rng.uniform(1e-7, 1e-6, n)) * rng.uniform(0.9, 1.1, n)
    return f.iloc[:300], f.iloc[300:]


def test_shuffled_control_passes_when_there_is_skill():
    tr, va = _frames(True)
    r = shuffled_label_control(HAR, tr, va)
    assert r.passed and r.values["shuffled_median_qlike"] > r.values["honest_qlike"]


def test_shuffled_control_fails_when_there_is_no_skill():
    tr, va = _frames(False)
    assert not shuffled_label_control(HAR, tr, va).passed


def test_shuffled_control_flags_label_free_models():
    tr, va = _frames(True)
    r = shuffled_label_control(lambda: Persistence(24), tr.assign(rv_24=tr["rv_24"]), va)
    assert not r.passed and "ignores" in r.detail


def test_leak_guard_flags_leak_and_spares_real_features(synth_candles):
    r = leaked_feature_control(synth_candles, 24, SEARCH_WINDOWS, lengths=(200, 300))
    assert r.passed and r.values == {"real_flagged": [], "leaked_flagged": ["leak"]}


def test_find_noncausal_columns_catches_centered_window(synth_candles):
    def bad(c):
        f = build_features(c, (6, 24))
        f["centered"] = f["rv_6"].rolling(5, center=True).mean()
        return f
    assert find_noncausal_columns(bad, synth_candles, (200, 300)) == ["centered"]


def test_purged_kfold_covers_everything_and_respects_purge():
    seen = []
    for tr, te in purged_kfold(200, 5, 7):
        assert len(set(tr) & set(te)) == 0
        gap = np.abs(tr[:, None] - te[None, :]).min()
        assert gap > 7
        seen.extend(te)
    assert sorted(seen) == list(range(200))
    with pytest.raises(ValueError):
        list(purged_kfold(5, 5, 1))


def test_crosscheck_runs_and_compares_orders(dataset):
    p = LabPartition(dataset, horizon=24)
    frame = pd.concat([p.train(), p.validation()])
    scores = purged_cv_scores(HistoricalMean, frame, k=4, purge=24)
    assert len(scores) == 4 and all(np.isfinite(scores))
    cc = crosscheck({"mean": HistoricalMean, "har": HAR}, frame, {"mean": 1.0, "har": 2.0},
                    k=4, purge=24)
    assert set(cc.cv_order) == {"mean", "har"} and cc.validation_order == ["mean", "har"]
    assert cc.agrees == (cc.cv_order == ["mean", "har"])


def test_search_logs_every_trial_and_never_touches_holdout(synth_candles, tmp_path):
    p = LabPartition(make_dataset(synth_candles, 24, SEARCH_WINDOWS), horizon=24)
    led = Ledger(tmp_path / "l.jsonl")
    r = run_har_search(p, led, study="s1", n_trials=6, seed=0)
    assert r.n_trials == 6 and led.verify() == 6
    v = variants_tried(led, "s1")
    assert v["trials"] == 6 and 1 <= v["distinct"] <= 6
    assert {e.kind for e in led.read()} == {"lab.trial"}
    assert p.holdout_status(led) == "sealed"
    led2 = Ledger(tmp_path / "l2.jsonl")
    assert run_har_search(p, led2, study="s1", n_trials=6, seed=0).best_params == r.best_params
    assert variants_tried(led, "other")["trials"] == 0
