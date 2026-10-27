import pandas as pd
import pytest

from sx_core.ledger import Ledger
from sx_lab.partition import (HoldoutRefused, LabPartition, PartitionError, make_ranges)
from lab_fixtures import _dataset  # noqa: F401

SPEC = "a" * 64


def _ledger(tmp_path):
    return Ledger(tmp_path / "ledger.jsonl")


def test_default_split_is_60_20_20_with_embargo():
    r = make_ranges(1000, 24)
    assert (r.train.start, r.train.stop) == (0, 600)
    assert (r.validation.start, r.validation.stop) == (624, 800)
    assert (r.holdout.start, r.holdout.stop) == (824, 1000)


def test_bad_fractions_and_tiny_input_refused():
    with pytest.raises(PartitionError):
        make_ranges(100, 1, (0.5, 0.5, 0.5))
    with pytest.raises(PartitionError):
        make_ranges(10, 5)


def test_embargo_below_horizon_refused(dataset):
    with pytest.raises(PartitionError, match="below the horizon"):
        LabPartition(dataset, horizon=24, embargo=10)


def test_splits_are_chronological_and_labels_do_not_straddle(dataset):
    p = LabPartition(dataset, horizon=24)
    tr, va = p.train(), p.validation()
    assert tr.index.max() < va.index.min()
    # every training label was already knowable when validation's first origin closed
    assert tr["target_known_at"].max() <= va["known_at"].min()
    assert len(tr) + len(va) + len(p.ranges.holdout) + 2 * p.embargo == len(dataset)


def test_nan_and_unsorted_frames_refused(dataset):
    bad = dataset.copy()
    bad.iloc[3, 1] = float("nan")
    with pytest.raises(PartitionError, match="NaN"):
        LabPartition(bad, horizon=24)
    with pytest.raises(PartitionError, match="increasing"):
        LabPartition(dataset.iloc[::-1], horizon=24)


def test_repr_never_prints_holdout(dataset):
    p = LabPartition(dataset, horizon=24)
    assert "sealed" in repr(p)
    assert str(float(p._holdout["target"].iloc[0])) not in repr(p)


def test_holdout_needs_lock_reason_and_matching_spec(dataset, tmp_path):
    p, led = LabPartition(dataset, horizon=24), _ledger(tmp_path)
    assert p.holdout_status(led) == "sealed"
    with pytest.raises(HoldoutRefused, match="not locked"):
        p.open_holdout(led, SPEC, "final")
    p.lock_evaluation(led, SPEC)
    assert p.holdout_status(led) == "locked"
    with pytest.raises(HoldoutRefused, match="reason"):
        p.open_holdout(led, SPEC, "  ")
    with pytest.raises(HoldoutRefused, match="differs"):
        p.open_holdout(led, "b" * 64, "final")
    with pytest.raises(HoldoutRefused, match="64"):
        p.lock_evaluation(led, "nothex")


def test_holdout_opens_once_and_is_logged_even_across_objects(dataset, tmp_path):
    led = _ledger(tmp_path)
    p = LabPartition(dataset, horizon=24)
    p.lock_evaluation(led, SPEC)
    p.lock_evaluation(led, SPEC)  # same spec again: no duplicate entry
    out = p.open_holdout(led, SPEC, "final evaluation")
    pd.testing.assert_frame_equal(out, dataset.iloc[p.ranges.holdout])
    kinds = [e.kind for e in led.read()]
    assert kinds == ["lab.evaluation_locked", "lab.holdout_opened"]
    assert led.verify() == 2
    # a fresh object (a restart, or someone re-creating it) cannot reopen the spent holdout
    again = LabPartition(dataset, horizon=24)
    assert again.holdout_status(led) == "opened"
    with pytest.raises(HoldoutRefused, match="spent"):
        again.open_holdout(led, SPEC, "peek again")
    with pytest.raises(HoldoutRefused, match="already opened"):
        again.lock_evaluation(led, "c" * 64)
    # changing the fractions does not make the same holdout rows fresh
    other = LabPartition(dataset, horizon=24, fractions=(0.6, 0.2, 0.2))
    assert other.holdout_id == p.holdout_id


def test_returned_frames_are_copies(dataset):
    p = LabPartition(dataset, horizon=24)
    x = p.train()
    x.iloc[0, 1] = 999.0
    assert p.train().iloc[0, 1] != 999.0
