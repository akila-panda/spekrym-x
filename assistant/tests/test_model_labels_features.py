"""Phase 9A: triple-barrier labels and causal features (frozen synthetic fixtures)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sx_assistant.model.features import FEATURE_LOOKBACK, FEATURE_NAMES, build_rows
from sx_assistant.model.labels_triple_barrier import (BarrierConfig, atr_series, label_one,
                                                       label_rows)
from sx_assistant.model.windowed import windowed_setups
from sx_core.clock import tf_delta
from sx_core.contracts import Candle, Setup
from sx_core.storage import candles_to_frame

FX = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "model"
CFG = BarrierConfig()


@pytest.fixture(scope="module")
def candles() -> list[Candle]:
    return [Candle(**d) for d in json.loads((FX / "candles_h1_1800.json").read_text())]


@pytest.fixture(scope="module")
def setups() -> list[Setup]:
    return [Setup(**d) for d in json.loads((FX / "setups_synthetic.json").read_text())]


def _flat(n: int, atr_range: float = 0.001):
    c = np.full(n, 1.0)
    return c + atr_range / 2, c - atr_range / 2, c.copy()


def test_label_hand_cases():
    cfg = BarrierConfig(horizon=5, atr_period=2, target_atr=1.0, stop_atr=1.0)
    h, lo, c = _flat(12)
    atr = atr_series(h, lo, c, 2)
    a = atr[3]
    assert a == pytest.approx(0.001)
    h2, l2 = h.copy(), lo.copy()
    h2[5] = 1.0 + 1.2 * a                                  # target only
    assert label_one(h2, l2, c, atr, 3, 1, cfg)[:3] == (1, 5, "target")
    l2[4], h2[4] = 1.0 - 1.2 * a, 1.0 + 1.2 * a            # both barriers in one bar -> stop
    assert label_one(h2, l2, c, atr, 3, 1, cfg)[:3] == (0, 4, "stop")
    assert label_one(h, lo, c, atr, 3, 1, cfg)[:3] == (0, 8, "time")
    assert label_one(h2, l2, c, atr, 3, -1, cfg)[2] == "stop"  # short: high above -> stop first
    assert label_one(h, lo, c, atr, 8, 1, cfg) is None     # not enough future bars: no label


def test_features_have_no_label_columns_and_known_names(candles, setups):
    rows = build_rows(setups, candles, CFG)
    assert tuple(c for c in rows.columns if c in FEATURE_NAMES) == FEATURE_NAMES
    assert not {"label", "fwd_ret_atr", "outcome", "label_end_idx"} & set(rows.columns)
    assert (rows["decision_time"] >= pd.Series([s.known_at for s in setups]).min()).all()


def test_decision_is_first_close_at_or_after_known_at(candles, setups):
    rows = build_rows(setups, candles, CFG).set_index("setup_id")
    by_id = {s.id: s for s in setups}
    d = tf_delta("H1")
    for sid in list(rows.index)[:40]:
        i = int(rows.loc[sid, "decision_idx"])
        assert candles[i].time + d >= by_id[sid].known_at
        assert i == 0 or candles[i - 1].time + d < by_id[sid].known_at


def test_feature_rows_are_prefix_stable(candles, setups):
    full = build_rows(setups, candles, CFG).set_index("setup_id")
    for n in (300, 777, 1500):
        part = build_rows(setups, candles[:n], CFG).set_index("setup_id")
        assert len(part) and part.index.isin(full.index).all()
        cols = list(FEATURE_NAMES)
        a = part[cols].astype(float)
        b = full.loc[part.index, cols].astype(float)
        # n_recent counts use only setups known by the decision time, so they must match too
        pd.testing.assert_frame_equal(a, b, check_exact=True)
        assert (part["decision_idx"] < n).all()


def test_changing_bars_older_than_lookback_does_not_change_the_row(candles, setups):
    rows = build_rows(setups, candles, CFG).set_index("setup_id")
    sid = rows.index[rows["decision_idx"] > 400][0]
    i = int(rows.loc[sid, "decision_idx"])
    cut = i - FEATURE_LOOKBACK - CFG.atr_period - 2
    tampered = [c.model_copy(update={"open": c.open, "high": c.high + 0.01, "close": c.close})
                if k < cut else c for k, c in enumerate(candles)]
    again = build_rows(setups, tampered, CFG).set_index("setup_id")
    for f in ("atr_rel", "height_atr", "dist_mid_atr", "ret6_with_dir", "ret24_with_dir",
              "n_recent", "age_bars"):
        assert again.loc[sid, f] == pytest.approx(rows.loc[sid, f], abs=1e-12), f


def test_retrospective_setups_are_refused(candles, setups):
    bad = setups[0].model_copy(update={"status": "retrospective"})
    with pytest.raises(ValueError, match="non-causal"):
        build_rows([bad], candles, CFG)


def test_labels_drop_unlabellable_tail(candles, setups):
    rows = build_rows(setups, candles, CFG)
    lab = label_rows(rows, candles_to_frame(candles), CFG)
    assert len(lab) < len(rows) and set(lab["label"].unique()) <= {0, 1}
    assert (lab["label_end_idx"] <= len(candles) - 1).all()


def test_windowed_equals_full_for_a_causal_producer(candles, setups):
    def producer(window):  # a stand-in causal producer: setups already known inside the window
        d = tf_delta("H1")
        end = window[-1].time + d
        return [s for s in setups if window[0].time <= s.event_time and s.known_at <= end]

    full = producer(candles)
    got = windowed_setups(candles, warmup=100, step=300, analyze=producer)
    assert [s.id for s in got] == [s.id for s in sorted(full, key=lambda s: (s.known_at,
                                                                           s.event_time, s.id))]
