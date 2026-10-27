"""The only supported way to run paper orders: frozen rules, gates on every order, ledger.

The broker is private. Orders reach it only through ``submit``, which stamps the run's
``rules_version`` (rules name plus hash) on the request and applies the gates built from
the frozen rules. The runner refuses to start on live mode or on rules that changed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from sx_assistant.paper.broker import OrderRequest, Quote
from sx_assistant.paper.orders import KillSwitch
from sx_assistant.paper.sim_broker import DEFAULT_SLIPPAGE, SimBroker
from sx_assistant.paper.tracker import Tracker
from sx_assistant.rules.ruleset import rules_version, verify_frozen
from sx_assistant.suggestions.risk_gates import DailyLossGate, MaxOpenTradesGate, NewsBlackoutGate
from sx_core.config import enforce_paper_mode
from sx_core.contracts import PaperOrder
from sx_core.ledger import Ledger


class PaperRunner:
    backend = "sim"

    def __init__(self, rules_path: str | Path, *, ledger: Ledger | None = None,
                 data_version: str = "sim", slippage: float = DEFAULT_SLIPPAGE,
                 env: Mapping[str, str] | None = None) -> None:
        enforce_paper_mode(env)
        self.rules, self.rules_hash = verify_frozen(rules_path)
        self.rules_version = rules_version(self.rules, self.rules_hash)
        self.kill_switch = KillSwitch()
        self.tracker = Tracker(ledger, data_version)
        gates = [NewsBlackoutGate(self.rules.blackouts),
                 MaxOpenTradesGate(self.rules.max_open_trades),
                 DailyLossGate(self.rules.daily_loss_limit, self._realized_on)]
        self._broker = SimBroker(slippage=slippage, gates=gates, kill_switch=self.kill_switch,
                                 listener=self.tracker.record, env=env)
        if ledger is not None:
            ledger.append("run_started", {"rules_hash": self.rules_hash,
                                          "rules": self.rules.to_wire()},
                          data_version, rules_version=self.rules_version)

    def _realized_on(self, when: datetime) -> float:
        day = when.date()
        return sum(o.pnl or 0.0 for o in self._broker.orders()
                   if o.state == "closed" and o.closed_at is not None and o.closed_at.date() == day)

    def submit(self, req: OrderRequest, quote: Quote) -> PaperOrder:
        return self._broker.submit(replace(req, rules_version=self.rules_version), quote)

    def on_quote(self, quote: Quote) -> list[PaperOrder]:
        return self._broker.on_quote(quote)

    def cancel(self, order_id: str, quote: Quote) -> PaperOrder:
        return self._broker.cancel(order_id, quote)

    def close_all(self, quote: Quote) -> list[PaperOrder]:
        return self._broker.close_all(quote)

    def orders(self) -> list[PaperOrder]:
        return self._broker.orders()

    def kill(self, reason: str) -> None:
        self.kill_switch.trip(reason)
