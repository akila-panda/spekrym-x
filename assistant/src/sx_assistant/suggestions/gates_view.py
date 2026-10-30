"""Advisory view of the Phase 6 risk gates for a suggestion.

The gates themselves (``risk_gates.py``) are the same classes the paper runner builds from the
frozen rule set; this module only runs them and reports each result. Nothing here places an
order. ``PaperRunner`` applies the gates again, for real, at order time.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime

from sx_assistant.paper.broker import OrderRequest, Quote, RiskGate
from sx_assistant.rules.ruleset import RuleSet
from sx_assistant.suggestions.risk_gates import DailyLossGate, MaxOpenTradesGate, NewsBlackoutGate
from sx_core.contracts import PaperOrder
from sx_core.contracts.suggestion import Gate

NO_STATE = "no paper account state loaded; assumed none; checked again when an order is placed"
_STATE_GATES = ("max_open_trades", "daily_loss_halt")


def build_gates(rules: RuleSet, realized_on: Callable[[datetime], float]) -> list[RiskGate]:
    return [NewsBlackoutGate(rules.blackouts), MaxOpenTradesGate(rules.max_open_trades),
            DailyLossGate(rules.daily_loss_limit, realized_on)]


def evaluate_gates(req: OrderRequest, quote: Quote, gates: Sequence[RiskGate],
                   open_orders: list[PaperOrder], *, state_known: bool) -> list[Gate]:
    out = []
    for g in gates:
        why = g.check(req, quote, open_orders)
        detail = why or "ok"
        if not state_known and g.name in _STATE_GATES:
            detail = f"{detail} ({NO_STATE})"
        out.append(Gate(name=g.name, passed=why is None, detail=detail))
    return out
