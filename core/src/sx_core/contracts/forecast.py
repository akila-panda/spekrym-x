from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from sx_core.contracts._base import Contract, Tf, UtcDatetime
from sx_core.labels import ForecastStatus

Regime = Literal["quiet", "normal", "expanding", "extreme"]


class Interval(Contract):
    low: float
    high: float
    nominal_coverage: float = Field(gt=0, lt=1)


class ModelRef(Contract):
    name: str
    version: str
    params_hash: str


class BaselineComparison(Contract):
    baseline: str
    metric: str
    delta: float


class TrackRecord(Contract):
    n: int = Field(ge=0)
    empirical_coverage: float
    variants_tried: int = Field(ge=0)


class Forecast(Contract):
    """Output of the Lab. Volatility or range only, never direction."""

    id: str
    instrument: str
    tf: Tf
    issued_at: UtcDatetime
    horizon_end: UtcDatetime
    target: Literal["realized_vol", "range"]
    point: float
    interval: Interval
    regime: Regime | None = None
    model: ModelRef
    baseline_comparison: BaselineComparison | None = None
    track_record: TrackRecord
    status: ForecastStatus

    @model_validator(mode="after")
    def _point_inside_interval(self) -> Forecast:
        if not self.interval.low <= self.point <= self.interval.high:
            raise ValueError("point outside interval")
        return self
