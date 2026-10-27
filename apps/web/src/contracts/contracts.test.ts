import { describe, expect, it } from 'vitest'
import { Candle, Forecast, Setup, Suggestion } from '.'
import { sampleCandles, sampleSetups, semanticId } from '../data/toSetup'

describe('sample data matches the contracts', () => {
  it('every sample setup validates and was knowable when stamped', () => {
    const setups = sampleSetups()
    expect(setups).toHaveLength(6)
    for (const s of setups) expect(Date.parse(s.known_at)).toBeGreaterThanOrEqual(Date.parse(s.event_time))
  })
  it('every sample candle validates and is complete', () => {
    const c = sampleCandles()
    expect(c).toHaveLength(288)
    expect(c.every(x => x.complete)).toBe(true)
  })
  it('setup ids are unique and do not depend on price', () => {
    const ids = sampleSetups().map(s => s.id)
    expect(new Set(ids).size).toBe(ids.length)
    expect(semanticId(['a', 'b'])).toBe(semanticId(['a', 'b']))
  })
})

describe('contracts reject bad records', () => {
  const base = sampleSetups()[0]
  it('known_at before event_time', () => {
    expect(Setup.safeParse({ ...base, known_at: '2000-01-01T00:00:00.000Z' }).success).toBe(false)
  })
  it('inverted geometry', () => {
    expect(Setup.safeParse({ ...base, geometry: { ...base.geometry, price_low: 2, price_high: 1 } }).success).toBe(false)
  })
  it('candle with high below close', () => {
    const c = sampleCandles()[0]
    expect(Candle.safeParse({ ...c, high: c.low - 1 }).success).toBe(false)
  })
  it('suggestion status must be not_validated', () => {
    const s = { id: 'x', instrument: 'EUR_USD', tf: 'M15', created_at: '2026-10-21T00:00:00.000Z', setup_ids: [], side: 'long', entry: 1, stop: 0.9, target: 1.1,
      score: 0.5, reasons: [], gates: [], rules_version: 'v1', status: 'not_validated' }
    expect(Suggestion.safeParse(s).success).toBe(true)
    expect(Suggestion.safeParse({ ...s, status: 'validated' }).success).toBe(false)
    expect(Suggestion.safeParse({ ...s, reasons: [{ text: 'no evidence', evidence_id: '' }] }).success).toBe(false)
  })
  it('forecast point must sit inside its interval', () => {
    const f = { id: 'f', instrument: 'EUR_USD', tf: 'H1', issued_at: '2026-10-21T00:00:00.000Z', horizon_end: '2026-10-21T01:00:00.000Z', target: 'realized_vol',
      point: 5, interval: { low: 1, high: 2, nominal_coverage: 0.9 }, model: { name: 'm', version: '1', params_hash: 'h' },
      track_record: { n: 0, empirical_coverage: 0, variants_tried: 0 }, status: 'exploratory' }
    expect(Forecast.safeParse(f).success).toBe(false)
    expect(Forecast.safeParse({ ...f, point: 1.5 }).success).toBe(true)
  })
})
