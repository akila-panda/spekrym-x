"""Provider and output errors (Phase 9C-1).

Messages never contain keys, request URLs or headers. ``MalformedOutput`` is for a reply that
is not valid JSON or does not fit the brief schema; evidence breaks use ``EvidenceError``.
"""

from __future__ import annotations


class ProviderError(Exception):
    kind = "provider_error"


class RateLimited(ProviderError):
    kind = "rate_limited"

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class Transient(ProviderError):
    """5xx, timeout or network failure. A timeout may still have used quota: never resent."""

    kind = "transient"


class AuthError(ProviderError):
    kind = "auth"


class BadRequest(ProviderError):
    kind = "bad_request"


class MalformedOutput(ValueError):
    kind = "malformed_output"
