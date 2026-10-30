"""Setups over a long history without the quadratic replay cost (issue 27).

``analyze_causal`` replays bar by bar, so one pass over 12,000 bars is far too slow. We run it on
overlapping windows (``warmup`` earlier bars + ``step`` new bars) and keep only setups whose
``known_at`` falls in the new part. Each kept setup was computed from bars up to its own
``known_at``, so it is causal. Approximation (documented, not hidden): a setup near the start of
a window is computed with only ``warmup`` bars of history, so grouping that depends on a longer
history (for example liquidity tolerance, issue 29) can differ from a single full-series run.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from sx_assistant.ta.normalize import analyze_causal
from sx_core.clock import tf_delta
from sx_core.contracts import Candle, Setup


def windowed_setups(candles: Sequence[Candle], *, warmup: int = 240, step: int = 240,
                    analyze: Callable[[Sequence[Candle]], list[Setup]] = analyze_causal,
                    progress: Callable[[int, int], None] | None = None) -> list[Setup]:
    if warmup < 1 or step < 1:
        raise ValueError("warmup and step must be >= 1")
    n, delta = len(candles), (tf_delta(candles[0].tf) if candles else None)
    seen: dict[str, Setup] = {}
    for start in range(0, n, step):
        stop = min(n, start + step)
        window = list(candles[max(0, start - warmup):stop])
        for s in analyze(window):
            if start and s.known_at <= candles[start].time:
                continue  # belongs to an earlier chunk
            if s.known_at > candles[stop - 1].time + delta:
                continue
            seen.setdefault(s.id, s)
        if progress:
            progress(stop, n)
    return sorted(seen.values(), key=lambda s: (s.known_at, s.event_time, s.id))
