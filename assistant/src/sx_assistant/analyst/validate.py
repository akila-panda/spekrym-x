"""Output checks for the analyst (Phase 9C-1). Application code decides, never the model.

Order: parse JSON -> fit the schema -> every cited id must exist in the packet -> wording
(no probability language, no trade instructions) -> numbers. A bad id or wording REJECTS the
whole reply (it can be repaired once by the router). A number in a claim that is not found in
the cited evidence marks only that claim ``unverified``; a valid id never proves a claim.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal

from pydantic import ValidationError

from sx_assistant.analyst.brief_types import BriefDraft, CheckedClaim
from sx_assistant.analyst.errors import MalformedOutput
from sx_assistant.analyst.packet import EvidencePacket
from sx_assistant.suggestions.evidence import EvidenceError, check_wording

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w)")
# "buy-side liquidity" and "sell-side liquidity" are structure terms, not instructions.
_DIRECTIVE = re.compile(
    r"\b(?:buy|sell)\b(?![- ]?side)|\bgo (?:long|short)\b|\benter (?:a |the )?(?:long|short|trade|"
    r"position)\b|\bplace (?:an? |the )?order\b|\btake profit\b", re.IGNORECASE)


def parse_draft(text: str) -> BriefDraft:
    body = _FENCE.sub("", text.strip())
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end <= start:
        raise MalformedOutput("reply contains no JSON object")
    try:
        raw = json.loads(body[start:end + 1])
    except ValueError as e:
        raise MalformedOutput(f"reply is not valid JSON: {e}") from None
    try:
        return BriefDraft.model_validate(raw)
    except ValidationError as e:
        bad = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()[:3])
        raise MalformedOutput(f"reply does not fit the schema: {bad}") from None


def _numbers(text: str) -> set[Decimal]:
    return {Decimal(m) for m in _NUM.findall(text)}


def check_draft(draft: BriefDraft, packet: EvidencePacket) -> list[CheckedClaim]:
    items = packet.by_id()
    texts = [draft.headline, *draft.caveats] + [c.text for c in draft.claims]
    for t in texts:
        check_wording(t)
        if _DIRECTIVE.search(t):
            raise EvidenceError(f"trade instruction wording is not allowed: {t!r}")
    out: list[CheckedClaim] = []
    for c in draft.claims:
        unknown = [i for i in c.evidence_ids if i not in items]
        if unknown:
            raise EvidenceError(f"claim cites ids not in the evidence packet: {unknown}")
        known = set()
        for i in c.evidence_ids:
            known |= _numbers(items[i].text) | _numbers(i)
        missing = sorted(_numbers(c.text) - known)
        if missing:
            out.append(CheckedClaim(
                text=c.text, evidence_ids=c.evidence_ids, status="unverified",
                note="number(s) not found in the cited evidence: "
                     + ", ".join(str(m.normalize()) for m in missing)))
        else:
            out.append(CheckedClaim(text=c.text, evidence_ids=c.evidence_ids,
                                    status="supported"))
    return out
