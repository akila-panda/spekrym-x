import type {
  IChartApi, ISeriesApi, ISeriesPrimitive, ISeriesPrimitivePaneRenderer, ISeriesPrimitivePaneView,
  SeriesAttachedParameter, Time, UTCTimestamp
} from 'lightweight-charts'

export type Band = { id: string; label: string; from: number; to: number }
export type BandStyle = { colors: Record<string, string>; font: string }
type Px = { label: string; left: number; right: number; color: string }

// Maps a band edge to an x pixel. Edges outside the visible range clamp to the pane edge.
export function edgeX(
  t: number, coord: (t: number) => number | null, range: { from: number; to: number } | null, width: number
): number | null {
  const c = coord(t)
  if (c !== null) return c
  if (!range) return null
  if (t <= range.from) return 0
  if (t >= range.to) return width
  return null
}

class Renderer implements ISeriesPrimitivePaneRenderer {
  constructor(private px: Px[], private font: string) {}
  draw() {}
  drawBackground(target: Parameters<ISeriesPrimitivePaneRenderer['draw']>[0]) {
    target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
      ctx.save()
      for (const b of this.px) {
        const l = Math.max(0, b.left), r = Math.min(mediaSize.width, b.right)
        if (r <= l) continue
        ctx.globalAlpha = 0.1; ctx.fillStyle = b.color; ctx.fillRect(l, 0, r - l, mediaSize.height)
        ctx.globalAlpha = 1; ctx.font = this.font; ctx.fillStyle = b.color; ctx.textBaseline = 'top'
        ctx.fillText(b.label, l + 6, 6)
      }
      ctx.restore()
    })
  }
}

class View implements ISeriesPrimitivePaneView {
  px: Px[] = []
  constructor(private owner: SessionBandsPrimitive) {}
  zOrder() { return 'bottom' as const }
  renderer() { return new Renderer(this.px, this.owner.style.font) }
}

export class SessionBandsPrimitive implements ISeriesPrimitive<Time> {
  private chart: IChartApi | null = null
  private series: ISeriesApi<'Candlestick'> | null = null
  private requestUpdate: (() => void) | null = null
  private view = new View(this)
  constructor(private bands: Band[], public style: BandStyle) {}

  attached(p: SeriesAttachedParameter<Time>) {
    this.chart = p.chart as IChartApi; this.series = p.series as ISeriesApi<'Candlestick'>; this.requestUpdate = p.requestUpdate
  }
  detached() { this.chart = null; this.series = null; this.requestUpdate = null }
  setStyle(style: BandStyle) { this.style = style; this.requestUpdate?.() }
  setBands(bands: Band[]) { this.bands = bands; this.requestUpdate?.() }
  paneViews() { return [this.view] }
  updateAllViews() {
    const ts = this.chart?.timeScale(); if (!ts) { this.view.px = []; return }
    const width = ts.width()
    const vr = ts.getVisibleRange()
    const range = vr ? { from: Number(vr.from), to: Number(vr.to) } : null
    const coord = (t: number) => ts.timeToCoordinate(t as UTCTimestamp)
    const out: Px[] = []
    for (const b of this.bands) {
      const l = edgeX(b.from, coord, range, width), r = edgeX(b.to, coord, range, width)
      if (l !== null && r !== null) out.push({ label: b.label, left: l, right: r, color: this.style.colors[b.id] ?? '#888' })
    }
    this.view.px = out
  }
}
