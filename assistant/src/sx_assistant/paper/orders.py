"""Order helpers: request validation, idempotent ids, kill switch."""

from __future__ import annotations

import math

from sx_assistant.paper.broker import OrderRequest
from sx_core.contracts.ids import order_id


def request_order_id(req: OrderRequest, backend: str) -> str:
    """Same suggestion, backend, side and rules always give the same id (no prices)."""
    return order_id(req.suggestion_id, backend, req.side, req.rules_version)


def validate_request(req: OrderRequest) -> str | None:
    """Return a reason the request is unusable, or ``None``."""
    nums = (req.units, req.entry, req.stop, req.target)
    if not all(math.isfinite(x) for x in nums):
        return "non-finite number in request"
    if req.units <= 0:
        return "units must be positive"
    if req.side == "long" and not (req.stop < req.entry < req.target):
        return "long needs stop < entry < target"
    if req.side == "short" and not (req.target < req.entry < req.stop):
        return "short needs target < entry < stop"
    return None


class KillSwitch:
    """Once tripped, no new order is accepted until ``reset`` is called on purpose."""

    def __init__(self) -> None:
        self._reason: str | None = None

    @property
    def tripped(self) -> bool:
        return self._reason is not None

    @property
    def reason(self) -> str | None:
        return self._reason

    def trip(self, reason: str) -> None:
        self._reason = reason or "kill switch tripped"

    def reset(self) -> None:
        self._reason = None
