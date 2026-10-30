"""Shared HTTP helpers for the adapters: one place that maps failures to ``errors.py``."""

from __future__ import annotations

from typing import Any

import httpx

from sx_assistant.analyst.errors import (AuthError, BadRequest, RateLimited, Transient)


def _retry_after(resp: httpx.Response) -> float | None:
    raw = resp.headers.get("retry-after")
    try:
        return max(0.0, float(raw)) if raw is not None else None
    except ValueError:
        return None


def _detail(resp: httpx.Response, secret: str) -> str:
    try:
        err = resp.json().get("error")
        text = err.get("message", "") if isinstance(err, dict) else str(err or "")
    except (ValueError, AttributeError):
        text = ""
    text = text.replace(secret, "***") if secret else text
    return text[:200]


def raise_for_status(resp: httpx.Response, secret: str) -> None:
    s = resp.status_code
    if s < 400:
        return
    if s == 429:
        raise RateLimited("HTTP 429 rate limited", _retry_after(resp))
    if s in (401, 403):
        raise AuthError(f"HTTP {s}: credentials or access refused")
    if s == 408 or s >= 500:
        raise Transient(f"HTTP {s}")
    raise BadRequest(f"HTTP {s} {_detail(resp, secret)}".strip())


def send(client: httpx.Client, method: str, url: str, *, headers: dict[str, str],
         secret: str, timeout: float, body: dict[str, Any] | None = None) -> Any:
    """One request, no retry. Returns the parsed JSON body."""
    try:
        resp = client.request(method, url, headers=headers, json=body, timeout=timeout)
    except httpx.TimeoutException:
        raise Transient("timeout (the request may still have used quota)") from None
    except httpx.HTTPError as e:
        raise Transient(f"network error: {type(e).__name__}") from None
    raise_for_status(resp, secret)
    try:
        return resp.json()
    except ValueError:
        raise Transient("response was not JSON") from None
