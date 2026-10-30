"""Environment loading and the paper-mode guard (docs/PRINCIPLES.md rule 2).

``enforce_paper_mode`` must be the first thing every entry point calls. Anything other
than the exact string ``paper`` (including unset) is refused. ``OANDA_ENV`` must be
``practice``. Secrets are ``SecretStr`` so they never appear in ``repr`` or logs.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, SecretStr


class TradingModeError(RuntimeError):
    """The process was asked to run in a mode other than paper."""


def parse_dotenv(text: str) -> dict[str, str]:
    """Minimal ``KEY=value`` parser: ``#`` comments, blank lines, optional matching quotes."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            out[key] = value
    return out


def enforce_paper_mode(env: Mapping[str, str] | None = None) -> None:
    """Raise ``TradingModeError`` unless ``SX_TRADING_MODE == "paper"`` and OANDA is practice."""
    e = os.environ if env is None else env
    mode = e.get("SX_TRADING_MODE")
    if mode != "paper":
        raise TradingModeError(
            f"SX_TRADING_MODE must be exactly 'paper' (got {mode!r}); refusing to start")
    oanda = e.get("OANDA_ENV", "practice")
    if oanda != "practice":
        raise TradingModeError(
            f"OANDA_ENV must be 'practice' (got {oanda!r}); refusing to start")


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    trading_mode: str = "paper"
    oanda_env: str = "practice"
    oanda_token: SecretStr = SecretStr("")
    oanda_account_id: str = ""
    ib_host: str = "127.0.0.1"
    ib_port: int = 7497
    ib_client_id: int = 1
    anthropic_api_key: SecretStr = SecretStr("")
    groq_api_key: SecretStr = SecretStr("")
    gemini_api_key: SecretStr = SecretStr("")


def load_settings(env: Mapping[str, str] | None = None, dotenv_path: str | Path | None = None
                  ) -> Settings:
    """Merge ``dotenv_path`` (if it exists) under the environment, guard, then build Settings.

    Real environment variables win over the file. The guard runs on the merged values.
    """
    merged: dict[str, str] = {}
    if dotenv_path is not None and Path(dotenv_path).is_file():
        merged.update(parse_dotenv(Path(dotenv_path).read_text()))
    merged.update(os.environ if env is None else env)
    enforce_paper_mode(merged)
    g = merged.get
    return Settings(
        trading_mode=g("SX_TRADING_MODE", "paper"),
        oanda_env=g("OANDA_ENV", "practice"),
        oanda_token=SecretStr(g("OANDA_TOKEN", "")),
        oanda_account_id=g("OANDA_ACCOUNT_ID", ""),
        ib_host=g("IB_HOST", "127.0.0.1"),
        ib_port=int(g("IB_PORT", "7497")),
        ib_client_id=int(g("IB_CLIENT_ID", "1")),
        anthropic_api_key=SecretStr(g("ANTHROPIC_API_KEY", "")),
        groq_api_key=SecretStr(g("GROQ_API_KEY", "")),
        gemini_api_key=SecretStr(g("GEMINI_API_KEY", "")),
    )
