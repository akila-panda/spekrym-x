"""The one interface the rest of spekrym-x sees (Phase 9C-1, decision P6).

An adapter turns (system, user) text into a ``Completion`` or raises one of the errors in
``errors.py``. Nothing outside ``analyst/providers`` knows which vendor answered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelSpec:
    provider_id: str
    model_id: str
    max_input_chars: int = 24_000     # bounded input: larger requests are refused, not trimmed
    max_output_tokens: int = 2_000
    timeout_s: float = 45.0


@dataclass(frozen=True)
class Completion:
    text: str
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_s: float


class Provider(Protocol):
    spec: ModelSpec
    key_fingerprint: str     # short hash of the key; lets state notice a replaced key

    def complete(self, system: str, user: str) -> Completion: ...

    def list_models(self) -> list[str]:
        """Model ids this key can see (used by ``check``; makes no generation request)."""
