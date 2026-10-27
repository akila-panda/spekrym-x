"""Loaders for the frozen Phase 4 fixtures (``tests/fixtures/ta``, synthetic, hand-designed)."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry, Source

M15 = timedelta(minutes=15)
D0 = datetime(2026, 10, 19, tzinfo=UTC)


def at(i: int) -> datetime:
    """Open time of M15 bar ``i`` of the labelled day."""
    return D0 + i * M15


def bars(raw: list[dict]) -> list[Candle]:
    return [Candle.model_validate(r) for r in raw]


@pytest.fixture(scope="session")
def ta_dir(fixtures_dir):
    return fixtures_dir / "ta"


@pytest.fixture(scope="session")
def day(ta_dir) -> list[Candle]:
    return bars(json.loads((ta_dir / "labelled_day.json").read_text()))


@pytest.fixture(scope="session")
def day_tail(ta_dir) -> list[Candle]:
    return bars(json.loads((ta_dir / "labelled_day_tail.json").read_text()))


@pytest.fixture(scope="session")
def day_expected(ta_dir) -> list[dict]:
    return json.loads((ta_dir / "labelled_day_expected.json").read_text())


@pytest.fixture(scope="session")
def liq(ta_dir) -> dict:
    d = json.loads((ta_dir / "liquidity_day.json").read_text())
    return {"candles": bars(d["candles"]), "expected": d["expected"]}


@pytest.fixture(scope="session")
def candle_day(ta_dir) -> dict:
    d = json.loads((ta_dir / "candle_day.json").read_text())
    return {"candles": bars(d["candles"]), "level_price": d["level_price"],
            "expected": d["expected"]}


@pytest.fixture(scope="session")
def dst_h1(ta_dir) -> list[Candle]:
    return bars(json.loads((ta_dir / "dst_h1.json").read_text()))


def make_level(price: float, known_at: datetime, *, status: str = "causal",
               kind: str = "session_level") -> Setup:
    """A minimal causal reference level for the candle-pattern tests."""
    return Setup(
        id=setup_id(kind, "EUR_USD", "M15", "bullish", D0, f"test:{status}"), kind=kind,
        instrument="EUR_USD", tf="M15", direction="bullish",
        geometry=Geometry(price_low=price, price_high=price, t_start=D0), event_time=D0,
        known_at=known_at, lifecycle="fresh",
        source=Source(library="test", version="0", adapter="conftest"),
        plain_text="test level", invalidation="n/a", status=status)
