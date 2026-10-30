"""Suggestions engine (Phase 9B): Setups + the 9A rank score (+ optional Lab forecast).

Produces ``Suggestion`` contracts.

Not advice and not a validated signal. ``score`` is a RANK against validation-period scores
(never a probability). Levels reuse the barrier multiples the 9A labels used (target 1.5 x ATR,
stop 1.0 x ATR from the decision bar's close); they are provisional and carry no cost model.
Everything here is causal: setups with ``known_at > as_of`` and bars not closed by ``as_of``
are dropped before any feature is built. No order is placed; gates are shown as advice.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from sx_assistant.model.features import FEATURE_NAMES, build_rows
from sx_assistant.model.labels_triple_barrier import BarrierConfig, atr_series
from sx_assistant.model.scorer import ScoredSetup, Scorer
from sx_assistant.paper.broker import OrderRequest, Quote
from sx_assistant.rules.ruleset import rules_version, verify_frozen
from sx_assistant.suggestions.evidence import EvidenceError, make_reason, validate_suggestion
from sx_assistant.suggestions.gates_view import build_gates, evaluate_gates
from sx_assistant.ta.normalize import lifecycle_at, require_causal
from sx_core.clock import tf_delta
from sx_core.contracts import Candle, Forecast, PaperOrder, Setup, Suggestion, suggestion_id

SCORER_TF = "H1"  # the 9A scorer was trained and validated on H1 only


@dataclass(frozen=True)
class EngineConfig:
    max_age_bars: int = 6      # decision bar must be among the newest bars (provisional)
    max_items: int = 10
    barrier: BarrierConfig = BarrierConfig()
    units: float = 1.0         # used only to build the advisory gate request


@dataclass(frozen=True)
class Rejected:
    setup_id: str
    why: str


@dataclass(frozen=True)
class EngineResult:
    suggestions: tuple[Suggestion, ...]
    scored: dict[str, ScoredSetup]          # keyed by suggestion id
    evidence: dict[str, Setup]              # every setup id a suggestion points at
    rejected: tuple[Rejected, ...]
    as_of: datetime
    rules_version: str


def _forecast_claim(f: Forecast) -> str:
    i = f.interval
    return (f"Lab {f.target} forecast (exploratory, not validated; volatility only, not a "
            f"direction): point {f.point:.3g}, interval {i.low:.3g} to {i.high:.3g}, "
            f"nominal coverage {i.nominal_coverage:.2f}")


def build_suggestions(setups: Sequence[Setup], candles: Sequence[Candle], scorer: Scorer,
                      rules_path: str | Path, *, as_of: datetime,
                      forecast: Forecast | None = None,
                      open_orders: Sequence[PaperOrder] | None = None,
                      realized_on: Callable[[datetime], float] | None = None,
                      config: EngineConfig | None = None) -> EngineResult:
    config = config or EngineConfig()
    rules, rhash = verify_frozen(rules_path)
    version = rules_version(rules, rhash)
    empty = EngineResult((), {}, {}, (), as_of, version)
    if not candles:
        return empty
    if candles[0].tf != SCORER_TF:
        raise ValueError(f"the scorer was validated on {SCORER_TF} bars only, got {candles[0].tf}")
    if forecast is not None and forecast.issued_at > as_of:
        raise ValueError("forecast was issued after as_of (not causal)")
    delta = tf_delta(candles[0].tf)
    bars = [c for c in candles if c.complete and c.time + delta <= as_of]
    sets = require_causal([s for s in setups if s.known_at <= as_of])
    if not bars or not sets:
        return empty
    n = len(bars)
    rows = build_rows(sets, bars, config.barrier)
    rows = rows[rows["decision_idx"] >= n - config.max_age_bars]
    by_id = {s.id: s for s in sets}
    live = [lifecycle_at(by_id[sid], bars, as_of) in ("fresh", "tested")
            for sid in rows["setup_id"]]
    rows = rows[np.array(live, dtype=bool)].reset_index(drop=True)
    if rows.empty:
        return empty
    scored = scorer.score(rows[list(FEATURE_NAMES)], list(rows["setup_id"]))
    hi, lo, cl = (np.array([getattr(b, a) for b in bars], float) for a in ("high", "low", "close"))
    atr = atr_series(hi, lo, cl, config.barrier.atr_period)
    gates = build_gates(rules, realized_on or (lambda _t: 0.0))
    known = set(by_id) | ({forecast.id} if forecast else set())
    out: list[tuple[Suggestion, ScoredSetup]] = []
    rejected: list[Rejected] = []
    for (_, row), sc in zip(rows.iterrows(), scored, strict=True):
        s = by_id[row["setup_id"]]
        try:
            i, long_ = int(row["decision_idx"]), s.direction == "bullish"
            entry, a, sgn = float(cl[i]), float(atr[i]), 1.0 if long_ else -1.0
            stop, target = entry - sgn * config.barrier.stop_atr * a, \
                entry + sgn * config.barrier.target_atr * a
            side = "long" if long_ else "short"
            reasons = [make_reason(s.plain_text, s.id, known)]
            reasons += [make_reason(r.text, s.id, known) for r in sc.reasons]
            if forecast is not None:
                reasons.append(make_reason(_forecast_claim(forecast), forecast.id, known))
            sid = suggestion_id(s.instrument, s.tf, as_of, side, [s.id], version)
            req = OrderRequest(sid, side, config.units, entry, stop, target, version)
            quote = Quote(as_of, entry, entry)  # mid only: blackout and count gates ignore spread
            sug = Suggestion(
                id=sid, instrument=s.instrument, tf=s.tf, created_at=as_of, setup_ids=[s.id],
                forecast_id=forecast.id if forecast else None, side=side, entry=entry,
                stop=stop, target=target, score=sc.rank_score, reasons=reasons,
                gates=evaluate_gates(req, quote, gates, list(open_orders or []),
                                     state_known=open_orders is not None),
                rules_version=version, status="not_validated")
            validate_suggestion(sug, known)
            out.append((sug, sc))
        except (EvidenceError, ValueError) as exc:
            rejected.append(Rejected(s.id, str(exc)))
    out.sort(key=lambda p: (-p[0].score, p[0].id))
    out = out[:config.max_items]
    return EngineResult(
        tuple(p[0] for p in out), {p[0].id: p[1] for p in out},
        {i: by_id[i] for p in out for i in p[0].setup_ids}, tuple(rejected), as_of, version)
