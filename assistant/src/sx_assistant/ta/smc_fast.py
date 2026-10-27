"""Lean numpy ports of three smart-money-concepts 0.0.27 functions (issue 27, replay speed).

Why: the replay wrapper calls the library once per bar, and the library is pandas-heavy
(about 70% of the replay time was in these three functions). These ports reproduce the
library's results **exactly**, including its quirks (float32 levels, the swing clean-up loop,
the order in which BOS/CHoCH entries are overwritten and removed). They are not a redesign.

Equality with the library is not assumed; ``assistant/tests/test_ta_smc_fast.py`` compares
them with the real library on every prefix of the fixtures and of many random series.
``smc_adapter.smc_setups(engine="library")`` still runs the original library path as the
reference.

Scope notes:
- ``swings`` returns the library's swings *without* its two forced edge swings. The adapter
  always nulls bars 0 and k-1 afterwards, and a real swing can never sit on either (it needs
  bars on both sides), so the cleaned result is identical.
- ``fvg_at`` returns the gap that is completed by the newest bar only. A gap at bar ``j``
  depends only on bars ``j-1..j+1``, so its values never change once bar ``j+1`` exists.
  Gaps found at earlier prefixes were already seen and are frozen.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def swings(high: np.ndarray, low: np.ndarray, swing_length: int
           ) -> tuple[np.ndarray, np.ndarray]:
    """``(HighLow, Level)`` as the library gives them, minus the forced edge swings."""
    n, half = len(high), swing_length            # the library doubles swing_length: window 2L
    hl = np.full(n, np.nan)
    if n >= 3 * half:
        s = np.arange(half, n - 2 * half + 1)    # window start; the bar is i = s + half - 1
        i = s + half - 1
        hmax = sliding_window_view(high, 2 * half).max(axis=1)[s]
        lmin = sliding_window_view(low, 2 * half).min(axis=1)[s]
        hl[i] = np.where(high[i] == hmax, 1.0, np.where(low[i] == lmin, -1.0, np.nan))
    while True:
        pos = np.flatnonzero(~np.isnan(hl))
        if len(pos) < 2:
            break
        cur, nxt = hl[pos[:-1]], hl[pos[1:]]
        highs, lows = high[pos[:-1]], low[pos[:-1]]
        nhighs, nlows = high[pos[1:]], low[pos[1:]]
        drop = np.zeros(len(pos), dtype=bool)
        ch = (cur == 1) & (nxt == 1)
        drop[:-1] |= ch & (highs < nhighs)
        drop[1:] |= ch & (highs >= nhighs)
        cl = (cur == -1) & (nxt == -1)
        drop[:-1] |= cl & (lows > nlows)
        drop[1:] |= cl & (lows <= nlows)
        if not drop.any():
            break
        hl[pos[drop]] = np.nan
    level = np.where(~np.isnan(hl), np.where(hl == 1, high, low), np.nan)
    return hl, level


def fvg_at(open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray
           ) -> tuple[int, float, float] | None:
    """The fair value gap centred on bar ``k-2`` (completed by bar ``k-1``), or ``None``."""
    k = len(close)
    if k < 3:
        return None
    j = k - 2
    if high[j - 1] < low[j + 1] and close[j] > open_[j]:
        return 1, float(low[j + 1]), float(high[j - 1])        # direction, top, bottom
    if low[j - 1] > high[j + 1] and close[j] < open_[j]:
        return -1, float(low[j - 1]), float(high[j + 1])
    return None


def bos_choch(close: np.ndarray, hl: np.ndarray, lvl: np.ndarray
              ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """``(BOS, CHOCH, Level, BrokenIndex)`` as ``smc.bos_choch(close_break=True)`` returns."""
    n = len(close)
    bos = np.zeros(n, dtype=np.int32)
    choch = np.zeros(n, dtype=np.int32)
    level = np.zeros(n, dtype=np.float32)
    lo_, hi_ = [], []                              # level_order, highs_lows_order
    last: list[int] = []
    up, down = [-1, 1, -1, 1], [1, -1, 1, -1]
    for i in np.flatnonzero(~np.isnan(hl)):
        lo_.append(float(lvl[i]))
        hi_.append(float(hl[i]))
        if len(lo_) >= 4:
            p = last[-2]
            a, b, c, d = lo_[-4], lo_[-3], lo_[-2], lo_[-1]
            tail = hi_[-4:]
            bos[p] = 1 if (tail == up and a < c < b < d) else 0
            level[p] = b if bos[p] != 0 else 0
            bos[p] = -1 if (tail == down and a > c > b > d) else bos[p]
            level[p] = b if bos[p] != 0 else 0
            choch[p] = 1 if (tail == up and d > b > a > c) else 0
            level[p] = b if choch[p] != 0 else level[p]
            choch[p] = -1 if (tail == down and d < b < a < c) else choch[p]
            level[p] = b if choch[p] != 0 else level[p]
        last.append(int(i))
    broken = np.zeros(n, dtype=np.int32)
    for i in np.where(np.logical_or(bos != 0, choch != 0))[0]:
        mask = np.zeros(n, dtype=np.bool_)
        if bos[i] == 1 or choch[i] == 1:
            mask = close[i + 2:] > level[i]
        elif bos[i] == -1 or choch[i] == -1:
            mask = close[i + 2:] < level[i]
        if np.any(mask):
            j = np.argmax(mask) + i + 2
            broken[i] = j
            for k in np.where(np.logical_or(bos != 0, choch != 0))[0]:
                if k < i and broken[k] >= j:
                    bos[k] = 0
                    choch[k] = 0
                    level[k] = 0
    for i in np.where(np.logical_and(np.logical_or(bos != 0, choch != 0), broken == 0))[0]:
        bos[i] = 0
        choch[i] = 0
        level[i] = 0
    return (np.where(bos != 0, bos, np.nan), np.where(choch != 0, choch, np.nan),
            np.where(level != 0, level, np.nan), np.where(broken != 0, broken, np.nan))
