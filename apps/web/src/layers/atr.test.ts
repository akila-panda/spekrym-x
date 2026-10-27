import { describe, expect, it } from 'vitest'
import { distanceFrom, pipSize, wilderAtr } from './atr'

const b = (high: number, low: number, close: number) => ({ time: 0, open: close, high, low, close })

describe('wilderAtr', () => {
  it('matches a hand calculation (period 2)', () => {
    // TR1 = max(2, |11-9|, |9-9|) = 2; TR2 = 2; first ATR = 2. TR3 = max(1, |15-11|, |14-11|) = 4. ATR = (2*1 + 4)/2 = 3.
    const bars = [b(10, 8, 9), b(11, 9, 10), b(12, 10, 11), b(15, 14, 15)]
    expect(wilderAtr(bars.slice(0, 3), 2)).toBe(2)
    expect(wilderAtr(bars, 2)).toBe(3)
  })
  it('is null until period + 1 closed bars exist', () => {
    expect(wilderAtr([b(2, 1, 1.5), b(3, 2, 2.5)], 2)).toBeNull()
  })
  it('uses only the bars given (causal: a later bar changes nothing earlier)', () => {
    const bars = [b(10, 8, 9), b(11, 9, 10), b(12, 10, 11), b(15, 14, 15)]
    expect(wilderAtr(bars.slice(0, 3), 2)).toBe(wilderAtr([...bars.slice(0, 3)], 2))
  })
})

describe('distanceFrom', () => {
  it('reports pips and ATR multiples without a direction', () => {
    const d = distanceFrom(1.085, 1.084, 0.0005)
    expect(d.pips).toBeCloseTo(10, 6); expect(d.atrMultiple).toBeCloseTo(2, 6); expect(d.atrPips).toBeCloseTo(5, 6)
    expect(distanceFrom(1.084, 1.085, 0.0005).pips).toBeCloseTo(10, 6)
  })
  it('gives no multiple when ATR is missing and uses 0.01 pips for JPY', () => {
    expect(distanceFrom(1.1, 1, null).atrMultiple).toBeNull()
    expect(pipSize('USD_JPY')).toBe(0.01)
    expect(distanceFrom(150.5, 150, 0.1, 'USD_JPY').pips).toBeCloseTo(50, 6)
  })
})
