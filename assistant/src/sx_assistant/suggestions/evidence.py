"""Evidence rules (Phase 9B). Every claim in a suggestion links to a known setup or forecast id.

A claim whose evidence id is not in the known set is REJECTED (``EvidenceError``), never kept
with a blank link. Claim wording is also checked: a score is a rank, so words that read as a
probability are refused.
"""

from __future__ import annotations

import math
import re
from collections.abc import Collection

from sx_core.contracts import Suggestion
from sx_core.contracts.suggestion import Reason

_PROBABILITY_WORDS = re.compile(r"probab|chance|likel|odds|win rate|%", re.IGNORECASE)


class EvidenceError(ValueError):
    """A claim has no evidence, or a suggestion breaks the evidence or wording rules."""


def check_wording(text: str) -> None:
    if _PROBABILITY_WORDS.search(text):
        raise EvidenceError(f"probability wording is not allowed in a claim: {text!r}")


def make_reason(text: str, evidence_id: str, known: Collection[str]) -> Reason:
    """Build a claim, or raise if it has no evidence that resolves to a known id."""
    if not text.strip():
        raise EvidenceError("a claim needs text")
    if evidence_id not in known:
        raise EvidenceError(f"claim has no evidence: {evidence_id!r} is not a known "
                            "setup or forecast id")
    check_wording(text)
    return Reason(text=text, evidence_id=evidence_id)


def validate_suggestion(s: Suggestion, known: Collection[str]) -> None:
    """Raise ``EvidenceError`` unless every id and claim in ``s`` resolves."""
    if not s.setup_ids:
        raise EvidenceError("a suggestion needs at least one setup id")
    allowed = set(s.setup_ids) | ({s.forecast_id} if s.forecast_id else set())
    unknown = [i for i in allowed if i not in known]
    if unknown:
        raise EvidenceError(f"ids not found among the evidence: {sorted(unknown)}")
    if not s.reasons:
        raise EvidenceError("a suggestion needs at least one reason")
    for r in s.reasons:
        if r.evidence_id not in allowed:
            raise EvidenceError(f"reason points at {r.evidence_id!r}, which is not one of this "
                                "suggestion's evidence ids")
        check_wording(r.text)
    if not (math.isfinite(s.score) and 0.0 <= s.score <= 100.0):
        raise EvidenceError("score must be a finite rank between 0 and 100")
