import { PremarketPayload } from '../contracts/premarket'
import type { Setup } from '../contracts/setup'
import type { Obj } from './sample'
import type { Dataset } from './dataset'

const sec = (t: string) => Date.parse(t) / 1000
const DAY = 86400
const hhmm = (t: string) => t.slice(5, 16).replace('T', ' ')

function sessionOf(text: string): Obj['session'] {
  const t = text.toLowerCase()
  return t.startsWith('asia') ? 'asia' : t.startsWith('london') ? 'london'
    : t.startsWith('new york') ? 'ny' : 'prior'
}

// Kinds the chart draws: session levels, sweep events, FVG and order-block zones, BOS/CHoCH lines.
// Swings, trendlines and candle patterns are counted, not drawn (known issue 36).
const ZONE_TAG: Record<string, string> = { fvg: 'FVG', order_block: 'OB', bos: 'BOS', choch: 'CHoCH' }
export function setupToObj(s: Setup, asOfDay: string): Obj | null {
  const tag = ZONE_TAG[s.kind]
  if (tag) {
    const g = s.geometry
    return {
      id: s.id, label: s.plain_text.split(/[:(]/)[0].trim() + ` · ${hhmm(s.event_time)}`, kind: s.kind === 'fvg' || s.kind === 'order_block' ? 'zone' : 'structure',
      price: (g.price_low + g.price_high) / 2, session: 'prior', text: s.plain_text, invalidation: s.invalidation,
      knownAt: sec(s.known_at), setupId: s.id, lifecycle: s.lifecycle, setupKind: s.kind, direction: s.direction, tag,
      span: { low: g.price_low, high: g.price_high, tStart: sec(g.t_start), tEnd: g.t_end ? sec(g.t_end) : undefined },
      time: sec(s.event_time), sourceText: `${s.source.library} ${s.source.version} / ${s.source.adapter}`, status: s.status
    }
  }
  if (s.kind !== 'session_level' && s.kind !== 'liquidity_sweep') return null
  const session = sessionOf(s.plain_text)
  const m = /\((?:trading day )?(\d{4}-\d{2}-\d{2})/.exec(s.plain_text)
  const base = s.plain_text.split(' (')[0]
  const day = m?.[1]
  const label = day && (day !== asOfDay || session === 'prior') ? `${base} · ${day.slice(5)}` : base
  const event = s.kind === 'liquidity_sweep'
  return {
    id: s.id, label, kind: event ? 'event' : 'level', price: (s.geometry.price_low + s.geometry.price_high) / 2,
    time: event ? sec(s.event_time) : undefined, session, text: s.plain_text, invalidation: s.invalidation,
    knownAt: sec(s.known_at), setupId: s.id, lifecycle: s.lifecycle,
    sourceText: `${s.source.library} ${s.source.version} / ${s.source.adapter}`, status: s.status
  }
}

export function toDataset(raw: unknown): Dataset {
  const p = PremarketPayload.parse(raw)
  const asOf = sec(p.as_of), asOfDay = p.as_of.slice(0, 10)
  const bars = p.candles.map(c => ({ time: sec(c.time), open: c.open, high: c.high, low: c.low, close: c.close }))
  const objs = p.setups.map(s => setupToObj(s, asOfDay)).filter((o): o is Obj => o !== null)
  const all = objs.map(o => o.id)
  const sample = p.status_labels.includes('sample')
  return {
    id: `api:${p.data_version}:${p.as_of}`, origin: 'api', instrument: p.instrument,
    label: p.source.label, badge: sample ? 'Sample data' : 'Not validated',
    bars, objects: objs,
    bands: p.session_bands.map(b => ({ id: b.id, label: b.name === 'ny' ? 'New York' : b.name[0].toUpperCase() + b.name.slice(1),
      from: sec(b.t_start), to: Math.min(sec(b.t_end), asOf) })),
    steps: [
      { id: 1, title: 'Market context', show: [] },
      { id: 2, title: 'Key price levels', show: objs.filter(o => o.kind === 'level' && o.session === 'prior').map(o => o.id) },
      { id: 3, title: 'Session liquidity', show: objs.filter(o => o.kind === 'level' || o.kind === 'event').map(o => o.id) },
      { id: 4, title: 'Structure & momentum', show: all },
      { id: 5, title: 'Scenarios & risk', show: all }, { id: 6, title: 'Final session plan', show: all }],
    lastClose: bars[bars.length - 1].close, sessionDayStart: Math.floor(asOf / DAY) * DAY, asOf,
    checklist: p.checklist.map(c => ({ id: c.id, tf: c.tf, text: c.text, knownAt: sec(c.known_at) })),
    notDrawn: p.setups.length - objs.length, dataVersion: p.data_version
  }
}
