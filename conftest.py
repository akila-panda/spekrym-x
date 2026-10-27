"""Repo-root pytest config: registers the causality plugin and shared fixtures."""

import json
from pathlib import Path

import pytest

from sx_core.contracts import Candle

pytest_plugins = ["sx_core.pytest_plugin"]

FIXTURES = Path(__file__).parent / "tests" / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def m15_candles() -> list[Candle]:
    """96 frozen EUR_USD M15 bars, 2026-10-19 00:00 to 23:45 UTC (see tests/fixtures)."""
    raw = json.loads((FIXTURES / "eurusd_m15_96bars.json").read_text())
    return [Candle.model_validate(r) for r in raw]
