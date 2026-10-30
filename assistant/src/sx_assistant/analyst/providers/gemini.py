"""Google Gemini adapter (Generative Language REST API).

Shape used: POST {BASE}/models/{model}:generateContent with the key in the ``x-goog-api-key``
header (never in the URL, so it cannot reach a log), ``systemInstruction``, ``contents`` and
``generationConfig`` (temperature 0, maxOutputTokens). Reply text is the joined ``text`` of
``candidates[0].content.parts``; usage is ``usageMetadata``. The header and endpoint were read
from Google's current docs; the other field names were NOT exercised against the live API from
the build sandbox (see DEPENDENCIES). No JSON mode is requested: our code validates and repairs.
"""

from __future__ import annotations

import hashlib
import time

import httpx
from pydantic import SecretStr

from sx_assistant.analyst.errors import BadRequest, Transient
from sx_assistant.analyst.provider import Completion, ModelSpec
from sx_assistant.analyst.providers._http import send

BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider:
    def __init__(self, spec: ModelSpec, api_key: SecretStr,
                 client: httpx.Client | None = None) -> None:
        self.spec = spec
        self._key = api_key
        self.key_fingerprint = hashlib.sha256(
            api_key.get_secret_value().encode()).hexdigest()[:8]
        self._client = client or httpx.Client()

    def _headers(self) -> dict[str, str]:
        return {"x-goog-api-key": self._key.get_secret_value()}

    def complete(self, system: str, user: str) -> Completion:
        if len(system) + len(user) > self.spec.max_input_chars:
            raise BadRequest("input larger than max_input_chars; not sent")
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": 0,
                                     "maxOutputTokens": self.spec.max_output_tokens}}
        t0 = time.perf_counter()
        data = send(self._client, "POST", f"{BASE}/models/{self.spec.model_id}:generateContent",
                    headers=self._headers(), secret=self._key.get_secret_value(),
                    timeout=self.spec.timeout_s, body=body)
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        except (KeyError, IndexError, TypeError):
            raise Transient("no candidate in reply (blocked or empty)") from None
        if not text.strip():
            raise Transient("empty reply")
        usage = data.get("usageMetadata") or {}
        return Completion(text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"),
                          time.perf_counter() - t0)

    def list_models(self) -> list[str]:
        data = send(self._client, "GET", f"{BASE}/models", headers=self._headers(),
                    secret=self._key.get_secret_value(), timeout=self.spec.timeout_s)
        out = []
        for m in data.get("models", []):
            if isinstance(m, dict) and "generateContent" in (m.get("supportedGenerationMethods")
                                                             or []):
                out.append(str(m.get("name", "")).removeprefix("models/"))
        return sorted(out)
