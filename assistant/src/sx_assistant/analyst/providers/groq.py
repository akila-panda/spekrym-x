"""Groq adapter (OpenAI-compatible chat completions).

Shape used: POST {BASE}/chat/completions with a bearer key, ``messages``, ``temperature`` 0 and
``max_completion_tokens``; reply text at ``choices[0].message.content``; usage at ``usage``.
Models: GET {BASE}/models. These shapes come from the OpenAI-compatible API Groq documents; the
exact parameter names were NOT exercised against the live API from the build sandbox (see
DEPENDENCIES). No JSON mode is requested: output is validated and repaired by our own code.
"""

from __future__ import annotations

import hashlib
import time

import httpx
from pydantic import SecretStr

from sx_assistant.analyst.errors import BadRequest, Transient
from sx_assistant.analyst.provider import Completion, ModelSpec
from sx_assistant.analyst.providers._http import send

BASE = "https://api.groq.com/openai/v1"


class GroqProvider:
    def __init__(self, spec: ModelSpec, api_key: SecretStr,
                 client: httpx.Client | None = None) -> None:
        self.spec = spec
        self._key = api_key
        self.key_fingerprint = hashlib.sha256(
            api_key.get_secret_value().encode()).hexdigest()[:8]
        self._client = client or httpx.Client()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._key.get_secret_value()}"}

    def complete(self, system: str, user: str) -> Completion:
        if len(system) + len(user) > self.spec.max_input_chars:
            raise BadRequest("input larger than max_input_chars; not sent")
        body = {"model": self.spec.model_id, "temperature": 0,
                "max_completion_tokens": self.spec.max_output_tokens,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        t0 = time.perf_counter()
        data = send(self._client, "POST", f"{BASE}/chat/completions", headers=self._headers(),
                    secret=self._key.get_secret_value(), timeout=self.spec.timeout_s, body=body)
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise Transient("unexpected response shape") from None
        if not isinstance(text, str) or not text.strip():
            raise Transient("empty reply")
        usage = data.get("usage") or {}
        return Completion(text, usage.get("prompt_tokens"), usage.get("completion_tokens"),
                          time.perf_counter() - t0)

    def list_models(self) -> list[str]:
        data = send(self._client, "GET", f"{BASE}/models", headers=self._headers(),
                    secret=self._key.get_secret_value(), timeout=self.spec.timeout_s)
        return sorted(m["id"] for m in data.get("data", []) if isinstance(m, dict) and "id" in m)
