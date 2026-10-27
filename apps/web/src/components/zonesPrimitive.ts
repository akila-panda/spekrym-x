import type {
  IChartApi, ISeriesApi, ISeriesPrimitive, ISeriesPrimitivePaneRenderer, ISeriesPrimitivePaneView,
  SeriesAttachedParameter, Time, UTCTimestamp
} from 'lightweight-charts'
import { edgeX } from './sessionBandsPrimitive'

// A zone (FVG, order block) is a box; a structure line (BOS, CHoCH) is a thin line with a tag.
// tEnd undefined means "to the right edge" (the zone is still current at the chart's last time).
export type ZoneDraw = {
  id: string; tag: string; kind: 'zone' | 'line'; low: number; high: number
  tStart: number; tEnd?: number; color: string; faded: boolean; selected: boolean
}
type Px = { z: ZoneDraw; l: number; r: number; top: number; bottom: number }

class Renderer implements ISeriesPrimitivePaneRenderer {
  constructor(private px: Px[], private font: string) {}
  draw() {}
  drawBackground(target: Parameters<ISeriesPrimitivePaneRenderer['draw']>[0]) {
    target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
      ctx.save(); ctx.font = this.font; ctx.textBaseline = 'top'
      for (const { z, l, r, top, bottom } of this.px) {
        const x0 = Math.max(0, l), x1 = Math.min(mediaSize.width, r)
        if (x1 <= x0) continue
        ctx.strokeStyle = z.color; ctx.fillStyle = z.color
        ctx.lineWidth = z.selected ? 2 : 1
        if (z.kind === 'zone') {
          ctx.globalAlpha = z.faded ? 0.06 : 0.14
          ctx.fillRect(x0, top, x1 - x0, Math.max(1, bottom - top))
          ctx.globalAlpha = z.faded ? 0.3 : 0.7
          ctx.strokeRect(x0 + 0.5, top + 0.5, x1 - x0, Math.max(1, bottom - top))
        } else {
          ctx.globalAlpha = z.faded ? 0.4 : 0.9
          ctx.beginPath(); ctx.moveTo(x0, top); ctx.lineTo(x1, top); ctx.stroke()
        }
        ctx.globalAlpha = z.faded ? 0.5 : 1
        ctx.fillText(z.tag, x0 + 3, top + (z.kind === 'zone' ? 2 : -13))
      }
      ctx.restore()
    })
  }
}

class View implements ISeriesPrimitivePaneView {
  px: Px[] = []
  constructor(private owner: ZonesPrimitive) {}
  zOrder() { return 'bottom' as const }
  renderer() { return new Renderer(this.px, this.owner.font) }
}

export class ZonesPrimitive implements ISeriesPrimitive<Time> {
  private chart: IChartApi | null = null
  private series: ISeriesApi<'Candlestick'> | null = null
  private requestUpdate: (() => void) | null = null
  private view = new View(this)
  constructor(private zones: ZoneDraw[], public font: string) {}

  attached(p: SeriesAttachedParameter<Time>) {
    this.chart = p.chart as IChartApi; this.series = p.series as ISeriesApi<'Candlestick'>; this.requestUpdate = p.requestUpdate
  }
  detached() { this.chart = null; this.series = null; this.requestUpdate = null }
  setZones(zones: ZoneDraw[]) { this.zones = zones; this.requestUpdate?.() }
  paneViews() { return [this.view] }
  updateAllViews() {
    const ts = this.chart?.timeScale(), s = this.series
    if (!ts || !s) { this.view.px = []; return }
    const width = ts.width(), vr = ts.getVisibleRange()
    const range = vr ? { from: Number(vr.from), to: Number(vr.to) } : null
    const coord = (t: number) => ts.timeToCoordinate(t as UTCTimestamp)
    const out: Px[] = []
    for (const z of this.zones) {
      const l = edgeX(z.tStart, coord, range, width)
      const r = z.tEnd === undefined ? width : edgeX(z.tEnd, coord, range, width)
      const a = s.priceToCoordinate(z.high), b = s.priceToCoordinate(z.low)
      if (l === null || r === null || a === null || b === null) continue
      out.push({ z, l, r, top: Math.min(a, b), bottom: Math.max(a, b) })
    }
    this.view.px = out
  }
}
