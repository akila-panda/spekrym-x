import type {
  IChartApi, ISeriesApi, ISeriesPrimitive, ISeriesPrimitiveAxisView, ISeriesPrimitivePaneRenderer,
  ISeriesPrimitivePaneView, SeriesAttachedParameter, Time
} from 'lightweight-charts'
import { decollide } from '../layers/decollide'

export type LevelLabel = { id: string; label: string; price: number; color: string; textColor: string; selected: boolean }
type Placed = LevelLabel & { y: number; fixedY: number }
const GAP = 18

class AxisView implements ISeriesPrimitiveAxisView {
  constructor(private p: Placed) {}
  coordinate() { return -1000 }
  fixedCoordinate() { return this.p.fixedY }
  text() { return this.p.price.toFixed(5) }
  textColor() { return this.p.textColor }
  backColor() { return this.p.color }
  tickVisible() { return false }
}

class Renderer implements ISeriesPrimitivePaneRenderer {
  constructor(private placed: Placed[], private font: string) {}
  draw(target: Parameters<ISeriesPrimitivePaneRenderer['draw']>[0]) {
    target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
      ctx.save()
      ctx.font = this.font; ctx.textBaseline = 'middle'; ctx.textAlign = 'right'
      for (const p of this.placed) {
        const w = ctx.measureText(p.label).width + 12, x = mediaSize.width - 4
        ctx.fillStyle = p.color; ctx.fillRect(x - w, p.fixedY - 8, w, 16)
        ctx.fillStyle = p.textColor; ctx.fillText(p.label, x - 6, p.fixedY + 1)
      }
      ctx.restore()
    })
  }
}

class View implements ISeriesPrimitivePaneView {
  constructor(private owner: LevelLabelsPrimitive) {}
  zOrder() { return 'top' as const }
  renderer() { return new Renderer(this.owner.placed, this.owner.font) }
}

// Draws level names in the pane and prices on the axis, both de-collided so labels never overlap.
export class LevelLabelsPrimitive implements ISeriesPrimitive<Time> {
  placed: Placed[] = []
  private axis: AxisView[] = []
  private series: ISeriesApi<'Candlestick'> | null = null
  private chart: IChartApi | null = null
  private requestUpdate: (() => void) | null = null
  private view = new View(this)
  constructor(private labels: LevelLabel[], public font: string) {}
  attached(p: SeriesAttachedParameter<Time>) {
    this.series = p.series as ISeriesApi<'Candlestick'>; this.chart = p.chart as IChartApi; this.requestUpdate = p.requestUpdate
  }
  detached() { this.series = null; this.chart = null; this.requestUpdate = null }
  setLabels(labels: LevelLabel[]) { this.labels = labels; this.requestUpdate?.() }
  paneViews() { return [this.view] }
  priceAxisViews() { return this.axis }
  updateAllViews() {
    const s = this.series; if (!s) { this.placed = []; this.axis = []; return }
    const raw: { l: LevelLabel; y: number }[] = []
    for (const l of this.labels) { const y = s.priceToCoordinate(l.price); if (y !== null) raw.push({ l, y: Number(y) }) }
    const h = this.chart?.paneSize().height ?? 600
    const ys = decollide(raw.map(o => o.y), GAP, 10, h - 10)
    this.placed = raw.map((o, i) => ({ ...o.l, y: o.y, fixedY: ys[i] }))
    this.axis = this.placed.map(p => new AxisView(p))
  }
}
