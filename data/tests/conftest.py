"""Fixtures for the data-layer tests. Frozen files only; no network."""

import json

import pytest

from sx_core.contracts import Candle
from sx_data.oanda_parse import parse_candles


@pytest.fixture(scope="session")
def m1_payload(fixtures_dir) -> dict:
    """OANDA-shaped M1 response: 06:00-09:00 UTC, 5 quiet minutes absent, last bar incomplete."""
    return json.loads((fixtures_dir / "oanda" / "eurusd_m1_oanda_shape.json").read_text())


@pytest.fixture(scope="session")
def m1_all(m1_payload) -> list[Candle]:
    return parse_candles(m1_payload, "EUR_USD", "M1")


@pytest.fixture(scope="session")
def m1_closed(m1_all) -> list[Candle]:
    return [c for c in m1_all if c.complete]


@pytest.fixture(scope="session")
def h1_week(fixtures_dir) -> list[Candle]:
    raw = json.loads((fixtures_dir / "eurusd_h1_week.json").read_text())
    return [Candle.model_validate(r) for r in raw]
