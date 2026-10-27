"""Small swing-high producers used to test the harness itself.

``causal_swings`` waits ``N`` bars for confirmation. The others are wrong on purpose.
"""

from __future__ import annotations

from collections.abc import Sequence

from sx_core.clock import known_at_after_bars
from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry, Source

N = 2  # bars on each side that must be lower for a swing high
SRC = Source(library="test", version="0", adapter="producers")


def _setup(c: Candle, known_at, price_high: float | None = None, tag: str = "") -> Setup:
    ph = c.high if price_high is None else price_high
    return Setup(
        id=setup_id("swing", c.instrument, c.tf, "bearish", c.time, tag),
        kind="swing", instrument=c.instrument, tf=c.tf, direction="bearish",
        geometry=Geometry(price_low=ph, price_high=ph, t_start=c.time),
        event_time=c.time, known_at=known_at, lifecycle="fresh", source=SRC,
        plain_text="swing high", invalidation="close above", status="causal")


def _is_swing_high(cs: Sequence[Candle], i: int) -> bool:
    window = cs[i - N: i + N + 1]
    return len(window) == 2 * N + 1 and all(cs[i].high > c.high for c in window if c is not cs[i])


def causal_swings(cs: Sequence[Candle]) -> list[Setup]:
    """Correct: a swing at bar i is known when bar i+N closes."""
    return [_setup(cs[i], known_at_after_bars(cs[i].time, cs[i].tf, N))
            for i in range(N, len(cs) - N) if _is_swing_high(cs, i)]


def early_known_at(cs: Sequence[Candle]) -> list[Setup]:
    """Look-ahead: same swings, but stamped known when the swing bar itself closes."""
    return [_setup(cs[i], known_at_after_bars(cs[i].time, cs[i].tf, 0))
            for i in range(N, len(cs) - N) if _is_swing_high(cs, i)]


def value_leak(cs: Sequence[Candle]) -> list[Setup]:
    """Look-ahead: geometry depends on the maximum high of the whole series."""
    top = max(c.high for c in cs)
    return [_setup(cs[i], known_at_after_bars(cs[i].time, cs[i].tf, N), price_high=top, tag="v")
            for i in range(N, len(cs) - N) if _is_swing_high(cs, i)]


def edge_swings(cs: Sequence[Candle]) -> list[Setup]:
    """Look-ahead: treats the last bar of whatever it is given as confirmed (no right side)."""
    out = causal_swings(cs)
    if len(cs) > N and all(cs[-1].high > c.high for c in cs[-1 - N: -1]):
        out.append(_setup(cs[-1], known_at_after_bars(cs[-1].time, cs[-1].tf, 0), tag="edge"))
    return out
