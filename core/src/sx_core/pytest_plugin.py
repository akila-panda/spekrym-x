"""Pytest plugin exposing the causality harness to every module's tests.

Registered from the repo-root ``conftest.py``. Usage in any test::

    def test_my_adapter_is_causal(assert_causal, m15_candles):
        assert_causal(my_producer, m15_candles)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from sx_core import causality


@pytest.fixture
def assert_causal() -> Callable[..., None]:
    """The prefix-equality assertion (see ``sx_core.causality.assert_causal``)."""
    return causality.assert_causal


@pytest.fixture
def check_prefix_equality() -> Callable[..., Any]:
    """Non-raising variant that returns the list of violations."""
    return causality.check_prefix_equality
