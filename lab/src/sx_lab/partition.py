"""Chronological train / validation / holdout split with an embargo and a governed holdout.

Decisions L1 and L2 (docs/PHASE_7A_NOTES.md). Default 60 / 20 / 20 by time order, with an
embargo of at least ``horizon`` rows dropped before validation and before the holdout so that
overlapping target windows cannot straddle a boundary.

Holdout governance lives in the LEDGER, so it survives restarts and cannot be reset by creating
a new object:
  1. ``lock_evaluation(ledger, spec_hash)`` records the frozen evaluation spec.
  2. ``open_holdout(ledger, spec_hash, reason)`` needs that latest lock, logs the access BEFORE
     returning data, and works once per holdout content. A second call is refused.

This is a process rule, not security: Python cannot hide data from code that already holds the
full frame, and the full frame must stay out of experiment code.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sx_core.ledger import Ledger
from sx_core.storage import data_version

DEFAULT_FRACTIONS = (0.6, 0.2, 0.2)
KIND_LOCKED = "lab.evaluation_locked"
KIND_OPENED = "lab.holdout_opened"
_SPEC = re.compile(r"^[0-9a-f]{64}$")


class PartitionError(ValueError):
    """The split cannot be made safely."""


class HoldoutRefused(PermissionError):
    """Holdout access was refused (not locked, spec mismatch, or already opened)."""


@dataclass(frozen=True)
class SplitRanges:
    n: int
    embargo: int
    train: range
    validation: range
    holdout: range


def make_ranges(n: int, embargo: int, fractions: Sequence[float] = DEFAULT_FRACTIONS
                ) -> SplitRanges:
    if len(fractions) != 3 or any(f <= 0 for f in fractions) or abs(sum(fractions) - 1) > 1e-9:
        raise PartitionError("fractions must be three positive numbers summing to 1")
    if embargo < 0:
        raise PartitionError("embargo must be >= 0")
    a = math.floor(n * fractions[0] + 1e-9)
    b = math.floor(n * (fractions[0] + fractions[1]) + 1e-9)
    ranges = SplitRanges(n, embargo, range(0, a), range(a + embargo, b),
                         range(b + embargo, n))
    if min(len(ranges.train), len(ranges.validation), len(ranges.holdout)) < 1:
        raise PartitionError(f"{n} rows with embargo {embargo} leave an empty split")
    return ranges


class LabPartition:
    def __init__(self, frame: pd.DataFrame, *, horizon: int, embargo: int | None = None,
                 fractions: Sequence[float] = DEFAULT_FRACTIONS):
        if not isinstance(frame.index, pd.DatetimeIndex) or not frame.index.is_unique \
                or not frame.index.is_monotonic_increasing:
            raise PartitionError("frame must have a unique, increasing DatetimeIndex")
        if frame.isna().any().any():
            raise PartitionError("frame contains NaN; drop warm-up and tail rows first")
        emb = horizon if embargo is None else embargo
        if emb < horizon:
            raise PartitionError(f"embargo {emb} is below the horizon {horizon}")
        self.horizon, self.embargo, self.fractions = horizon, emb, tuple(fractions)
        self.ranges = make_ranges(len(frame), emb, self.fractions)
        self._train = frame.iloc[self.ranges.train].copy()
        self._validation = frame.iloc[self.ranges.validation].copy()
        self._holdout = frame.iloc[self.ranges.holdout].copy()
        self.data_version = data_version(frame.reset_index())
        self.holdout_id = data_version(self._holdout.reset_index())
        key = f"{self.data_version}|{emb}|{self.fractions}"
        self.partition_id = hashlib.sha256(key.encode()).hexdigest()[:16]

    def __repr__(self) -> str:  # never prints data
        r = self.ranges
        return (f"LabPartition(train={len(r.train)}, validation={len(r.validation)}, "
                f"holdout=sealed:{len(r.holdout)}, embargo={r.embargo})")

    def train(self) -> pd.DataFrame:
        return self._train.copy()

    def validation(self) -> pd.DataFrame:
        return self._validation.copy()

    # ---- holdout governance ------------------------------------------------------------
    def _entries(self, ledger: Ledger, kind: str) -> list[dict]:
        return [e.payload for e in ledger.read()
                if e.kind == kind and e.payload.get("holdout_id") == self.holdout_id]

    def holdout_status(self, ledger: Ledger) -> str:
        if self._entries(ledger, KIND_OPENED):
            return "opened"
        return "locked" if self._entries(ledger, KIND_LOCKED) else "sealed"

    def lock_evaluation(self, ledger: Ledger, spec_hash: str) -> None:
        """Record the frozen evaluation spec (its hash). Allowed until the holdout is opened."""
        if not _SPEC.match(spec_hash):
            raise HoldoutRefused("spec_hash must be 64 lowercase hex characters")
        if self._entries(ledger, KIND_OPENED):
            raise HoldoutRefused("holdout already opened; a new evaluation needs new data")
        locks = self._entries(ledger, KIND_LOCKED)
        if locks and locks[-1]["spec_hash"] == spec_hash:
            return
        ledger.append(KIND_LOCKED, {"holdout_id": self.holdout_id,
                                    "partition_id": self.partition_id,
                                    "spec_hash": spec_hash}, self.data_version)

    def open_holdout(self, ledger: Ledger, spec_hash: str, reason: str) -> pd.DataFrame:
        """Log the access, then return a copy of the holdout. Once per holdout content."""
        if not reason.strip():
            raise HoldoutRefused("a reason is required")
        if self._entries(ledger, KIND_OPENED):
            raise HoldoutRefused("holdout already opened; it is spent")
        locks = self._entries(ledger, KIND_LOCKED)
        if not locks:
            raise HoldoutRefused("evaluation is not locked; call lock_evaluation first")
        if locks[-1]["spec_hash"] != spec_hash:
            raise HoldoutRefused("spec_hash differs from the latest lock")
        ledger.append(KIND_OPENED, {"holdout_id": self.holdout_id,
                                    "partition_id": self.partition_id,
                                    "spec_hash": spec_hash, "reason": reason.strip()},
                      self.data_version)
        return self._holdout.copy()
