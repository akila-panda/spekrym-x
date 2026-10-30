"""Shared helpers for the Phase 9C analyst tests (frozen sample fixture, no network)."""

import json

from sx_assistant.analyst.packet import build_packet
from sx_assistant.premarket.builder import build_premarket
from sx_assistant.premarket.data_source import FixtureSource


def sample_packet():
    src = FixtureSource()
    inst = src.instruments()[0]
    return build_packet(build_premarket(src, inst, src.last_close(inst)))


def reply(claims, headline="Premarket view", caveats=()):
    return json.dumps({"headline": headline, "claims": claims, "caveats": list(caveats)})
