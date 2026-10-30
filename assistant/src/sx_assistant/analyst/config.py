"""Which providers and models the analyst may use (Phase 9C-1; the $0 rule lives here).

A model is usable only if it is listed in ``approved_models.json`` AND the owner has set
``owner_confirmed_free`` for it. Keys come from ``Settings`` (never from code or the repo).
Nothing here can enable billing, buy credits or reach a paid model: an unlisted model id
raises ``ApprovalError``.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from sx_assistant.analyst.provider import ModelSpec, Provider
from sx_assistant.analyst.providers.gemini import GeminiProvider
from sx_assistant.analyst.providers.groq import GroqProvider
from sx_core.config import Settings, parse_dotenv

APPROVED_PATH = Path(__file__).with_name("approved_models.json")
DEFAULT_ORDER = ("groq", "gemini")
DEFAULT_MODELS = {"groq": "openai/gpt-oss-20b", "gemini": "gemini-3.8-flash"}
DEFAULT_DAILY_CAP = 50   # local safety cap per provider per UTC day (provisional)
_CLASSES = {"groq": GroqProvider, "gemini": GeminiProvider}


class ApprovalError(RuntimeError):
    """A model is not approved for use. The message says exactly what to change."""


@dataclass(frozen=True)
class ProviderSetup:
    providers: list[Provider]
    skipped: dict[str, str] = field(default_factory=dict)   # provider id -> why not used
    caps: dict[str, int] = field(default_factory=dict)      # provider id -> local daily cap


def load_env(dotenv_path: Path | None = None) -> dict[str, str]:
    """``.env`` values under the real environment (the environment wins), for model overrides."""
    merged: dict[str, str] = {}
    if dotenv_path is not None and Path(dotenv_path).is_file():
        merged.update(parse_dotenv(Path(dotenv_path).read_text()))
    merged.update(os.environ)
    return merged


def load_approved(path: Path = APPROVED_PATH) -> dict[tuple[str, str], dict]:
    raw = json.loads(Path(path).read_text())
    return {(m["provider"], m["model"]): m for m in raw["models"]}


def build_providers(settings: Settings, env: Mapping[str, str] | None = None, *,
                    client: httpx.Client | None = None, approved_path: Path = APPROVED_PATH,
                    require_confirmed: bool = True) -> ProviderSetup:
    e = env or {}
    keys = {"groq": settings.groq_api_key, "gemini": settings.gemini_api_key}
    order = [p.strip() for p in e.get("SX_ANALYST_ORDER", ",".join(DEFAULT_ORDER)).split(",")
             if p.strip()]
    approved = load_approved(approved_path)
    providers: list[Provider] = []
    skipped: dict[str, str] = {}
    caps: dict[str, int] = {}
    unconfirmed: list[str] = []
    for pid in order:
        if pid not in _CLASSES:
            raise ApprovalError(f"unknown provider {pid!r} in SX_ANALYST_ORDER")
        key = keys[pid]
        if not key.get_secret_value():
            skipped[pid] = f"no key (set {pid.upper()}_API_KEY in .env)"
            continue
        model = e.get(f"SX_{pid.upper()}_MODEL", DEFAULT_MODELS[pid])
        entry = approved.get((pid, model))
        if entry is None:
            raise ApprovalError(f"{pid} model {model!r} is not in approved_models.json; "
                                "only listed models can be used")
        if require_confirmed and not entry.get("owner_confirmed_free"):
            msg = (f"{pid} model {model!r} is not confirmed free. After checking the {pid} "
                   "console, set owner_confirmed_free to true (and confirmed_on) in "
                   "approved_models.json")
            unconfirmed.append(msg)
            skipped[pid] = "not confirmed free (owner_confirmed_free is false); never called"
            continue
        providers.append(_CLASSES[pid](ModelSpec(pid, model), key, client))
        caps[pid] = int(entry.get("max_requests_per_day", DEFAULT_DAILY_CAP))
    if unconfirmed and not providers:       # nothing confirmed at all: refuse loudly
        raise ApprovalError(unconfirmed[0])
    return ProviderSetup(providers, skipped, caps)
