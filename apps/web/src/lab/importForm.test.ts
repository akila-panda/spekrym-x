import { describe, expect, it } from 'vitest'
import { DatasetList, ImportJob } from '../contracts/datasets'
import { describeApiError, estimateBars, fileNameFor, presetRange, rangeProblem } from './importForm'

const NOW = new Date('2026-10-28T09:00:00Z')

describe('import form helpers', () => {
  it('presets end today (excluded) and start whole months earlier', () => {
    expect(presetRange(24, NOW)).toEqual({ start: '2024-10-28', end: '2026-10-28' })
    expect(presetRange(6, NOW)).toEqual({ start: '2026-04-28', end: '2026-10-28' })
  })
  it('estimates bars like the API (days x bars per day x 5/7)', () => {
    expect(estimateBars({ start: '2026-09-01', end: '2026-10-01' }, 'H1')).toBe(514)   // real month: 528
    expect(estimateBars({ start: '2026-10-01', end: '2026-09-01' }, 'H1')).toBe(0)
    expect(estimateBars({ start: '2026-01-01', end: '2026-02-01' }, 'D')).toBe(0)
  })
  it('names the file exactly as the API does', () => {
    expect(fileNameFor('EUR_USD', 'H1', { start: '2024-10-01', end: '2026-10-27' })).toBe('eur_usd_h1_20241001_20261027.parquet')
  })
  it('flags bad ranges before any request', () => {
    const ok = { start: '2025-01-01', end: '2026-01-01' }
    expect(rangeProblem(ok, 'H1', 250_000, NOW)).toBeNull()
    expect(rangeProblem({ start: '', end: '2026-01-01' }, 'H1', 250_000, NOW)).toMatch(/Choose/)
    expect(rangeProblem({ start: '2026-02-01', end: '2026-01-01' }, 'H1', 250_000, NOW)).toMatch(/after/)
    expect(rangeProblem({ start: '1999-01-01', end: '2026-01-01' }, 'H1', 250_000, NOW)).toMatch(/2005/)
    expect(rangeProblem({ start: '2026-01-01', end: '2027-01-01' }, 'H1', 250_000, NOW)).toMatch(/future/)
    expect(rangeProblem({ start: '2005-01-01', end: '2026-01-01' }, 'M5', 250_000, NOW)).toMatch(/too many/)
  })
  it('turns API errors into one readable line', () => {
    expect(describeApiError(409, { detail: 'file exists' })).toBe('file exists')
    expect(describeApiError(422, { detail: [{ msg: 'Value error, end must be after start' }] })).toBe('end must be after start')
    expect(describeApiError(500, null)).toBe('The API answered 500.')
  })
})

describe('dataset contracts', () => {
  it('parses a list and a finished job', () => {
    const row = { file: 'a.parquet', size_bytes: 10, integrity: 'ok', n_bars: 5, feed_degraded: false }
    expect(DatasetList.parse({ folder: '/x', items: [row], token_configured: true,
      options: { instruments: ['EUR_USD'], timeframes: ['H1'], max_bars: 100 } }).items).toHaveLength(1)
    expect(ImportJob.parse({ id: 'j', state: 'done', message: 'ok', elapsed_s: 1, request: {}, result: row }).state).toBe('done')
  })
  it('rejects an unknown integrity value', () => {
    expect(() => DatasetList.parse({ folder: '/x', items: [{ file: 'a', size_bytes: 1, integrity: 'weird' }], token_configured: true,
      options: { instruments: [], timeframes: [], max_bars: 1 } })).toThrow()
  })
})
