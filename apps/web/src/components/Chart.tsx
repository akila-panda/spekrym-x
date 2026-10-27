import { useEffect, useRef } from 'react'
import { createChart, ColorType, LineStyle, type IChartApi, type ISeriesApi, type IPriceLine, type UTCTimestamp } from 'lightweight-charts'
import type { Bar } from '../data/sample'
import { useDataset } from '../data/DataProvider'
import { barsKnownAt, bandsKnownAt } from '../layers/replay'
import { SessionBandsPrimitive } from './sessionBandsPrimitive'
import { LevelLabelsPrimitive, type LevelLabel } from './levelLabelsPrimitive'
import { ZonesPrimitive, type ZoneDraw } from './zonesPrimitive'

const css = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim()
const MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"
const SANS = 'Inter, system-ui, sans-serif'
const bandStyle = () => ({ colors: { asia: css('--asia'), london: css('--london'), ny: css('--ny') }, font: `500 11px ${SANS}` })
const SESSION_VAR: Record<string, string> = { asia: '--asia', london: '--london', ny: '--ny', prior: '--muted' }
const toData = (bs: Bar[]) => bs.map(b => ({ ...b, time: b.time as UTCTimestamp }))

type Props = { visible: string[]; selected: string | null; theme: string; replayT: number | null }

export function Chart({ visible, selected, theme, replayT }: Props) {
  const { bars, objects, bands: sessionBands, label, instrument } = useDataset()
  const el = useRef<HTMLDivElement>(null)
  const chart = useRef<IChartApi | null>(null)
  const series = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const lines = useRef<IPriceLine[]>([])
  const bandsPrim = useRef<SessionBandsPrimitive | null>(null)
  const labelsPrim = useRef<LevelLabelsPrimitive | null>(null)
  const zonesPrim = useRef<ZonesPrimitive | null>(null)

  useEffect(() => {
    const c = createChart(el.current!, { autoSize: true, rightPriceScale: { borderVisible: false }, timeScale: { timeVisible: true, borderVisible: false } })
    const s = c.addCandlestickSeries({ borderVisible: false, lastValueVisible: true, priceFormat: { type: 'price', precision: 5, minMove: 0.00001 } })
    s.setData(toData(bars))
    c.timeScale().setVisibleRange({ from: (bars[bars.length - 1].time - 36 * 3600) as UTCTimestamp, to: (bars[bars.length - 1].time + 3 * 3600) as UTCTimestamp })
    const bp = new SessionBandsPrimitive(sessionBands, bandStyle()); s.attachPrimitive(bp)
    const lp = new LevelLabelsPrimitive([], `500 11px ${MONO}`); s.attachPrimitive(lp)
    const zp = new ZonesPrimitive([], `500 10px ${MONO}`); s.attachPrimitive(zp)
    chart.current = c; series.current = s; bandsPrim.current = bp; labelsPrim.current = lp; zonesPrim.current = zp
    return () => { s.detachPrimitive(bp); s.detachPrimitive(lp); s.detachPrimitive(zp); c.remove(); chart.current = null; series.current = null }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- the chart is created once per dataset (Workspace keys it by dataset id)
  }, [])

  useEffect(() => {
    chart.current?.applyOptions({
      layout: { background: { type: ColorType.Solid, color: css('--bg') }, textColor: css('--muted'), fontFamily: MONO },
      grid: { vertLines: { color: css('--border') }, horzLines: { color: css('--border') } }
    })
    bandsPrim.current?.setStyle(bandStyle())
    series.current?.applyOptions({ upColor: css('--bull'), downColor: css('--bear'), wickUpColor: css('--bull'), wickDownColor: css('--bear') })
  }, [theme])

  // Causal replay: only closed bars up to t, and bands clipped at t.
  useEffect(() => {
    const c = chart.current, s = series.current; if (!c || !s) return
    const range = c.timeScale().getVisibleLogicalRange()
    s.setData(toData(barsKnownAt(bars, replayT)))
    if (range) c.timeScale().setVisibleLogicalRange(range)
    bandsPrim.current?.setBands(bandsKnownAt(sessionBands, replayT))
  // eslint-disable-next-line react-hooks/exhaustive-deps -- bars and bands are fixed for the life of this chart instance
  }, [replayT])

  useEffect(() => {
    const s = series.current; if (!s) return
    lines.current.forEach(l => s.removePriceLine(l)); lines.current = []
    const shown = objects.filter(o => visible.includes(o.id))
    const levels = shown.filter(o => o.kind === 'level')
    levels.forEach(o => lines.current.push(s.createPriceLine({
      price: o.price, title: '', color: css(SESSION_VAR[o.session]), lineWidth: selected === o.id ? 3 : 1,
      lineStyle: LineStyle.Dashed, axisLabelVisible: false })))
    labelsPrim.current?.setLabels(levels.map((o): LevelLabel => ({
      id: o.id, label: o.label, price: o.price, color: css(SESSION_VAR[o.session]), textColor: css('--bg'), selected: selected === o.id })))
    s.setMarkers(shown.filter(o => o.kind === 'event').map(o => ({
      time: o.time as UTCTimestamp, position: 'aboveBar' as const, shape: 'circle' as const,
      color: selected === o.id ? css('--accent') : css('--warn'), text: o.label })))
  // eslint-disable-next-line react-hooks/exhaustive-deps -- objects are fixed for the life of this chart instance
  }, [visible, selected, theme])

  // Zones and structure lines. Orientation colours only (bull/bear tokens), never a forecast.
  // Under replay a zone is clipped at the replay time; otherwise it runs to the right edge.
  useEffect(() => {
    const dirColor = (d?: string) => css(d === 'bullish' ? '--bull' : d === 'bearish' ? '--bear' : '--muted')
    zonesPrim.current?.setZones(objects.filter(o => visible.includes(o.id) && o.span).map((o): ZoneDraw => {
      const sp = o.span!, end = sp.tEnd ?? (replayT ?? undefined)
      return { id: o.id, tag: o.tag ?? '', kind: o.kind === 'zone' ? 'zone' : 'line', low: sp.low, high: sp.high,
        tStart: sp.tStart, tEnd: end !== undefined && replayT !== null ? Math.min(end, replayT) : end,
        color: dirColor(o.direction), faded: o.lifecycle === 'mitigated' || o.lifecycle === 'broken', selected: selected === o.id }
    }))
  // eslint-disable-next-line react-hooks/exhaustive-deps -- objects are fixed for the life of this chart instance
  }, [visible, selected, theme, replayT])

  return <div className="relative h-full w-full"><div ref={el} className="absolute inset-0" role="img"
    aria-label={`${instrument.replace('_', '/')} M15 candlestick chart with session bands, price levels, zones and structure lines. ${label}`} /></div>
}
