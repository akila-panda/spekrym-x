"""P11 evaluation protocol for the scorer: chronological train / validation / sealed holdout.

* Splits are by BAR position on one time-ordered series (no shuffling across time).
* Purge gap (bars) = label horizon + feature look-back, stated in the spec and enforced:
  a train row's label window ends before the first validation row's feature window starts, and
  the same between validation and holdout. See ``split_of`` and ``assert_purged``.
* Holdout is reachable only through ``open_holdout``: it verifies spec, data and configuration
  hashes against the lock, writes the opening to the ledger BEFORE returning data, and works
  once per holdout content. A second evaluation on a spent holdout is refused (policy below).
* Policy for later experiments: a new experiment id needs NEW holdout rows (later data); the
  spent holdout may then only be used as validation data under a new spec that says so. Silent
  reuse is impossible because the holdout id is a hash of its rows.
Process rule, not security (same limit as the Lab, L-3).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field

import pandas as pd

from sx_assistant.model.features import FEATURE_LOOKBACK, FEATURE_NAMES
from sx_assistant.model.labels_triple_barrier import BarrierConfig
from sx_core.ledger import Ledger
from sx_core.storage import data_version

KIND_LOCKED, KIND_OPENED, KIND_TRIAL = ("model.evaluation_locked", "model.holdout_opened",
                                       "model.trial")
GRID = ({"num_leaves": 4, "min_data_in_leaf": 50, "num_boost_round": 60},
        {"num_leaves": 4, "min_data_in_leaf": 100, "num_boost_round": 120},
        {"num_leaves": 8, "min_data_in_leaf": 50, "num_boost_round": 60},
        {"num_leaves": 8, "min_data_in_leaf": 100, "num_boost_round": 120},
        {"num_leaves": 16, "min_data_in_leaf": 100, "num_boost_round": 60})


class ProtocolError(ValueError):
    """The split or spec cannot be used safely."""


class HoldoutRefused(PermissionError):
    """Holdout access refused (not locked, hash mismatch, or already opened)."""


@dataclass(frozen=True)
class ProtocolSpec:
    experiment_id: str = "SCORER-001"
    instrument: str = "EUR_USD"
    tf: str = "H1"
    barrier: BarrierConfig = field(default_factory=BarrierConfig)
    feature_lookback: int = FEATURE_LOOKBACK
    purge_bars: int = 72  # = horizon 24 + look-back 48
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2)
    feature_names: tuple[str, ...] = FEATURE_NAMES
    grid: tuple[dict, ...] = GRID
    seed: int = 1
    n_shuffles: int = 20
    min_rows_per_split: int = 150

    def __post_init__(self) -> None:
        if self.purge_bars < self.barrier.horizon + self.feature_lookback:
            raise ProtocolError(f"purge_bars {self.purge_bars} < horizon + look-back "
                                f"{self.barrier.horizon + self.feature_lookback}")
        if len(self.fractions) != 3 or abs(sum(self.fractions) - 1) > 1e-9 \
                or min(self.fractions) <= 0:
            raise ProtocolError("fractions must be three positive numbers summing to 1")

    def canonical(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=list)

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()


def bounds(n_bars: int, fractions: tuple[float, float, float]) -> tuple[int, int]:
    return (math.floor(n_bars * fractions[0] + 1e-9),
            math.floor(n_bars * (fractions[0] + fractions[1]) + 1e-9))


def split_of(decision_idx: int, b1: int, b2: int, gap: int) -> str:
    """'train' | 'validation' | 'holdout' | 'purged' for a row decided at ``decision_idx``."""
    if decision_idx < b1:
        return "train"
    if b1 + gap <= decision_idx < b2:
        return "validation"
    if decision_idx >= b2 + gap:
        return "holdout"
    return "purged"


def assert_purged(parts: dict[str, pd.DataFrame], spec: ProtocolSpec) -> None:
    """Raise unless each split's labels end before the next split's feature windows begin."""
    order = ["train", "validation", "holdout"]
    for a, b in zip(order, order[1:], strict=False):
        if parts[a].empty or parts[b].empty:
            continue
        end_a = int(parts[a]["label_end_idx"].max())
        start_b = int(parts[b]["decision_idx"].min()) - spec.feature_lookback
        if not end_a < start_b:
            raise ProtocolError(f"{a} labels end at bar {end_a}, {b} features start at {start_b}")
        if not parts[a]["decision_idx"].max() < parts[b]["decision_idx"].min():
            raise ProtocolError(f"{a} and {b} are not in chronological order")


def _hash(df: pd.DataFrame) -> str:
    keep = ["decision_idx", "label", "label_end_idx", *[c for c in df.columns
                                                         if c in FEATURE_NAMES]]
    return data_version(df[keep].reset_index(drop=True))


class ScorerPartition:
    """Rows split chronologically. ``train()`` and ``validation()`` only; holdout is governed."""

    def __init__(self, rows: pd.DataFrame, n_bars: int, spec: ProtocolSpec, candles_dv: str):
        need = {"decision_idx", "label", "label_end_idx", *FEATURE_NAMES}
        if not need <= set(rows.columns) or not rows["decision_idx"].is_monotonic_increasing:
            raise ProtocolError("rows need features, labels and increasing decision_idx")
        self.spec, self.candles_dv = spec, candles_dv
        self.b1, self.b2 = bounds(n_bars, spec.fractions)
        tag = [split_of(int(i), self.b1, self.b2, spec.purge_bars) for i in rows["decision_idx"]]
        self.n_purged = tag.count("purged")
        parts = {k: rows[[t == k for t in tag]].reset_index(drop=True)
                 for k in ("train", "validation", "holdout")}
        assert_purged(parts, spec)
        for k, v in parts.items():
            if len(v) < spec.min_rows_per_split:
                raise ProtocolError(f"{k} has {len(v)} rows (< {spec.min_rows_per_split})")
        self._train, self._val, self._hold = parts["train"], parts["validation"], parts["holdout"]
        self.hashes = {"train": _hash(self._train), "validation": _hash(self._val),
                       "holdout": _hash(self._hold)}
        self.holdout_id = self.hashes["holdout"]

    def __repr__(self) -> str:  # never prints data
        return (f"ScorerPartition(train={len(self._train)}, validation={len(self._val)}, "
                f"holdout=sealed:{len(self._hold)}, purged={self.n_purged})")

    def train(self) -> pd.DataFrame:
        return self._train.copy()

    def validation(self) -> pd.DataFrame:
        return self._val.copy()

    def _entries(self, ledger: Ledger, kind: str) -> list[dict]:
        return [e.payload for e in ledger.read()
                if e.kind == kind and e.payload.get("holdout_id") == self.holdout_id]

    def status(self, ledger: Ledger) -> str:
        if self._entries(ledger, KIND_OPENED):
            return "opened"
        return "locked" if self._entries(ledger, KIND_LOCKED) else "sealed"

    def lock_evaluation(self, ledger: Ledger, config_hash: str) -> None:
        """Freeze spec + data + chosen configuration. Allowed until the holdout is opened."""
        if self._entries(ledger, KIND_OPENED):
            raise HoldoutRefused("holdout already opened; a new evaluation needs new holdout rows")
        payload = {"holdout_id": self.holdout_id, "spec_hash": self.spec.hash,
                   "config_hash": config_hash, "candles_data_version": self.candles_dv,
                   "split_hashes": self.hashes, "experiment_id": self.spec.experiment_id}
        locks = self._entries(ledger, KIND_LOCKED)
        if locks and locks[-1] == payload:
            return
        ledger.append(KIND_LOCKED, payload, self.candles_dv)

    def open_holdout(self, ledger: Ledger, config_hash: str, reason: str) -> pd.DataFrame:
        """Verify hashes, log the opening, THEN return a copy of the holdout. Once only."""
        if not reason.strip():
            raise HoldoutRefused("a reason is required")
        if self._entries(ledger, KIND_OPENED):
            raise HoldoutRefused("holdout already opened; it is spent (see module policy)")
        locks = self._entries(ledger, KIND_LOCKED)
        if not locks:
            raise HoldoutRefused("evaluation is not locked")
        lock = locks[-1]
        checks = {"spec_hash": self.spec.hash, "config_hash": config_hash,
                  "candles_data_version": self.candles_dv, "split_hashes": self.hashes}
        bad = [k for k, v in checks.items() if lock.get(k) != v]
        if bad:
            raise HoldoutRefused(f"differs from the lock: {', '.join(bad)}")
        ledger.append(KIND_OPENED, {**lock, "reason": reason.strip()}, self.candles_dv)
        return self._hold.copy()
