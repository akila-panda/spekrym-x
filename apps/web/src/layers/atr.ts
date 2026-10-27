import type { Bar } from '../data/sample'

export const ATR_PERIOD = 14
export const pipSize = (instrument: string) => (instrument.endsWith('JPY') ? 0.01 : 0.0001)

// Wilder ATR on closed bars: true range from the second bar on, first value = mean of the first
// `period` true ranges, then ATR = (prev * (period - 1) + TR) / period. Null until period + 1 bars exist.
export function wilderAtr(bars: Bar[], period = ATR_PERIOD): number | null {
  if (bars.length < period + 1) return null
  const tr = (i: number) => Math.max(bars[i].high - bars[i].low,
    Math.abs(bars[i].high - bars[i - 1].close), Math.abs(bars[i].low - bars[i - 1].close))
  let atr = 0
  for (let i = 1; i <= period; i++) atr += tr(i)
  atr /= period
  for (let i = period + 1; i < bars.length; i++) atr = (atr * (period - 1) + tr(i)) / period
  return atr
}

export type Distance = { pips: number; atrMultiple: number | null; atrPips: number | null }
// Plain distance of a level from a reference price. Describes where things are; it predicts nothing.
export function distanceFrom(price: number, ref: number, atr: number | null, instrument = 'EUR_USD'): Distance {
  const pip = pipSize(instrument), d = Math.abs(price - ref)
  return { pips: d / pip, atrMultiple: atr && atr > 0 ? d / atr : null, atrPips: atr ? atr / pip : null }
}
