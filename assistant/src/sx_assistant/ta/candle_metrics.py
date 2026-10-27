"""Explicit, configurable candle-shape definitions (decision I15, definitions only).

This is the written specification of what a doji, pin bar and engulfing candle *mean* here, as
plain arithmetic on one or two closed candles. Every number lives in ``CandleRules`` and is a
**proposed default, not approved or tuned** (owner decision 2026-10-27: approve the
definitions, defer the numbers). Nothing in the pipeline calls this module yet: the emitted
candle setups still come from TA-Lib (``candles_talib.py``), whose own thresholds are not these.
Wiring these definitions in, or replacing TA-Lib with them, is a separate decision.

Measurements, for a candle with open ``o``, high ``h``, low ``l``, close ``c``:

    range = h - l          body = |c - o|
    upper_wick = h - max(o, c)          lower_wick = min(o, c) - l
    body_to_range = body / range        (undefined when range == 0)

Zero-range candles (``h == l``) have no shape: every predicate returns ``None``/``False``.
Comparisons are written as ``value <= limit`` when the rule is inclusive and ``value < limit``
when strict, chosen per rule in ``CandleRules``. Floating-point values that are mathematically
equal can differ in the last bit, so equality at a boundary is only dependable for values that
are exact in binary (tests use quarters).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from sx_core.contracts import Candle


@dataclass(frozen=True)
class CandleRules:
    """Thresholds. All defaults are proposed, unapproved values (I15)."""

    doji_max_body_to_range: float = 0.10
    doji_inclusive: bool = True                  # body/range <= max (False: strictly below)
    pin_max_body_to_range: float = 0.35
    pin_min_wick_to_body: float = 2.0            # long wick >= this x body
    pin_inclusive: bool = True                   # both pin limits inclusive (False: strict)
    engulf_inclusive: bool = False               # equal body edges count as engulfing

    def __post_init__(self) -> None:
        for name in ("doji_max_body_to_range", "pin_max_body_to_range"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.pin_min_wick_to_body < 0:
            raise ValueError("pin_min_wick_to_body must be >= 0")


DEFAULT_RULES = CandleRules()


@dataclass(frozen=True)
class Metrics:
    range: float
    body: float
    upper_wick: float
    lower_wick: float

    @property
    def body_to_range(self) -> float | None:
        return None if self.range == 0 else self.body / self.range


def metrics(c: Candle) -> Metrics:
    return Metrics(range=c.high - c.low, body=abs(c.close - c.open),
                   upper_wick=c.high - max(c.open, c.close),
                   lower_wick=min(c.open, c.close) - c.low)


def _le(a: float, b: float, inclusive: bool) -> bool:
    return a <= b if inclusive else a < b


def _ge(a: float, b: float, inclusive: bool) -> bool:
    return a >= b if inclusive else a > b


def is_doji(c: Candle, rules: CandleRules = DEFAULT_RULES) -> bool:
    """A candle whose body is a small share of its range. Zero-range candles are not dojis."""
    ratio = metrics(c).body_to_range
    return ratio is not None and _le(ratio, rules.doji_max_body_to_range, rules.doji_inclusive)


def pin_bar(c: Candle, rules: CandleRules = DEFAULT_RULES) -> str | None:
    """``"bullish"`` (long lower wick), ``"bearish"`` (long upper wick) or ``None``.

    Needs: non-zero range; body/range within the maximum; the longer wick at least
    ``pin_min_wick_to_body`` x body (a zero body passes when that wick is non-zero); and the
    longer wick strictly longer than the other one (equal wicks are not a pin bar).
    """
    m = metrics(c)
    ratio = m.body_to_range
    if ratio is None or m.upper_wick == m.lower_wick:
        return None
    if not _le(ratio, rules.pin_max_body_to_range, rules.pin_inclusive):
        return None
    wick = max(m.upper_wick, m.lower_wick)
    if wick <= 0:
        return None
    wick_to_body = math.inf if m.body == 0 else wick / m.body
    if not _ge(wick_to_body, rules.pin_min_wick_to_body, rules.pin_inclusive):
        return None
    return "bullish" if m.lower_wick > m.upper_wick else "bearish"


def is_engulfing(prev: Candle, cur: Candle, rules: CandleRules = DEFAULT_RULES) -> str | None:
    """``"bullish"`` / ``"bearish"`` if ``cur``'s body engulfs ``prev``'s body, else ``None``.

    Both candles need a non-zero body, of opposite colours. Bullish: ``prev`` fell, ``cur``
    rose, and ``cur.open`` is at or below ``prev.close`` while ``cur.close`` is at or above
    ``prev.open`` (strictly so unless ``engulf_inclusive``). Bearish is the mirror image.
    Wicks are ignored.
    """
    inc = rules.engulf_inclusive
    if prev.close < prev.open and cur.close > cur.open:
        if _le(cur.open, prev.close, inc) and _ge(cur.close, prev.open, inc):
            return "bullish"
    elif prev.close > prev.open and cur.close < cur.open:
        if _ge(cur.open, prev.close, inc) and _le(cur.close, prev.open, inc):
            return "bearish"
    return None
