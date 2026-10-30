"""Typed shapes for the analyst brief (Phase 9C-1).

``BriefDraft`` is what the model must return. ``Brief`` is what the app keeps after our checks:
every claim carries a ``supported`` or ``unverified`` status. Labels are fixed: the analyst is
Exploratory and Not validated, and the writer (provider and model) is always recorded.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _M(BaseModel):
    model_config = ConfigDict(extra="ignore")


class BriefClaim(_M):
    text: str = Field(min_length=3, max_length=400)
    evidence_ids: list[str] = Field(min_length=1, max_length=6)


class BriefDraft(_M):
    headline: str = Field(min_length=3, max_length=200)
    claims: list[BriefClaim] = Field(min_length=1, max_length=12)
    caveats: list[str] = Field(default_factory=list, max_length=5)


class CheckedClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    evidence_ids: list[str]
    status: Literal["supported", "unverified"]
    note: str | None = None


class Writer(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str
    model: str


class Brief(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: Literal["analyst_brief"] = "analyst_brief"
    instrument: str
    as_of: str
    headline: str
    claims: list[CheckedClaim]
    caveats: list[str]
    labels: list[str]
    source_label: str
    packet_hash: str
    prompt_version: str
    writer: Writer
