"""FastAPI app factory. Run: ``python -m uvicorn sx_api.main:create_app --factory --port 8000``.

The factory refuses to start unless ``SX_TRADING_MODE`` is exactly ``paper``. The nearest ``.env``
(working directory or a parent folder) is read; real environment variables win.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sx_api.jobs import JobManager
from sx_api.routes import analyst, datasets, exp001, health, lab, paper, premarket, suggestions
from sx_assistant import rules
from sx_assistant.analyst.config import ProviderSetup, build_providers, load_env
from sx_assistant.analyst.service import AnalystService, SetupFactory
from sx_assistant.premarket.data_source import FixtureSource, MarketDataSource
from sx_core.config import Settings, enforce_paper_mode, load_settings
from sx_data.oanda_rest import OandaClient

DEV_ORIGINS = [f"http://{h}:{p}" for h in ("localhost", "127.0.0.1") for p in (5173, 5174, 5175)]


def find_dotenv(start: Path | None = None) -> Path | None:
    """First ``.env`` in ``start`` (default: the working directory) or any parent folder."""
    here = (start or Path.cwd()).resolve()
    return next((d / ".env" for d in (here, *here.parents) if (d / ".env").is_file()), None)


def _oanda_factory(settings: Settings) -> Callable[[], OandaClient]:
    guard = {"SX_TRADING_MODE": settings.trading_mode, "OANDA_ENV": settings.oanda_env}
    return lambda: OandaClient(settings.oanda_token, env=guard)


def create_app(source: MarketDataSource | None = None, env: Mapping[str, str] | None = None,
               client_factory: Callable[[], object] | None = None,
               data_dir: Path | None = None, model_dir: Path | None = None,
               experiments_dir: Path | None = None, rules_path: Path | None = None,
               analyst_dir: Path | None = None,
               analyst_setup: SetupFactory | None = None) -> FastAPI:
    dotenv = find_dotenv() if env is None else None
    settings: Settings | None = None
    if env is None:
        settings = load_settings(dotenv_path=dotenv)
    else:
        enforce_paper_mode(env)
    app = FastAPI(title="spekrym-x API", version="0.1.0")
    app.state.source = source or FixtureSource()
    app.state.cache = {}
    app.state.jobs = JobManager()
    root = dotenv.parent if dotenv else Path.cwd()
    app.state.data_dir = data_dir or root / "lab" / "outputs" / "data"
    app.state.model_dir = model_dir or root / "assistant" / "outputs" / "model"
    app.state.protect_dirs = [experiments_dir or root / "lab" / "experiments",
                              app.state.model_dir]
    app.state.rules_path = rules_path or (
        Path(rules.__file__).parent / "frozen" / "paper_v1.json")
    if analyst_setup is None:
        if settings is None:
            analyst_setup = lambda _c: ProviderSetup([], {"all": "no settings loaded"})  # noqa: E731
        else:
            analyst_env = load_env(dotenv)
            analyst_setup = lambda c: build_providers(  # noqa: E731
                settings, analyst_env, require_confirmed=c)
    app.state.analyst = AnalystService(
        analyst_dir or root / "assistant" / "outputs" / "analyst", analyst_setup)
    app.state.client_factory = client_factory or (_oanda_factory(settings) if settings else None)
    app.state.token_configured = client_factory is not None or bool(
        settings and settings.oanda_token.get_secret_value())
    app.add_middleware(CORSMiddleware, allow_origins=DEV_ORIGINS,
                       allow_methods=["GET", "POST", "DELETE"],
                       allow_headers=["*"])
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": "spekrym-x API", "paper_only": True,
                "try": ["/health", "/premarket", "/docs"]}

    for module in (health, premarket, suggestions, analyst, paper, lab, datasets, exp001):
        app.include_router(module.router)
    return app
