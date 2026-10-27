"""FastAPI app factory. Run: ``python -m uvicorn sx_api.main:create_app --factory --port 8000``.

The factory refuses to start unless ``SX_TRADING_MODE`` is exactly ``paper``. The nearest ``.env``
(working directory or a parent folder) is read; real environment variables win.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sx_api.routes import health, lab, paper, premarket, suggestions
from sx_assistant.premarket.data_source import FixtureSource, MarketDataSource
from sx_core.config import enforce_paper_mode, load_settings

DEV_ORIGINS = [f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 5174, 5175)]


def find_dotenv(start: Path | None = None) -> Path | None:
    """First ``.env`` in ``start`` (default: the working directory) or any parent folder."""
    here = (start or Path.cwd()).resolve()
    return next((d / ".env" for d in (here, *here.parents) if (d / ".env").is_file()), None)


def create_app(source: MarketDataSource | None = None,
               env: Mapping[str, str] | None = None) -> FastAPI:
    if env is None:
        load_settings(dotenv_path=find_dotenv())
    else:
        enforce_paper_mode(env)
    app = FastAPI(title="spekrym-x API", version="0.1.0")
    app.state.source = source or FixtureSource()
    app.state.cache = {}
    app.add_middleware(CORSMiddleware, allow_origins=DEV_ORIGINS, allow_methods=["GET"],
                       allow_headers=["*"])
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": "spekrym-x API", "paper_only": True,
                "try": ["/health", "/premarket", "/docs"]}

    for module in (health, premarket, suggestions, paper, lab):
        app.include_router(module.router)
    return app
