"""Static daily brief: one labelled figure, as HTML (always) or PNG/PDF (needs Chrome).

Colours are the light-theme tokens of docs/UI_DESIGN.md. The figure carries the source label,
the honesty labels and the "not a forecast" line; it draws only what the analysis already holds
(closed bars, causal levels). PNG and PDF export go through kaleido, which needs Google Chrome
installed; HTML needs nothing extra. Install: ``pip install -e "assistant[report]"``.
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go

from sx_assistant.premarket.builder import PremarketAnalysis
from sx_assistant.premarket.chart_payload import DISCLAIMER, session_bands

BG, SURFACE, BORDER, TEXT, MUTED = "#FAF9F5", "#FFFFFF", "#E4DFD3", "#1F1E1D", "#6B665D"
BULL, BEAR = "#2E8B64", "#C2453B"
SESSION_COLOUR = {"asia": "#3B8394", "london": "#A9812A", "ny": "#6F5CC4"}
MAX_LEVELS = 8  # the levels nearest to the last close; a brief is not a dump of every object


def _session_key(plain_text: str) -> str:
    t = plain_text.lower()
    return "asia" if t.startswith("asia") else "london" if t.startswith("london") \
        else "ny" if t.startswith("new york") else "prior"


def build_figure(a: PremarketAnalysis) -> go.Figure:
    last = a.candles[-1].close
    levels = [s for s in a.setups if s.kind == "session_level"]
    levels = sorted(levels, key=lambda s: abs(s.geometry.price_low - last))[:MAX_LEVELS]
    fig = go.Figure(go.Candlestick(
        x=[c.time for c in a.candles], open=[c.open for c in a.candles],
        high=[c.high for c in a.candles], low=[c.low for c in a.candles],
        close=[c.close for c in a.candles], name=a.instrument,
        increasing_line_color=BULL, decreasing_line_color=BEAR))
    for b in session_bands(a.candles[0].time, a.as_of):
        fig.add_vrect(x0=b["t_start"], x1=min(b["t_end"], a.as_of.strftime("%Y-%m-%dT%H:%M:%SZ")),
                      fillcolor=SESSION_COLOUR[b["name"]], opacity=0.07, line_width=0)
    for s in levels:
        key = _session_key(s.plain_text)
        fig.add_hline(y=s.geometry.price_low, line_dash="dash", line_width=1,
                      line_color=SESSION_COLOUR.get(key, MUTED),
                      annotation_text=s.plain_text.split(" (")[0], annotation_position="top left",
                      annotation_font_size=10, annotation_font_color=MUTED)
    facts = "<br>".join(f"{i.tf}: {i.text}" for i in a.checklist) or "No higher-timeframe facts."
    fig.update_layout(
        title=dict(text=f"{a.instrument.replace('_', '/')} premarket brief · as of "
                        f"{a.as_of:%Y-%m-%d %H:%M} UTC<br><sub>{a.source.label} · Causal · "
                        f"Not validated · data {a.data_version}</sub>", x=0.01),
        paper_bgcolor=BG, plot_bgcolor=SURFACE, font=dict(color=TEXT, size=12),
        xaxis=dict(rangeslider=dict(visible=False), gridcolor=BORDER),
        yaxis=dict(gridcolor=BORDER, tickformat=".5f"), showlegend=False,
        margin=dict(l=60, r=30, t=90, b=150), width=1100, height=700,
        annotations=[dict(x=0, y=-0.12, xref="paper", yref="paper", xanchor="left", yanchor="top",
                          align="left", showarrow=False, font=dict(size=11, color=MUTED),
                          text=f"{facts}<br><b>{a.source.label}.</b> {DISCLAIMER}")])
    return fig


def write_brief(a: PremarketAnalysis, path: str | Path) -> Path:
    """Write the brief. ``.html`` always works; ``.png`` / ``.pdf`` need kaleido and Chrome."""
    p, fig = Path(path), build_figure(a)
    ext = p.suffix.lower()
    if ext == ".html":
        fig.write_html(p, include_plotlyjs="cdn")
    elif ext in (".png", ".pdf"):
        try:
            fig.write_image(p)
        except RuntimeError as exc:  # kaleido raises this when Chrome is missing
            raise RuntimeError(f"{ext} export needs Google Chrome (kaleido): {exc}") from exc
    else:
        raise ValueError(f"unsupported brief format {ext!r}; use .html, .png or .pdf")
    return p
