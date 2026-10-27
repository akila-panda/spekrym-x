// Frozen SAMPLE data. Generated from a seeded random walk. Not market data.
export type Bar = { time: number; open: number; high: number; low: number; close: number }
export type Obj = {
  id: string; label: string; kind: 'level' | 'event' | 'zone' | 'structure'; price: number; time?: number
  session: 'asia' | 'london' | 'ny' | 'prior'; text: string; invalidation: string; knownAt: number
  // Present on objects that come from the API (real setup id, lifecycle, producer, status).
  setupId?: string; lifecycle?: string; sourceText?: string; status?: string
  // Zones (FVG, order block) and structure lines (BOS, CHoCH): orientation, short tag, price/time extent.
  setupKind?: string; direction?: 'bullish' | 'bearish' | 'neutral'; tag?: string
  span?: { low: number; high: number; tStart: number; tEnd?: number }
}

function rng(seed: number) {
  return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
}
const r = rng(42)
const START = Date.UTC(2026, 9, 19) / 1000
export const bars: Bar[] = []
let p = 1.085
for (let i = 0; i < 288; i++) {
  const o = p, c = o + (r() - 0.5) * 0.0010 + (1.085 - o) * 0.01
  bars.push({ time: START + i * 900, open: o, high: Math.max(o, c) + r() * 0.0004, low: Math.min(o, c) - r() * 0.0004, close: c })
  p = c
}
const day = (d: number, h0: number, h1: number) =>
  bars.filter(b => { const t = (b.time - START) / 3600; return t >= d * 24 + h0 && t < d * 24 + h1 })
const hi = (xs: Bar[]) => xs.reduce((a, b) => (b.high > a.high ? b : a))
const lo = (xs: Bar[]) => xs.reduce((a, b) => (b.low < a.low ? b : a))

const prior = day(1, 0, 24), asia = day(2, 0, 7), london = day(2, 7, 12)
const pdh = hi(prior), aH = hi(asia), aL = lo(asia), lH = hi(london), lL = lo(london)
// Frozen wicks so the sample levels are visibly separated (about 5 pips apart). Still sample data.
pdh.high += 0.0010
lH.high += 0.0005
const swept = lH.high > aH.high

export const objects: Obj[] = [
  { id: 'pdh', label: 'Previous day high', kind: 'level', price: pdh.high, session: 'prior', knownAt: START + 48 * 3600,
    text: 'Highest price of the previous day. A common reference where stops cluster.',
    invalidation: 'A close well above it turns it from resistance into broken structure.' },
  { id: 'asiaH', label: 'Asia high', kind: 'level', price: aH.high, session: 'asia', knownAt: START + 55 * 3600,
    text: 'Highest price of the Asia session (00:00–07:00 UTC).', invalidation: 'Fixed reference once the session has closed.' },
  { id: 'asiaL', label: 'Asia low', kind: 'level', price: aL.low, session: 'asia', knownAt: START + 55 * 3600,
    text: 'Lowest price of the Asia session (00:00–07:00 UTC).', invalidation: 'Fixed reference once the session has closed.' },
  { id: 'lonH', label: 'London high', kind: 'level', price: lH.high, session: 'london', knownAt: START + 60 * 3600,
    text: 'Highest price of the London session so far (07:00–12:00 UTC).', invalidation: 'Moves up if price makes a new high before the session ends.' },
  { id: 'lonL', label: 'London low', kind: 'level', price: lL.low, session: 'london', knownAt: START + 60 * 3600,
    text: 'Lowest price of the London session so far.', invalidation: 'Moves down if price makes a new low before the session ends.' },
  { id: 'sweep', label: swept ? 'Liquidity sweep?' : 'No sweep of Asia high', kind: 'event', price: lH.high, time: lH.time, session: 'london', knownAt: lH.time + 900,
    text: swept ? 'London traded above the Asia high. Whether this was a sweep depends on how price reacted afterwards.'
                : 'London did not trade above the Asia high, so there is no sweep of it in this sample.',
    invalidation: 'A sustained close above the London high.' }
]
export const lastClose = bars[bars.length - 1].close
export const SAMPLE_START = START
export const SESSION_DAY_START = START + 48 * 3600
export const BAR_SECONDS = 900
export const sessionBands = [
  { id: 'asia', label: 'Asia', from: START + 48 * 3600, to: START + 55 * 3600 },
  { id: 'london', label: 'London', from: START + 55 * 3600, to: START + 60 * 3600 }
]
const all = ['pdh', 'asiaH', 'asiaL', 'lonH', 'lonL', 'sweep']
export const steps = [
  { id: 1, title: 'Market context', show: [] as string[] },
  { id: 2, title: 'Key price levels', show: ['pdh'] },
  { id: 3, title: 'Session liquidity', show: all },
  { id: 4, title: 'Structure & momentum', show: all },
  { id: 5, title: 'Scenarios & risk', show: all },
  { id: 6, title: 'Final session plan', show: all }
]
