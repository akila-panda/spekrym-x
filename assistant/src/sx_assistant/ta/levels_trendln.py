"""trendln support/resistance trendlines: **Retrospective**, premarket only.

trendln fits lines to the whole window it is given, so every line is a function of the entire
series. Each output is tagged ``status="retrospective"`` and ``known_at`` is the close of the
last bar of the window (never earlier). It never feeds a model or a paper trade:
``normalize.require_causal`` raises if a retrospective setup is passed on.

trendln return value (read from its source): ``((min_idx, pmin, min_trends, min_windows),
(max_idx, pmax, max_trends, max_windows))``; each trend is ``([point indexes], (slope,
intercept, residual, slope_err, intercept_err, wrong_side_area))`` with ``y = slope*x +
intercept`` in bar-index space. Support lines come from lows, resistance from highs.

``Setup.geometry`` is an axis-aligned box, so a sloped line is stored as the bounding box of
its two endpoints; the slope is in ``plain_text``. Optional dependency: ``pip install -e
"assistant[retro]"`` (pulls scipy, scikit-image, matplotlib, sympy).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from sx_assistant.ta.common import check_series, fmt_price, lib_source
from sx_core.clock import available_at
from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry

ADAPTER = "sx_assistant.ta.levels_trendln"


def _trendln():  # type: ignore[no-untyped-def]
    try:
        import trendln
    except ImportError as exc:
        raise ImportError('trendln is not installed: pip install -e "assistant[retro]"') from exc
    return trendln


def trendline_setups(candles: Sequence[Candle], *, max_lines: int = 3) -> list[Setup]:
    """Up to ``max_lines`` support and ``max_lines`` resistance lines, best-fitting first."""
    instrument, tf = check_series(candles)
    if len(candles) < 10:
        raise ValueError("need at least 10 bars for trendlines")
    tl = _trendln()
    n = len(candles)
    lows = np.array([c.low for c in candles])
    highs = np.array([c.high for c in candles])
    (_, _, mins, _), (_, _, maxs, _) = tl.calc_support_resistance(
        (lows, highs), extmethod=tl.METHOD_NAIVE, accuracy=2)
    known = available_at(candles[-1].time, tf)
    src = lib_source("trendln", ADAPTER)
    out: list[Setup] = []
    for side, lines, direction in (("support", mins, "bullish"), ("resistance", maxs, "bearish")):
        best = sorted(lines, key=lambda ln: (-len(ln[0]), float(ln[1][3]), ln[0]))[:max_lines]
        for idxs, fit in best:
            slope, icpt = float(fit[0]), float(fit[1])
            first, last = int(idxs[0]), int(idxs[-1])
            p0, p1 = slope * first + icpt, slope * (n - 1) + icpt
            out.append(Setup(
                id=setup_id("support_resistance", instrument, tf, direction,
                            candles[last].time,
                            f"{side}:{candles[first].time:%Y%m%dT%H%M}"),
                kind="support_resistance", instrument=instrument, tf=tf, direction=direction,
                geometry=Geometry(price_low=min(p0, p1), price_high=max(p0, p1),
                                  t_start=candles[first].time, t_end=candles[-1].time),
                event_time=candles[last].time, known_at=known, lifecycle="fresh", source=src,
                plain_text=f"{side.capitalize()} trendline through {len(idxs)} points, "
                           f"{fmt_price(p0, instrument)} to {fmt_price(p1, instrument)} "
                           f"(slope {slope:+.6f} per bar). Retrospective: fitted on the whole "
                           "window, premarket view only",
                invalidation=f"A close {'below' if side == 'support' else 'above'} the line "
                             "breaks it.", status="retrospective"))
    return sorted(out, key=lambda s: (s.known_at, s.event_time, s.id))
