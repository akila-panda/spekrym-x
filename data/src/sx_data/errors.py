"""Errors raised by the data layer. Messages never contain tokens or request headers."""

from __future__ import annotations


class DataError(RuntimeError):
    """Base class for data-layer failures."""


class OandaError(DataError):
    """The OANDA practice API refused or failed a request."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class ParseError(DataError):
    """A broker payload did not have the documented shape."""


class ResampleError(DataError):
    """Input to ``resample`` was not clean enough to aggregate safely."""
