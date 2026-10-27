"""Honesty labels (docs/PRINCIPLES.md rule 3) and helpers.

The five labels are the only status values any record may carry. Each contract
accepts a subset (see ``SetupStatus``, ``ForecastStatus``).
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Literal


class StatusLabel(StrEnum):
    SAMPLE = "sample"
    EXPLORATORY = "exploratory"
    NOT_VALIDATED = "not_validated"
    RETROSPECTIVE = "retrospective"
    CAUSAL = "causal"


DISPLAY_NAMES: dict[StatusLabel, str] = {
    StatusLabel.SAMPLE: "Sample data",
    StatusLabel.EXPLORATORY: "Exploratory",
    StatusLabel.NOT_VALIDATED: "Not validated",
    StatusLabel.RETROSPECTIVE: "Retrospective",
    StatusLabel.CAUSAL: "Causal",
}

# Subsets allowed by docs/CONTRACTS.md.
SetupStatus = Literal["causal", "retrospective"]
ForecastStatus = Literal["exploratory", "not_validated"]
SuggestionStatus = Literal["not_validated"]


class RetrospectiveInputError(ValueError):
    """A Retrospective object was offered to a model or a paper trade."""


def display_name(label: StatusLabel | str) -> str:
    """Human-readable name for a label, e.g. ``not_validated`` -> ``Not validated``."""
    return DISPLAY_NAMES[StatusLabel(label)]


def assert_not_retrospective(objects: Iterable[object]) -> None:
    """Principle 1: retrospective analysis never feeds a model or a paper trade.

    Call this at the boundary where objects enter a model or a suggestion.
    Objects without a ``status`` attribute are ignored.
    """
    for obj in objects:
        if getattr(obj, "status", None) == StatusLabel.RETROSPECTIVE:
            ident = getattr(obj, "id", "?")
            raise RetrospectiveInputError(
                f"retrospective object {ident!r} cannot feed a model or trade")
