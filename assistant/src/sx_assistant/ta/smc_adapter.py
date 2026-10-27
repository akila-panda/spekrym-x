"""Adapter around smart-money-concepts 0.0.27 (read from source, see docs/DEPENDENCIES.md).

What the source does that is NOT causal, and what we do about it (all via the replay wrapper):

- ``swing_highs_lows`` needs ``swing_length`` bars to its right, and forces a fake swing on
  the first and last bar. We drop bars 0 and k-1 and only accept swings with their full right
  side present, so a swing is known when its ``swing_length``-th right-hand bar closes.
- ``bos_choch`` returns a future ``BrokenIndex`` and a level as float32; ``ob`` returns float32
  zones (swapped in one branch); ``liquidity`` scales its tolerance by the high-low range of
  the whole frame. Run on a prefix, each is a function of that prefix only.
- Objects are frozen at first sight (``causal_wrapper``). So results can differ from a
  one-shot library call on the full series: that is intended (the one-shot call looks ahead).
- Speed (issue 27): the default engine replaces three pandas-heavy library calls (swings, FVG,
  BOS/CHoCH) with exact numpy ports in ``smc_fast``; ``engine="library"`` keeps the original
  per-prefix path as the reference, and tests assert identical output on every prefix.
- Library lifecycle columns (mitigated/broken index) are ignored; ``normalize.lifecycle_at``
  recomputes lifecycle as of any time ``t`` from closed bars.
"""

from __future__ import annotations

import contextlib
import io
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from sx_assistant.ta import smc_fast
from sx_assistant.ta.causal_wrapper import PrefixView, Seen, replay_first_seen
from sx_assistant.ta.common import check_series, fmt_price, lib_source, to_frame
from sx_core.contracts import Candle, Setup, setup_id
from sx_core.contracts.setup import Geometry

try:
    with contextlib.redirect_stdout(io.StringIO()):  # the library prints a banner on import
        from smartmoneyconcepts import smc
except ImportError as exc:
    raise ImportError(
        "smartmoneyconcepts is not installed. Run: pip install --no-deps "
        "smartmoneyconcepts==0.0.27 (--no-deps because it declares numba, which it never "
        "imports, and numba/llvmlite have no Intel-Mac wheels)") from exc

ADAPTER = "sx_assistant.ta.smc_adapter"
DIST = "smartmoneyconcepts"


def clean_swings(view: PrefixView, swing_length: int) -> pd.DataFrame:
    """Library swings on this prefix without its two forced edge swings."""
    def make() -> pd.DataFrame:
        sw = smc.swing_highs_lows(view.df, swing_length=swing_length)
        sw.loc[[0, view.k - 1], ["HighLow", "Level"]] = np.nan
        return sw
    return view.cached(f"swings{swing_length}", make)


Items = list[tuple[str, dict[str, Any]]]


def _emit_bos(out: Items, bc: dict[str, np.ndarray], levels: np.ndarray) -> None:
    for kind, col in (("bos", "BOS"), ("choch", "CHOCH")):
        for p in np.flatnonzero(~np.isnan(bc[col])):
            d = int(bc[col][p])
            lvl = float(levels[np.argmin(np.abs(levels - float(bc["Level"][p])))])
            out.append((f"{kind}:{p}:{d}", {"p": int(p), "dir": d, "level": lvl,
                                           "j": int(bc["BrokenIndex"][p])}))


def _emit_zones(out: Items, df: pd.DataFrame, sw: pd.DataFrame, range_percent: float) -> None:
    """Order blocks and liquidity sweeps (library calls; already numpy-based, not ported)."""
    ob = smc.ob(df, sw)
    for idx in np.flatnonzero(~np.isnan(ob["OB"].to_numpy())):
        out.append((f"ob:{idx}:{int(ob['OB'].iloc[idx])}",
                    {"idx": int(idx), "dir": int(ob["OB"].iloc[idx]),
                     "top": float(df["high"].iloc[idx]), "bottom": float(df["low"].iloc[idx])}))
    liq = smc.liquidity(df, sw, range_percent=range_percent)
    for i in np.flatnonzero(~np.isnan(liq["Liquidity"].to_numpy())):
        swept = liq["Swept"].iloc[i]
        if np.isnan(swept) or int(swept) <= 0:
            continue
        out.append((f"liq:{i}:{int(liq['Liquidity'].iloc[i])}",
                    {"i": int(i), "dir": int(liq["Liquidity"].iloc[i]),
                     "level": round(float(liq["Level"].iloc[i]), 6), "swept": int(swept)}))


def _extract_library(view: PrefixView, swing_length: int, range_percent: float) -> Items:
    """Reference path: the library called on this prefix (slow; kept as the oracle)."""
    df, k = view.df, view.k
    out: Items = []
    sw = clean_swings(view, swing_length)
    hl = sw["HighLow"].to_numpy()
    for i in np.flatnonzero(~np.isnan(hl)):
        out.append((f"swing:{i}:{int(hl[i])}",
                    {"i": int(i), "dir": int(hl[i]), "level": float(sw["Level"].iloc[i])}))
    if k < 3:
        return out
    fvg = smc.fvg(df)
    for j in np.flatnonzero(~np.isnan(fvg["FVG"].to_numpy())):
        d = int(fvg["FVG"].iloc[j])
        out.append((f"fvg:{j}:{d}", {"j": int(j), "dir": d, "top": float(fvg["Top"].iloc[j]),
                                     "bottom": float(fvg["Bottom"].iloc[j])}))
    if np.isnan(hl).all():
        return out
    bc = smc.bos_choch(df, sw)
    _emit_bos(out, {c: bc[c].to_numpy() for c in ("BOS", "CHOCH", "Level", "BrokenIndex")},
              sw["Level"].dropna().to_numpy())
    _emit_zones(out, df, sw, range_percent)
    return out


def _extract_fast(view: PrefixView, swing_length: int, range_percent: float,
                  arrays: tuple[np.ndarray, ...]) -> Items:
    """Same objects as ``_extract_library`` on the prefix, minus gaps already seen earlier."""
    o, h, lo, c = (a[:view.k] for a in arrays)
    out: Items = []
    hl, lvl = smc_fast.swings(h, lo, swing_length)
    for i in np.flatnonzero(~np.isnan(hl)):
        out.append((f"swing:{i}:{int(hl[i])}",
                    {"i": int(i), "dir": int(hl[i]), "level": float(lvl[i])}))
    if view.k < 3:
        return out
    gap = smc_fast.fvg_at(o, h, lo, c)             # older gaps are unchanged and frozen
    if gap is not None:
        j = view.k - 2
        out.append((f"fvg:{j}:{gap[0]}", {"j": j, "dir": gap[0], "top": gap[1],
                                          "bottom": gap[2]}))
    if np.isnan(hl).all():
        return out
    bos, choch, blevel, broken = smc_fast.bos_choch(c, hl, lvl)
    _emit_bos(out, {"BOS": bos, "CHOCH": choch, "Level": blevel, "BrokenIndex": broken},
              lvl[~np.isnan(lvl)])
    sw = pd.DataFrame({"HighLow": hl, "Level": lvl})
    _emit_zones(out, view.df, sw, range_percent)
    return out


def _setup(s: Seen, cs: Sequence[Candle], swing_length: int) -> Setup:
    inst, tf = cs[0].instrument, cs[0].tf
    kind = s.key.split(":", 1)[0]
    d = s.data
    px = lambda x: fmt_price(x, inst)  # noqa: E731
    src = lib_source(DIST, ADAPTER)

    def build(kd: str, direction: str, low: float, high: float, t0: Candle, ev: Candle,
              t_end: Candle | None, disc: str, text: str, inval: str) -> Setup:
        return Setup(
            id=setup_id(kd, inst, tf, direction, ev.time, disc), kind=kd, instrument=inst,
            tf=tf, direction=direction, geometry=Geometry(
                price_low=low, price_high=high, t_start=t0.time,
                t_end=None if t_end is None else t_end.time),
            event_time=ev.time, known_at=s.known_at, lifecycle="fresh", source=src,
            plain_text=text, invalidation=inval, status="causal")

    if kind == "swing":
        c, high = cs[d["i"]], d["dir"] == 1
        word, beyond = ("high", "above") if high else ("low", "below")
        return build("swing", "bearish" if high else "bullish", d["level"], d["level"], c, c,
                     None, word, f"Swing {word} {px(d['level'])}: {word}est of "
                     f"{swing_length} bars on its right (a pivot, not a forecast)",
                     f"A close {beyond} {px(d['level'])} breaks the swing.")
    if kind == "fvg":
        c, bull = cs[d["j"]], d["dir"] == 1
        far, beyond = (d["bottom"], "below") if bull else (d["top"], "above")
        return build("fvg", "bullish" if bull else "bearish", d["bottom"], d["top"],
                     cs[d["j"] - 1], c, None, "", f"{'Bullish' if bull else 'Bearish'} fair "
                     f"value gap {px(d['bottom'])} to {px(d['top'])} (three-candle gap)",
                     f"A close {beyond} {px(far)} fills the gap and invalidates it.")
    if kind in ("bos", "choch"):
        c, bull = cs[d["j"]], d["dir"] == 1
        name = "break of structure" if kind == "bos" else "change of character"
        beyond, back = ("above", "below") if bull else ("below", "above")
        return build(kind, "bullish" if bull else "bearish", d["level"], d["level"],
                     cs[d["p"]], c, c, f"p:{cs[d['p']].time:%Y%m%dT%H%M}",
                     f"{'Bullish' if bull else 'Bearish'} {name}: closed {beyond} "
                     f"{px(d['level'])}", f"A close back {back} {px(d['level'])} undoes it.")
    if kind == "ob":
        c, bull = cs[d["idx"]], d["dir"] == 1
        far, beyond = (d["bottom"], "below") if bull else (d["top"], "above")
        return build("order_block", "bullish" if bull else "bearish", d["bottom"], d["top"],
                     c, c, None, "", f"{'Bullish' if bull else 'Bearish'} order block "
                     f"{px(d['bottom'])} to {px(d['top'])}: the candle with the "
                     f"{'lowest low' if bull else 'highest high'} before the swing break",
                     f"A close {beyond} {px(far)} invalidates the block.")
    c = cs[d["swept"]]  # liquidity
    side = "highs" if d["dir"] == 1 else "lows"
    return build("liquidity_sweep", "neutral", d["level"], d["level"], cs[d["i"]], c, c,
                 f"i:{cs[d['i']].time:%Y%m%dT%H%M}", f"Equal {side} near {px(d['level'])} "
                 "(2+ swing points) were traded through", "Informational: it is a past event; "
                 "it does not predict what price does next.")


def smc_setups(candles: Sequence[Candle], swing_length: int = 3,
               range_percent: float = 0.01, engine: str = "fast") -> list[Setup]:
    """Swings, FVGs, BOS/CHoCH, order blocks and liquidity sweeps, all causal (see module doc).

    ``engine="fast"`` (default) uses the numpy ports in ``smc_fast``; ``engine="library"`` is
    the original per-prefix library path. Both give identical output (tested).
    """
    check_series(candles)
    if swing_length < 1:
        raise ValueError("swing_length must be >= 1")
    if engine == "library":
        def extract(v: PrefixView) -> Items:
            return _extract_library(v, swing_length, range_percent)
    elif engine == "fast":
        frame = to_frame(candles)
        arrays = tuple(frame[x].to_numpy() for x in ("open", "high", "low", "close"))

        def extract(v: PrefixView) -> Items:
            return _extract_fast(v, swing_length, range_percent, arrays)
    else:
        raise ValueError(f"unknown engine {engine!r}")
    seen = replay_first_seen(candles, extract)
    out = [_setup(s, candles, swing_length) for s in seen]
    return sorted(out, key=lambda s: (s.known_at, s.event_time, s.id))
