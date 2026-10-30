"""Direct ``httpx`` client for the OANDA **practice** candles endpoint. No ``oandapyV20``.

Safety: refuses to build unless ``SX_TRADING_MODE=paper`` and ``OANDA_ENV=practice``, and only
ever talks to the practice host. The token is a ``SecretStr``, is sent only in the
``Authorization`` header, and never appears in errors, ``repr`` or logs.

Only fixed-length granularities that align to UTC are fetchable (M1 to H1). H4 and D are not:
OANDA aligns them differently (daily alignment), while this project builds H4 and D from M1 at
00:00 UTC (decision X10). Use ``resample`` for those.

Not verified in this session: behaviour against the live API (no network route to OANDA from
the sandbox). Request and response shapes follow OANDA's documented v20 candles endpoint as
recalled; tests use ``httpx.MockTransport`` and frozen fixtures only.
"""

from __future__ import annotations

import time as _time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import SecretStr

from sx_core.config import TradingModeError, enforce_paper_mode
from sx_core.contracts import Candle
from sx_core.contracts._base import Tf, format_utc
from sx_data.errors import OandaError
from sx_data.oanda_parse import parse_candles

PRACTICE_HOST = "https://api-fxpractice.oanda.com"
FETCHABLE: frozenset[str] = frozenset({"M1", "M5", "M15", "M30", "H1"})
MAX_PAGE = 5000  # OANDA's documented per-request candle cap


class OandaClient:
    def __init__(
        self,
        token: SecretStr,
        *,
        base_url: str = PRACTICE_HOST,
        env: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = _time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        page_size: int = MAX_PAGE,
        max_retries: int = 4,
        min_interval: float = 0.05,
        timeout: float = 30.0,
    ) -> None:
        enforce_paper_mode(env)
        if base_url != PRACTICE_HOST:
            raise TradingModeError(f"only the OANDA practice host is allowed (got {base_url!r})")
        if not token.get_secret_value():
            raise OandaError("OANDA_TOKEN is empty")
        if not 1 <= page_size <= MAX_PAGE:
            raise ValueError(f"page_size must be 1..{MAX_PAGE}")
        self._sleep = sleep
        self._now = now
        self._page = page_size
        self._retries = max_retries
        self._min_interval = min_interval
        self._last_call = 0.0
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token.get_secret_value()}",
                     "Accept-Datetime-Format": "RFC3339"},
            timeout=timeout,
            transport=transport,
        )

    def __repr__(self) -> str:
        return f"OandaClient(host={PRACTICE_HOST!r}, token=***)"

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> OandaClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- transport -------------------------------------------------------------------------
    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        for attempt in range(self._retries + 1):
            wait = self._min_interval - (_time.monotonic() - self._last_call)
            if wait > 0:
                self._sleep(wait)
            self._last_call = _time.monotonic()
            try:
                resp = self._http.get(path, params=params)
            except httpx.TransportError as exc:
                if attempt == self._retries:
                    raise OandaError(f"network error: {type(exc).__name__}") from None
                self._sleep(min(2.0**attempt, 30.0))
                continue
            if resp.status_code == 200:
                body = resp.json()
                if not isinstance(body, dict):
                    raise OandaError("unexpected response body", 200)
                return body
            retryable = resp.status_code == 429 or resp.status_code >= 500
            if retryable and attempt < self._retries:
                self._sleep(_retry_delay(resp, attempt))
                continue
            raise OandaError(_describe(resp), resp.status_code)
        raise OandaError("retries exhausted")  # pragma: no cover

    # -- candles ---------------------------------------------------------------------------
    def fetch_candles(self, instrument: str, tf: Tf, start: datetime, end: datetime
                      ) -> list[Candle]:
        """Closed candles with ``start <= time < end``, oldest first, with bid/ask close.

        Pages forward from ``start`` using ``from`` + ``count`` (never ``to`` together with
        ``count``). The still-forming candle is dropped. ``end`` is clamped to now.
        """
        if tf not in FETCHABLE:
            raise ValueError(f"{tf} is not fetched from the broker; build it with resample()")
        for name, t in (("start", start), ("end", end)):
            if t.tzinfo is None or t.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        start, end = start.astimezone(UTC), min(end.astimezone(UTC), self._now())
        out: list[Candle] = []
        cursor, include_first = start, True
        while cursor < end:
            payload = self._get(f"/v3/instruments/{instrument}/candles", {
                "price": "MBA", "granularity": tf, "from": format_utc(cursor),
                "count": str(self._page), "includeFirst": "true" if include_first else "false",
            })
            page = parse_candles(payload, instrument, tf)
            if not page:
                break
            last = page[-1].time
            if not include_first and last <= cursor:
                raise OandaError("pagination made no progress")
            added = 0
            for c in page:
                if c.complete and start <= c.time < end and (not out or c.time > out[-1].time):
                    out.append(c)
                    added += 1
            # A short page is NOT the end: the real API can return fewer than ``count`` on a
            # follow-up page (a 5000-candle request gave 4999), which once cut a download off
            # five months early. Stop only at ``end`` or when a page adds no new closed bar.
            if last >= end or added == 0:
                break
            cursor, include_first = last, False
        return out


def _retry_delay(resp: httpx.Response, attempt: int) -> float:
    header = resp.headers.get("Retry-After", "")
    try:
        return min(max(float(header), 0.0), 60.0)
    except ValueError:
        return min(2.0**attempt, 30.0)


def _describe(resp: httpx.Response) -> str:
    """A short, header-free description of a failed response."""
    detail = ""
    try:
        body = resp.json()
        if isinstance(body, dict):
            detail = str(body.get("errorMessage", ""))[:200]
    except ValueError:
        pass
    hint = " (check the practice token and account region)" \
        if resp.status_code in (401, 403) else ""
    return f"OANDA returned HTTP {resp.status_code}{': ' + detail if detail else ''}{hint}"
