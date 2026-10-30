"""Generate the premarket brief from an evidence packet (Phase 9C-1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sx_assistant.analyst.brief_types import Brief, CheckedClaim, Writer
from sx_assistant.analyst.packet import EvidencePacket
from sx_assistant.analyst.prompts import brief_v1
from sx_assistant.analyst.router import RouteResult, Router
from sx_assistant.analyst.validate import check_draft, parse_draft
from sx_core.labels import DISPLAY_NAMES, StatusLabel

LABELS = [DISPLAY_NAMES[StatusLabel.EXPLORATORY], DISPLAY_NAMES[StatusLabel.NOT_VALIDATED]]
DEFERRED_REASON = ("No brief was produced: every approved free provider was unavailable, "
                   "rate limited or returned output that failed the checks. Nothing was invented "
                   "and nothing paid was called.")


@dataclass(frozen=True)
class BriefResult:
    status: Literal["published", "deferred"]
    brief: Brief | None
    route: RouteResult
    reason: str


def generate_brief(packet: EvidencePacket, router: Router) -> BriefResult:
    def check(text: str) -> tuple[str, list[str], list[CheckedClaim]]:
        draft = parse_draft(text)
        return draft.headline, draft.caveats, check_draft(draft, packet)

    route = router.run(brief_v1.SYSTEM, brief_v1.render_user(packet), check)
    if route.status != "ok":
        return BriefResult("deferred", None, route, DEFERRED_REASON)
    headline, caveats, claims = route.value
    brief = Brief(instrument=packet.instrument, as_of=packet.as_of.isoformat(),
                  headline=headline, claims=claims, caveats=caveats, labels=LABELS,
                  source_label=packet.source_label, packet_hash=packet.hash(),
                  prompt_version=brief_v1.VERSION,
                  writer=Writer(provider=route.provider or "", model=route.model or ""))
    return BriefResult("published", brief, route, "ok")
