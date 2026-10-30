"""Pre-registered experiment spec: typed, canonical-hashed, lockable only when complete (8A).

The spec is a YAML file. Its hash is SHA-256 of the canonical JSON of the parsed content, so
whitespace and key order do not matter but every value does, including ``status`` and the
approval block. A changed spec is a new experiment with a new id (decision L12). ``lockable``
lists every reason the spec cannot be locked yet; nothing locks a draft.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from sx_core.ledger import canonical_json

BLOCKED_LABEL = re.compile(r"sample|synthetic|not live", re.IGNORECASE)


class SpecError(ValueError):
    pass


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DataSpec(_M):
    instrument: str
    tf: str
    data_version: str | None
    first_bar: str | None
    last_bar: str | None


class PartitionSpec(_M):
    train: float
    validation: float
    holdout: float
    embargo_bars: int


class ModelSpec(_M):
    name: str
    role: Literal["reference", "baseline", "challenger"]
    pin: str | None = None
    settings: dict[str, int | float | str | bool] = {}


class McsSpec(_M):
    level: float
    reps: int
    block_size: int
    method: str
    seed: int


class ConformalSpec(_M):
    alpha: float
    calibration: str


class ApprovalSpec(_M):
    approved_by: str | None
    approved_on: str | None


class ExperimentSpec(_M):
    id: str
    status: Literal["draft", "approved"]
    question: str
    data: DataSpec
    horizon_bars: int
    windows: list[int]
    gap_policy: str
    partition: PartitionSpec
    models: list[ModelSpec]
    primary_metric: str
    secondary_metrics: list[str]
    mcs: McsSpec
    conformal: ConformalSpec
    max_variants: int
    stopping_rule: str
    outcome_rules: dict[str, str]
    labels: list[str]
    approval: ApprovalSpec

    def lockable(self) -> list[str]:
        why: list[str] = []
        if self.status != "approved":
            why.append("status is not 'approved'")
        if not (self.approval.approved_by and self.approval.approved_on):
            why.append("approval block is empty")
        for k, v in self.data.model_dump().items():
            if v is None:
                why.append(f"data.{k} is not filled")
        if self.horizon_bars not in self.windows:
            why.append("horizon_bars must be one of windows")
        if self.partition.embargo_bars < self.horizon_bars:
            why.append("embargo_bars is below horizon_bars")
        p = self.partition
        if abs(p.train + p.validation + p.holdout - 1) > 1e-9:
            why.append("partition fractions do not sum to 1")
        if self.mcs.block_size < self.horizon_bars:
            why.append("mcs.block_size is below horizon_bars")
        if not any(m.role == "reference" for m in self.models):
            why.append("no reference model")
        return why


def load_spec(path: str | Path) -> tuple[ExperimentSpec, str]:
    """Parse and validate; return the spec and its hash."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
        spec = ExperimentSpec.model_validate(raw)
    except (yaml.YAMLError, ValidationError, OSError) as e:
        raise SpecError(f"cannot load spec {path}: {str(e)[:300]}") from e
    return spec, hashlib.sha256(canonical_json(spec.model_dump()).encode()).hexdigest()


def refuse_blocked_label(label: str) -> None:
    """Decision L11: sample or synthetic data can never be used for the experiment."""
    if BLOCKED_LABEL.search(label):
        raise SpecError(f"data label {label!r} is sample/synthetic; EXP runs need real data")
