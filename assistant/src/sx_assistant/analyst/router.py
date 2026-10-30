"""Quota-aware failover across providers (Phase 9C). One provider answers each request.

Rules: providers are tried in priority order and the first valid answer wins (others are not
called). A rate limit cools the provider down (``Retry-After`` when sent); a 5xx or timeout cools
it briefly and is NEVER retried on the same provider (a timeout may have used quota); an auth or
bad-request error disables it until the key changes or the owner resets it. A reply that fails
our checks gets ONE repair request per brief in total, then the next provider is tried. A local
daily request cap (estimate) skips a provider before any call. If nothing works the result is
``deferred``: no brief is made up and nothing paid is called. State (cooldowns, disables, usage
estimates) is kept in a ``StateStore``; with ``SqliteState`` it survives restarts. Total calls
per brief are at most ``len(providers) + 1``.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from sx_assistant.analyst.errors import (AuthError, BadRequest, MalformedOutput, RateLimited,
                                         Transient)
from sx_assistant.analyst.provider import Provider
from sx_assistant.analyst.state import MemoryState, ProviderState, StateStore
from sx_assistant.suggestions.evidence import EvidenceError

MAX_COOLDOWN_S = 86_400.0


@dataclass(frozen=True)
class Attempt:
    provider: str
    model: str
    outcome: str      # ok, rate_limited, transient, auth, bad_request, invalid_output, skipped
    latency_s: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class RouteResult:
    status: Literal["ok", "deferred"]
    value: Any
    provider: str | None
    model: str | None
    attempts: list[Attempt] = field(default_factory=list)


def _day(now: float) -> str:
    return datetime.fromtimestamp(now, UTC).strftime("%Y-%m-%d")


class Router:
    def __init__(self, providers: list[Provider], *, state: StateStore | None = None,
                 clock: Callable[[], float] = time.time,
                 daily_caps: Mapping[str, int] | None = None,
                 default_cooldown_s: float = 60.0, transient_cooldown_s: float = 30.0) -> None:
        self.providers = providers
        self.state = state or MemoryState()
        self._clock = clock
        self._caps = dict(daily_caps or {})
        self._default = default_cooldown_s
        self._transient = transient_cooldown_s

    def _prepare(self, p: Provider) -> tuple[ProviderState, str | None]:
        """Load state, roll the day, adopt a changed key; return (state, reason to skip)."""
        s = self.state.load(p.spec.provider_id, p.spec.model_id)
        now = self._clock()
        s.roll_day(_day(now))
        fp = getattr(p, "key_fingerprint", None)
        if fp and s.key_fp != fp:
            if s.key_fp is not None:                 # a different key: old disable is stale
                s.disabled_reason, s.cooldown_until = None, 0.0
            s.key_fp = fp
        self.state.save(s)
        cap = self._caps.get(p.spec.provider_id)
        if s.disabled_reason:
            return s, f"disabled: {s.disabled_reason}"
        if s.cooldown_until > now:
            return s, "cooling down"
        if cap is not None and s.requests_today >= cap:
            return s, f"local daily cap of {cap} requests reached (estimate)"
        return s, None

    def run(self, system: str, user: str, check: Callable[[str], Any]) -> RouteResult:
        attempts: list[Attempt] = []
        repairs_left = 1
        for p in self.providers:
            pid, mid = p.spec.provider_id, p.spec.model_id
            st, skip = self._prepare(p)
            if skip:
                attempts.append(Attempt(pid, mid, "skipped", detail=skip))
                continue
            prompt = user
            while True:
                st.requests_today += 1               # counted before sending (timeouts too)
                self.state.save(st)
                try:
                    comp = p.complete(system, prompt)
                except RateLimited as e:
                    wait = min(e.retry_after if e.retry_after is not None else self._default,
                               MAX_COOLDOWN_S)
                    st.cooldown_until, st.last_error = self._clock() + wait, e.kind
                    attempts.append(Attempt(pid, mid, "rate_limited", detail=str(e)))
                    break
                except Transient as e:
                    st.cooldown_until, st.last_error = self._clock() + self._transient, e.kind
                    attempts.append(Attempt(pid, mid, "transient", detail=str(e)))
                    break
                except (AuthError, BadRequest) as e:
                    st.disabled_reason, st.last_error = f"{e.kind}: {e}", e.kind
                    attempts.append(Attempt(pid, mid, e.kind, detail=str(e)))
                    break
                finally:
                    self.state.save(st)
                st.tokens_today += (comp.prompt_tokens or 0) + (comp.completion_tokens or 0)
                meta = dict(latency_s=comp.latency_s, prompt_tokens=comp.prompt_tokens,
                            completion_tokens=comp.completion_tokens)
                try:
                    value = check(comp.text)
                except (MalformedOutput, EvidenceError) as e:
                    st.last_error = "invalid_output"
                    self.state.save(st)
                    attempts.append(Attempt(pid, mid, "invalid_output", detail=str(e)[:300],
                                            **meta))
                    if repairs_left > 0:
                        repairs_left -= 1
                        prompt = (f"{user}\n\nYour previous reply was rejected: {str(e)[:300]}\n"
                                  "Reply again with the corrected JSON object only.")
                        continue
                    break
                st.last_error, st.last_success_at = None, self._clock()
                self.state.save(st)
                attempts.append(Attempt(pid, mid, "ok", **meta))
                return RouteResult("ok", value, pid, mid, attempts)
            self.state.save(st)
        return RouteResult("deferred", None, None, None, attempts)
