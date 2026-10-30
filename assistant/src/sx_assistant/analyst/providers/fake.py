"""Offline providers for tests and the ``--fake`` demo. They never touch the network."""

from __future__ import annotations

import json
from collections.abc import Sequence

from sx_assistant.analyst.errors import ProviderError
from sx_assistant.analyst.packet import EvidencePacket
from sx_assistant.analyst.provider import Completion, ModelSpec


class FakeProvider:
    """Plays a script: each item is reply text (str) or an exception to raise."""

    def __init__(self, provider_id: str, script: Sequence[str | ProviderError],
                 model_id: str = "fake") -> None:
        self.spec = ModelSpec(provider_id, model_id)
        self.key_fingerprint = "fake"
        self._script = list(script)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> Completion:
        self.calls.append((system, user))
        item = self._script.pop(0) if self._script else ProviderError("script exhausted")
        if isinstance(item, Exception):
            raise item
        return Completion(item, 100, 50, 0.01)

    def list_models(self) -> list[str]:
        return [self.spec.model_id]


def echo_reply(packet: EvidencePacket, n: int = 3) -> str:
    """A valid reply built from the packet itself (claim text copied from the evidence)."""
    claims = [{"text": i.text.split(";")[0][:300], "evidence_ids": [i.id]}
              for i in packet.items[:n]]
    return json.dumps({"headline": f"Premarket evidence for {packet.instrument}",
                       "claims": claims, "caveats": ["Offline echo, not a real analyst."]})
