import type { Bar } from '../data/sample'
import { BAR_SECONDS } from '../data/sample'

// A bar is known only once it has closed: open time + one bar length <= t.
export const barsKnownAt = (bars: Bar[], t: number | null): Bar[] =>
  t === null ? bars : bars.filter(b => b.time + BAR_SECONDS <= t)

export type BandLike = { id: string; label: string; from: number; to: number }
// Bands grow with time: a band that has not started is dropped, an open one is clipped at t.
export function bandsKnownAt<T extends BandLike>(bands: T[], t: number | null): T[] {
  if (t === null) return bands
  return bands.filter(b => b.from < t).map(b => ({ ...b, to: Math.min(b.to, t) }))
}
