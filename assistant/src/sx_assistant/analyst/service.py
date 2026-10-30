"""The analyst as one service object (Phase 9C-2), used by the CLI and the API.

``status`` makes no provider call. ``generate`` first returns a saved brief for the same evidence
packet (same hash) so a repeat never spends quota, unless ``force``. Only one generation runs at
a time: a second request gets ``busy`` instead of a duplicate call. Everything it writes goes to
one folder: ``state.db`` (provider state), ``routing.jsonl`` and ``brief_<hash>.json``.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sx_assistant.analyst.brief import LABELS, generate_brief
from sx_assistant.analyst.config import (ApprovalError, ProviderSetup, load_approved)
from sx_assistant.analyst.log import write_routing_log
from sx_assistant.analyst.packet import EvidencePacket
from sx_assistant.analyst.router import Router
from sx_assistant.analyst.state import SqliteState

SetupFactory = Callable[[bool], ProviderSetup]     # argument: require_confirmed


class AnalystService:
    def __init__(self, out_dir: Path, setup_factory: SetupFactory,
                 clock: Callable[[], float] = time.time) -> None:
        self.dir = Path(out_dir)
        self.state = SqliteState(self.dir / "state.db")
        self._setup = setup_factory
        self._clock = clock
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        now = self._clock()
        try:
            setup = self._setup(False)
        except ApprovalError as e:
            return {"status": "misconfigured", "error": str(e), "providers": [],
                    "labels": LABELS}
        approved = load_approved()
        rows = []
        for p in setup.providers:
            s = self.state.load(p.spec.provider_id, p.spec.model_id)
            s.roll_day(datetime.fromtimestamp(now, UTC).strftime("%Y-%m-%d"))
            conf = bool(approved.get((s.provider, s.model), {}).get("owner_confirmed_free"))
            rows.append({
                "provider": s.provider, "model": s.model, "key_present": True,
                "owner_confirmed_free": conf, "health": s.health(now),
                "cooldown_remaining_s": max(0, round(s.cooldown_until - now)),
                "disabled_reason": s.disabled_reason, "last_error": s.last_error,
                "requests_today_estimate": s.requests_today,
                "tokens_today_estimate": s.tokens_today,
                "daily_cap": setup.caps.get(s.provider)})
        rows += [{"provider": k, "key_present": False, "note": v}
                 for k, v in setup.skipped.items()]
        return {"status": "ok", "providers": rows, "labels": LABELS,
                "note": "Usage figures are local estimates, not the providers' own counts."}

    def _path(self, packet_hash: str) -> Path:
        return self.dir / f"brief_{packet_hash}.json"

    @staticmethod
    def _read_file(path: Path) -> dict[str, Any] | None:
        """The saved file dict ({brief, saved_at}), or None.

        None means the file is unreadable, has the old 9C-1 layout (no ``brief`` key) or was
        written by the offline fake provider. Such a file is never reused, so a demo brief
        can not stand in for a real one."""
        try:
            data = json.loads(path.read_text())
            if data["brief"]["writer"]["provider"] == "fake":
                return None
            return data
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def latest(self) -> dict[str, Any] | None:
        files = sorted(self.dir.glob("brief_*.json"), key=lambda f: f.stat().st_mtime,
                       reverse=True)
        for f in files:
            data = self._read_file(f)
            if data is not None:
                return data
        return None

    def generate(self, packet: EvidencePacket, force: bool = False) -> dict[str, Any]:
        base = {"packet_hash": packet.hash(), "source_label": packet.source_label,
                "labels": LABELS}
        if not self._lock.acquire(blocking=False):
            return {**base, "status": "busy", "reason": "A brief is already being generated."}
        try:
            path = self._path(packet.hash())
            saved = self._read_file(path) if path.exists() and not force else None
            if saved is not None:
                return {**base, "status": "published", "reused": True, "attempts": [],
                        "brief": saved["brief"]}
            try:
                setup = self._setup(True)
            except ApprovalError as e:
                return {**base, "status": "unavailable", "reason": str(e), "attempts": []}
            if not setup.providers:
                return {**base, "status": "unavailable", "attempts": [],
                        "reason": "No provider is usable; nothing was called. "
                                  + "; ".join(f"{k}: {v}" for k, v in setup.skipped.items())}
            router = Router(setup.providers, state=self.state, clock=self._clock,
                            daily_caps=setup.caps)
            result = generate_brief(packet, router)
            write_routing_log(self.dir / "routing.jsonl", packet.hash(), result.route.attempts,
                              self._clock())
            attempts = [{"provider": a.provider, "model": a.model, "outcome": a.outcome,
                         "latency_s": a.latency_s, "detail": a.detail}
                        for a in result.route.attempts]
            if result.brief is None:
                return {**base, "status": "deferred", "reason": result.reason,
                        "attempts": attempts}
            brief = result.brief.model_dump(mode="json")
            path.write_text(json.dumps({"brief": brief, "saved_at": datetime.fromtimestamp(
                self._clock(), UTC).isoformat()}, indent=2))
            return {**base, "status": "published", "reused": False, "attempts": attempts,
                    "brief": brief}
        finally:
            self._lock.release()
