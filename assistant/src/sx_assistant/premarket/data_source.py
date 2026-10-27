"""Market-data source interface. Phase 5A ships one implementation: a frozen sample fixture.

A verified provider (for example the OANDA practice client) can be added later behind the same
``MarketDataSource`` protocol. Until a source has fetched real candles it must not claim to be
live. Every source states its own honesty label; the fixture's is ``SAMPLE DATA — NOT LIVE``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from sx_core.clock import bar_close
from sx_core.contracts import Candle
from sx_core.contracts._base import Tf
from sx_data.resample import resample

SAMPLE_LABEL = "SAMPLE DATA — NOT LIVE"
DEFAULT_FIXTURE = (Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "premarket"
                   / "eurusd_m15_sample.json")
CONTEXT_TFS: tuple[Tf, ...] = ("H1", "H4", "D")


@dataclass(frozen=True)
class SourceInfo:
    id: str            # "sample"
    name: str
    label: str         # shown on every surface
    live: bool         # True only for a provider that has fetched real candles


class MarketDataSource(Protocol):
    info: SourceInfo

    def instruments(self) -> list[str]: ...
    def last_close(self, instrument: str) -> datetime:
        """Close time of the newest closed M15 bar this source has."""
    def candles(self, instrument: str, tf: Tf, as_of: datetime) -> list[Candle]:
        """Closed bars of ``tf`` that had closed by ``as_of`` (never a forming bar)."""


class FixtureSource:
    """Frozen M15 fixture; H1, H4 and D are built from it with ``sx_data.resample``."""

    info = SourceInfo("sample", "Frozen EUR/USD fixture (synthetic)", SAMPLE_LABEL, False)

    def __init__(self, path: Path | str = DEFAULT_FIXTURE) -> None:
        raw = json.loads(Path(path).read_text())
        self._m15 = sorted((Candle.model_validate(r) for r in raw), key=lambda c: c.time)
        if not self._m15:
            raise ValueError("fixture has no candles")
        self._instrument = self._m15[0].instrument

    def instruments(self) -> list[str]:
        return [self._instrument]

    def last_close(self, instrument: str) -> datetime:
        self._check(instrument)
        return bar_close(self._m15[-1].time, "M15")

    def candles(self, instrument: str, tf: Tf, as_of: datetime) -> list[Candle]:
        self._check(instrument)
        closed = [c for c in self._m15 if c.complete and bar_close(c.time, "M15") <= as_of]
        if tf == "M15":
            return closed
        if tf not in CONTEXT_TFS:
            raise ValueError(f"fixture source has no {tf} bars")
        return resample(closed, tf, as_of=as_of) if closed else []

    def _check(self, instrument: str) -> None:
        if instrument != self._instrument:
            raise KeyError(f"unknown instrument {instrument!r}")
