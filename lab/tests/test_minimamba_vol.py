"""MiniMamba wrapper checks (8B). Skipped where torch/minimamba are not installed (the Mac's
main venv has no torch). Run in an environment that has both."""

import numpy as np
import pytest

pytest.importorskip("torch")
pytest.importorskip("minimamba")

from lab_fixtures import _dataset, _synth_candles  # noqa: E402, F401
from sx_lab.models.minimamba_vol import (MiniMambaEnsemble, MiniMambaVol,  # noqa: E402
                                         TrainConfig)

FAST = dict(epochs=2, batch_size=64, context_bars=16)


@pytest.fixture(scope="module")
def split(request):
    from sx_core.contracts import Candle
    import json
    from pathlib import Path
    from sx_lab.features import make_dataset
    raw = json.loads(Path("tests/fixtures/lab/eurusd_h1_synth_1000.json").read_text())
    ds = make_dataset([Candle.model_validate(r) for r in raw], 24)
    return ds.iloc[:300], ds.iloc[300:420]


@pytest.fixture(scope="module")
def model(split):
    return MiniMambaVol(TrainConfig(seed=1, **FAST)).fit(split[0])


def test_shape_positive_and_loss_falls(model, split):
    p = model.predict(split[1])
    assert len(p) == len(split[1]) and np.isfinite(p).all() and (p > 0).all()
    assert model.loss_by_epoch[-1] < model.loss_by_epoch[0]


def test_row_i_does_not_depend_on_later_rows(model, split):
    val = split[1]
    base = model.predict(val).to_numpy()
    k = 60
    changed = val.copy()
    for c in model.cols:
        changed.iloc[k + 1:, changed.columns.get_loc(c)] *= 7.0
    after = model.predict(changed).to_numpy()
    assert np.allclose(base[:k + 1], after[:k + 1], rtol=1e-6)
    assert not np.allclose(base[k + 1:], after[k + 1:])      # the edit does matter later


def test_predict_never_reads_target(model, split):
    val = split[1]
    scrambled = val.copy()
    scrambled["target"] = scrambled["target"].to_numpy()[::-1] * 3.0
    assert np.allclose(model.predict(val), model.predict(scrambled))


def test_same_seed_same_forecast_different_seed_differs(split, model):
    again = MiniMambaVol(TrainConfig(seed=1, **FAST)).fit(split[0])
    assert np.allclose(model.predict(split[1]), again.predict(split[1]))
    other = MiniMambaVol(TrainConfig(seed=2, **FAST)).fit(split[0])
    assert not np.allclose(model.predict(split[1]), other.predict(split[1]))


def test_history_equals_concatenation_and_state_roundtrip(model, split):
    tr, val = split
    h = tr.iloc[-15:]
    with_hist = model.predict(val, history=h).to_numpy()
    import pandas as pd
    joined = model.predict(pd.concat([h, val])).to_numpy()[len(h):]
    assert np.allclose(with_hist, joined)
    back = MiniMambaVol.from_state_bytes(model.state_bytes())
    assert np.allclose(back.predict(val, history=h), with_hist)


def test_ensemble_is_mean_of_log_forecasts(split):
    ens = MiniMambaEnsemble.train(split[0], [1, 2], TrainConfig(**FAST))
    a, b = (m.predict(split[1]).to_numpy() for m in ens.members)
    assert np.allclose(ens.predict(split[1]), np.sqrt(a * b))
    assert ens.params()["seeds"] == [1, 2]
