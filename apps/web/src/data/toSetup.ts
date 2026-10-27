import { objects, bars, SAMPLE_START, type Obj } from './sample'
import { Candle, Setup } from '../contracts'

const iso = (s: number) => new Date(s * 1000).toISOString()
// Deterministic id from semantic fields only, never from price values (docs/CONTRACTS.md).
export function semanticId(parts: string[]): string {
  let h = 0x811c9dc5
  for (const ch of parts.join('|')) { h ^= ch.charCodeAt(0); h = Math.imul(h, 0x01000193) >>> 0 }
  return `sx_${h.toString(16).padStart(8, '0')}`
}

export function toSetup(o: Obj): Setup {
  const event = o.kind === 'event'
  const eventTime = o.time ?? o.knownAt
  return Setup.parse({
    id: semanticId([event ? 'liquidity_sweep' : 'session_level', 'EUR_USD', 'M15', o.id, o.session]),
    kind: event ? 'liquidity_sweep' : 'session_level', instrument: 'EUR_USD', tf: 'M15', direction: 'neutral',
    geometry: { price_low: o.price, price_high: o.price, t_start: iso(o.time ?? SAMPLE_START + 48 * 3600) },
    event_time: iso(Math.min(eventTime, o.knownAt)), known_at: iso(o.knownAt), lifecycle: 'fresh',
    source: { library: 'sample', version: '1', adapter: 'sample-fixture' },
    plain_text: o.text, invalidation: o.invalidation, status: 'causal'
  })
}
export const sampleSetups = (): Setup[] => objects.map(toSetup)
export const sampleCandles = (): Candle[] => bars.map(b => Candle.parse({
  instrument: 'EUR_USD', tf: 'M15', time: iso(b.time), open: b.open, high: b.high, low: b.low, close: b.close, volume: 0, complete: true }))
