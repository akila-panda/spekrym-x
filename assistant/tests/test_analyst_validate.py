"""Phase 9C-1: evidence packet and output checks (frozen sample, no network)."""

import pytest
from analyst_helpers import reply, sample_packet

from sx_assistant.analyst.errors import MalformedOutput
from sx_assistant.analyst.validate import check_draft, parse_draft
from sx_assistant.suggestions.evidence import EvidenceError


@pytest.fixture(scope="module")
def packet():
    return sample_packet()


def _first(packet, kind):
    return next(i for i in packet.items if i.kind == kind)


def test_packet_is_causal_unique_and_bounded(packet):
    assert len(packet.ids) == len(packet.items) <= 1 + 12 + 20
    assert all(i.known_at <= packet.as_of for i in packet.items)
    assert "ctx:last_close" in packet.ids and packet.source_label.startswith("SAMPLE")
    assert packet.hash() == sample_packet().hash()


def test_valid_reply_is_supported(packet):
    s = _first(packet, "setup")
    claims = check_draft(parse_draft(reply(
        [{"text": "A zone sits between the cited prices.", "evidence_ids": [s.id]}])), packet)
    assert [c.status for c in claims] == ["supported"]


def test_fenced_json_is_accepted(packet):
    s = _first(packet, "setup")
    fenced = "```json\n" + reply([{"text": "Zone noted.", "evidence_ids": [s.id]}]) + "\n```"
    assert parse_draft(fenced).claims[0].evidence_ids == [s.id]


@pytest.mark.parametrize("bad", ["no json here", "{not json}", '{"headline": "x"}'])
def test_malformed_output_is_refused(bad):
    with pytest.raises(MalformedOutput):
        parse_draft(bad)


def test_unknown_evidence_id_rejects_the_reply(packet):
    d = parse_draft(reply([{"text": "A level exists.", "evidence_ids": ["setup:nope"]}]))
    with pytest.raises(EvidenceError, match="not in the evidence packet"):
        check_draft(d, packet)


def test_claim_without_evidence_fails_the_schema():
    with pytest.raises(MalformedOutput):
        parse_draft(reply([{"text": "A level exists.", "evidence_ids": []}]))


@pytest.mark.parametrize("text", ["A 70% chance of a bounce.", "Price is likely to rise.",
                                  "You should buy here.", "Go long on the retest.",
                                  "Place an order above the zone."])
def test_probability_and_trade_wording_is_rejected(packet, text):
    d = parse_draft(reply([{"text": text, "evidence_ids": ["ctx:last_close"]}]))
    with pytest.raises(EvidenceError):
        check_draft(d, packet)


def test_buy_side_liquidity_is_not_a_trade_instruction(packet):
    d = parse_draft(reply([{"text": "Buy-side liquidity was taken.",
                            "evidence_ids": ["ctx:last_close"]}]))
    assert check_draft(d, packet)[0].status in ("supported", "unverified")


def test_invented_number_marks_only_that_claim_unverified(packet):
    s = _first(packet, "setup")
    d = parse_draft(reply([
        {"text": "A zone is noted.", "evidence_ids": [s.id]},
        {"text": "Price reached 9.87654 earlier.", "evidence_ids": [s.id]}]))
    a, b = check_draft(d, packet)
    assert a.status == "supported" and b.status == "unverified" and "9.87654" in b.note


def test_quoted_price_matches_despite_trailing_zeros(packet):
    last = packet.by_id()["ctx:last_close"]
    price = last.text.split("closed at ")[1].rstrip(".")
    d = parse_draft(reply([{"text": f"The latest close was {price}0.",
                            "evidence_ids": ["ctx:last_close"]}]))
    assert check_draft(d, packet)[0].status == "supported"
