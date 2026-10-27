"""Shared Lab fixtures. Not a conftest.py on purpose: pytest imports every conftest.py under the
top-level name ``conftest``, which collided with assistant/tests/conftest.py. Test modules import
the private names below, and the fixtures register as ``synth_candles`` and ``dataset``."""

import json

import pytest

from sx_core.contracts import Candle
from sx_lab.features import make_dataset

HORIZON = 24


@pytest.fixture(scope="session", name="synth_candles")
def _synth_candles(fixtures_dir) -> list[Candle]:
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return [Candle.model_validate(r) for r in raw]


@pytest.fixture(scope="session", name="dataset")
def _dataset(fixtures_dir):
    raw = json.loads((fixtures_dir / "lab" / "eurusd_h1_synth_1000.json").read_text())
    return make_dataset([Candle.model_validate(r) for r in raw], HORIZON)
