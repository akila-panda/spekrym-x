"""Routing log (Phase 9C-2): one JSON line per provider attempt. Never prompts, replies or keys.

Records of one request share a ``route_id``; consecutive lines with the same id and a non-ok
outcome followed by another provider are the failover trail.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from sx_assistant.analyst.router import Attempt


def write_routing_log(path: Path, packet_hash: str, attempts: Iterable[Attempt],
                      now: float) -> str:
    stamp = datetime.fromtimestamp(now, UTC).isoformat()
    route_id = hashlib.sha256(f"{packet_hash}{now}".encode()).hexdigest()[:10]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for i, a in enumerate(attempts):
            f.write(json.dumps({"route_id": route_id, "seq": i, "at": stamp,
                                "packet": packet_hash, **dataclasses.asdict(a)}) + "\n")
    return route_id
