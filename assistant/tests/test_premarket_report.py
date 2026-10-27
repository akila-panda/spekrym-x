"""Static brief: labelled, causal figure; HTML export. PNG/PDF need Chrome and are not tested."""

from datetime import UTC, datetime

import pytest

pytest.importorskip("plotly")

from sx_assistant.premarket.builder import build_premarket  # noqa: E402
from sx_assistant.premarket.data_source import SAMPLE_LABEL, FixtureSource  # noqa: E402
from sx_assistant.premarket.report_plotly import MAX_LEVELS, build_figure, write_brief  # noqa: E402

T = datetime(2026, 10, 26, 12, tzinfo=UTC)


@pytest.fixture(scope="module")
def analysis():
    return build_premarket(FixtureSource(), "EUR_USD", T)


def test_figure_carries_labels_and_disclaimer(analysis):
    fig = build_figure(analysis)
    title = fig.layout.title.text
    assert SAMPLE_LABEL in title and "Not validated" in title and "2026-10-26 12:00 UTC" in title
    note = fig.layout.annotations[-1].text
    assert SAMPLE_LABEL in note and "Not a forecast" in note


def test_figure_draws_only_known_bars_and_a_capped_number_of_levels(analysis):
    fig = build_figure(analysis)
    assert len(fig.data[0].x) == len(analysis.candles)
    assert max(fig.data[0].x) < T
    hlines = [s for s in fig.layout.shapes if s.type == "line" and s.y0 == s.y1]
    assert 0 < len(hlines) <= MAX_LEVELS


def test_html_is_written_and_labelled(analysis, tmp_path):
    out = write_brief(analysis, tmp_path / "brief.html")
    text = out.read_text()
    assert out.exists() and "NOT LIVE" in text and "Not a forecast" in text


def test_unknown_format_is_refused(analysis, tmp_path):
    with pytest.raises(ValueError, match="unsupported brief format"):
        write_brief(analysis, tmp_path / "brief.docx")
