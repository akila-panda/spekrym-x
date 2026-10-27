import numpy as np
import pandas as pd
import pytest

from sx_lab.features import build_features, forward_target, make_dataset
from sx_lab.features.volatility import FeatureInputError
from lab_fixtures import _dataset, _synth_candles  # noqa: F401


def test_features_are_prefix_causal(synth_candles):
    """Features at row t computed on candles[:L] equal those computed on all candles."""
    full = build_features(synth_candles)
    for length in range(130, 200):
        part = build_features(synth_candles[:length])
        pd.testing.assert_frame_equal(part, full.iloc[:length], check_exact=True)


def test_future_bar_change_never_alters_earlier_features(synth_candles):
    base = build_features(synth_candles)
    changed = list(synth_candles)
    last = changed[-1]
    changed[-1] = last.model_copy(update={"close": last.close * 1.01,
                                          "high": last.high * 1.02})
    after = build_features(changed)
    pd.testing.assert_frame_equal(base.iloc[:-1], after.iloc[:-1], check_exact=True)


def test_target_is_a_label_that_does_use_the_future(synth_candles):
    t = forward_target(synth_candles, 24)["target"]
    assert t.iloc[-24:].isna().any()  # unfinished windows at the tail are NaN, not guessed
    r2 = np.log(pd.Series([c.close for c in synth_candles]).pipe(lambda s: s / s.shift(1))) ** 2
    assert t.iloc[100] == pytest.approx(r2.iloc[101:125].mean())


def test_dataset_has_no_nan_and_audit_columns(dataset):
    assert not dataset.isna().any().any()
    assert (dataset["target_known_at"] > dataset["known_at"]).all()
    assert len(dataset) == 1000 - 120 - 24


def test_dataset_needs_horizon_in_windows(synth_candles):
    with pytest.raises(ValueError, match="windows"):
        make_dataset(synth_candles, 12)


def test_rejects_forming_bar(synth_candles):
    bad = list(synth_candles[:50])
    bad[-1] = bad[-1].model_copy(update={"complete": False})
    with pytest.raises(FeatureInputError, match="forming"):
        build_features(bad)


def test_rejects_unordered(synth_candles):
    bad = [synth_candles[1], synth_candles[0], *synth_candles[2:20]]
    with pytest.raises(FeatureInputError, match="increasing"):
        build_features(bad)
