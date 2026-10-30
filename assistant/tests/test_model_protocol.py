"""Phase 9A: P11 protocol (purge, sealed holdout), negative controls, scorer (synthetic)."""

import json
import re
from pathlib import Path

import pytest

from sx_assistant.model.controls import leak_scan, leaked_feature_control, shuffled_control
from sx_assistant.model.features import FEATURE_NAMES, build_rows
from sx_assistant.model.labels_triple_barrier import label_rows
from sx_assistant.model.protocol import (HoldoutRefused, ProtocolError, ProtocolSpec,
                                         ScorerPartition, assert_purged, bounds, split_of)
from sx_assistant.model.scorer import LABELS, SCORE_NOTE, Scorer, ScoredSetup
from sx_assistant.model.train_lgbm import auc, fit, margin
from sx_core.contracts import Candle, Setup
from sx_core.ledger import Ledger
from sx_core.storage import candles_to_frame

FX = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "model"
FEATS = list(FEATURE_NAMES)
PARAMS = {"num_leaves": 4, "min_data_in_leaf": 10, "num_boost_round": 30}


@pytest.fixture(scope="module")
def built():
    candles = [Candle(**d) for d in json.loads((FX / "candles_h1_1800.json").read_text())]
    setups = [Setup(**d) for d in json.loads((FX / "setups_synthetic.json").read_text())]
    spec = ProtocolSpec(min_rows_per_split=30)
    rows = build_rows(setups, candles, spec.barrier)
    rows = rows.join(label_rows(rows, candles_to_frame(candles), spec.barrier), how="inner")
    return spec, rows, len(candles)


@pytest.fixture
def part(built):
    spec, rows, n = built
    return ScorerPartition(rows, n, spec, "dv:test")


def test_spec_refuses_a_gap_shorter_than_horizon_plus_lookback():
    with pytest.raises(ProtocolError, match="purge_bars"):
        ProtocolSpec(purge_bars=71)
    assert ProtocolSpec().purge_bars == 24 + 48


def test_splits_are_chronological_and_purged(part, built):
    spec = built[0]
    tr, va, ho = part.train(), part.validation(), part._hold
    assert tr["decision_idx"].max() < va["decision_idx"].min() < ho["decision_idx"].min()
    assert va["decision_idx"].min() >= part.b1 + spec.purge_bars
    assert ho["decision_idx"].min() >= part.b2 + spec.purge_bars
    assert tr["label_end_idx"].max() < va["decision_idx"].min() - spec.feature_lookback
    assert va["label_end_idx"].max() < ho["decision_idx"].min() - spec.feature_lookback
    assert part.n_purged > 0
    assert split_of(part.b1, part.b1, part.b2, 72) == "purged"
    assert bounds(1800, spec.fractions) == (1080, 1440)


def test_assert_purged_catches_overlap(part, built):
    spec = built[0]
    tr, va = part.train(), part.validation()
    bad = tr.copy()
    bad.loc[bad.index[-1], "label_end_idx"] = int(va["decision_idx"].min())
    with pytest.raises(ProtocolError, match="labels end"):
        assert_purged({"train": bad, "validation": va, "holdout": part._hold}, spec)


def test_holdout_governance(part, tmp_path):
    led = Ledger(tmp_path / "l.jsonl")
    assert part.status(led) == "sealed" and "sealed" in repr(part)
    with pytest.raises(HoldoutRefused, match="not locked"):
        part.open_holdout(led, "cfg", "why")
    part.lock_evaluation(led, "cfg")
    with pytest.raises(HoldoutRefused, match="config_hash"):
        part.open_holdout(led, "other", "why")
    with pytest.raises(HoldoutRefused, match="reason"):
        part.open_holdout(led, "cfg", "  ")
    ho = part.open_holdout(led, "cfg", "one registered evaluation")
    assert len(ho) == len(part._hold) and part.status(led) == "opened"
    kinds = [e.kind for e in led.read()]
    assert kinds == ["model.evaluation_locked", "model.holdout_opened"]  # logged before use
    with pytest.raises(HoldoutRefused, match="spent"):
        part.open_holdout(led, "cfg", "again")
    with pytest.raises(HoldoutRefused, match="already opened"):
        part.lock_evaluation(led, "new")


def test_holdout_refuses_changed_data_or_spec(built, tmp_path):
    spec, rows, n = built
    led = Ledger(tmp_path / "l.jsonl")
    ScorerPartition(rows, n, spec, "dv:one").lock_evaluation(led, "cfg")
    with pytest.raises(HoldoutRefused, match="candles_data_version"):
        ScorerPartition(rows, n, spec, "dv:two").open_holdout(led, "cfg", "x")
    other = ProtocolSpec(min_rows_per_split=30, seed=2)
    with pytest.raises(HoldoutRefused, match="spec_hash"):
        ScorerPartition(rows, n, other, "dv:one").open_holdout(led, "cfg", "x")
    train_edit = rows.copy()  # holdout rows intact, an earlier label changed: split hash differs
    train_edit.loc[train_edit.index[0], "label"] = 1 - train_edit.loc[train_edit.index[0], "label"]
    with pytest.raises(HoldoutRefused, match="split_hashes"):
        ScorerPartition(train_edit, n, spec, "dv:one").open_holdout(led, "cfg", "x")
    hold_edit = rows.copy()  # holdout content changed: it is a different holdout, never locked
    hold_edit.loc[hold_edit["decision_idx"] >= 1500, "label"] = 1 - hold_edit["label"]
    with pytest.raises(HoldoutRefused, match="not locked"):
        ScorerPartition(hold_edit, n, spec, "dv:one").open_holdout(led, "cfg", "x")


def test_fit_is_deterministic_and_shuffled_control_shows_no_skill(part):
    tr, va = part.train(), part.validation()
    a = margin(fit(tr[FEATS], tr["label"].to_numpy(), PARAMS, 1), va[FEATS])
    b = margin(fit(tr[FEATS], tr["label"].to_numpy(), PARAMS, 1), va[FEATS])
    assert (a == b).all()
    c = shuffled_control(tr, va, FEATS, [PARAMS, {**PARAMS, "num_leaves": 8}], n=8, seed=3)
    assert c["behaves_as_expected"] and c["auc_max"] < 0.75


def test_leaked_feature_control_fails_as_it_should(part):
    tr, va = part.train(), part.validation()
    r = leaked_feature_control(tr, va, FEATS, PARAMS, seed=1)
    assert r["leaked_auc"] > 0.8 and r["flagged_with_leak"] == ["LEAK_fwd_ret_atr"]
    assert r["flagged_real_features"] == [] and r["behaves_as_expected"]
    assert leak_scan(va, FEATS) == []


def test_scorer_always_has_reasons_labels_and_no_probability_wording(part, tmp_path):
    tr, va = part.train(), part.validation()
    model = fit(tr[FEATS], tr["label"].to_numpy(), PARAMS, 1)
    sc = Scorer(model, margin(model, va[FEATS]))
    scored = sc.score(va[FEATS].head(6), list(va["setup_id"].head(6)))
    text = json.dumps([[s.note, s.labels, [r.text for r in s.reasons]] for s in scored]).lower()
    assert all(s.reasons and set(LABELS) <= set(s.labels) and 0 <= s.rank_score <= 100
               for s in scored)
    assert not re.search(r"probab|chance|likel|win rate|odds|%", text)
    assert all(s.note == SCORE_NOTE for s in scored)
    with pytest.raises(ValueError, match="reason"):
        ScoredSetup("x", 50.0, 0.0, (), LABELS, "m")
    with pytest.raises(ValueError, match="labels"):
        ScoredSetup("x", 50.0, 0.0, scored[0].reasons, ("Exploratory",), "m")
    sha = sc.save(tmp_path)
    again = Scorer.load(tmp_path, expect_hash=sha)
    assert again.version == sc.version
    assert [s.raw_margin for s in again.score(va[FEATS].head(6), list(va["setup_id"].head(6)))] \
        == pytest.approx([s.raw_margin for s in scored])
    assert auc(va["label"].to_numpy(), margin(again.model, va[FEATS])) == pytest.approx(
        auc(va["label"].to_numpy(), margin(model, va[FEATS])))
