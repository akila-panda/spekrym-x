import { describe, expect, it } from 'vitest'
import { bars, objects, SESSION_DAY_START, sessionBands, steps } from '../data/sample'
import { decollide } from './decollide'
import { rankByProximity } from './relevance'
import { barsKnownAt, bandsKnownAt } from './replay'
import { buildTimeline } from './timeline'
import { computeVisibility } from './visibility'
import { edgeX } from '../components/sessionBandsPrimitive'

const all = objects.map(o => o.id)
const base = { objects, stepIds: all, hidden: [] as string[], preset: 'everything' as const, refPrice: 1.0855, replayT: null, selected: null }

describe('sample data is frozen and separated', () => {
  it('levels are at least 3 pips apart', () => {
    const p = objects.filter(o => o.kind === 'level').map(o => o.price).sort((a, b) => a - b)
    for (let i = 1; i < p.length; i++) expect(p[i] - p[i - 1]).toBeGreaterThanOrEqual(0.0003)
  })
  it('matches the frozen values', () => {
    expect(objects.map(o => [o.id, +o.price.toFixed(5)])).toEqual([['pdh', 1.08671], ['asiaH', 1.08559], ['asiaL', 1.08322], ['lonH', 1.08613], ['lonL', 1.08382], ['sweep', 1.08613]])
    expect(bars).toHaveLength(288)
  })
})

describe('decollide', () => {
  it('keeps neighbours at least gap apart and preserves order', () => {
    const out = decollide([100, 101, 102, 300], 18, 0, 500)
    expect(out[1] - out[0]).toBeGreaterThanOrEqual(18)
    expect(out[2] - out[1]).toBeGreaterThanOrEqual(18)
    expect(out[3]).toBe(300)
  })
  it('stays inside the bounds and maps back to input order', () => {
    const out = decollide([499, 10, 498], 18, 0, 500)
    expect(Math.max(...out)).toBeLessThanOrEqual(500)
    expect(out[1]).toBe(10)
    expect(out[0]).toBeGreaterThan(out[2])
  })
  it('leaves well-spaced labels alone', () => { expect(decollide([10, 100, 200], 18, 0, 500)).toEqual([10, 100, 200]) })
})

describe('relevance and presets', () => {
  it('ranks nearest to price first and is deterministic on ties', () => {
    expect(rankByProximity(objects, 1.0855).map(o => o.id)[0]).toBe('asiaH')
    expect(rankByProximity(objects, 1.0861).slice(0, 2).map(o => o.id)).toEqual(['lonH', 'sweep'])
  })
  it('execution preset draws only the 4 nearest', () => {
    const v = computeVisibility({ ...base, preset: 'execution' })
    expect(v.drawn).toHaveLength(4)
    expect(v.cutByPreset).toHaveLength(2)
  })
  it('clean draws 2 and everything draws all', () => {
    expect(computeVisibility({ ...base, preset: 'clean' }).drawn).toHaveLength(2)
    expect(computeVisibility(base).drawn).toHaveLength(6)
  })
  it('a selected object is always drawn, a hidden one never', () => {
    expect(computeVisibility({ ...base, preset: 'clean', selected: 'asiaL' }).drawn).toContain('asiaL')
    expect(computeVisibility({ ...base, hidden: ['pdh'], selected: 'pdh' }).drawn).not.toContain('pdh')
  })
  it('step 2 shows only the previous day high and step 1 nothing', () => {
    expect(computeVisibility({ ...base, stepIds: steps[1].show }).drawn).toEqual(['pdh'])
    expect(computeVisibility({ ...base, stepIds: steps[0].show }).drawn).toEqual([])
  })
})

describe('causal replay', () => {
  it('hides every object with known_at after the replay time', () => {
    const t = objects.find(o => o.id === 'asiaH')!.knownAt
    const v = computeVisibility({ ...base, replayT: t })
    expect(v.available.sort()).toEqual(['asiaH', 'asiaL', 'pdh'])
    for (const id of v.drawn) expect(objects.find(o => o.id === id)!.knownAt).toBeLessThanOrEqual(t)
  })
  it('before the day starts nothing is known', () => {
    expect(computeVisibility({ ...base, replayT: SESSION_DAY_START - 1 }).available).toEqual([])
  })
  it('drops bars that have not closed yet', () => {
    const t = bars[10].time + 900
    const shown = barsKnownAt(bars, t)
    expect(shown[shown.length - 1].time).toBe(bars[10].time)
    expect(barsKnownAt(bars, bars[10].time + 899).length).toBe(10)
    expect(barsKnownAt(bars, null)).toHaveLength(288)
  })
  it('clips session bands at the replay time', () => {
    const asia = sessionBands[0], t = asia.from + 3600
    const b = bandsKnownAt(sessionBands, t)
    expect(b).toHaveLength(1)
    expect(b[0].to).toBe(t)
    expect(bandsKnownAt(sessionBands, asia.from)).toHaveLength(0)
  })
})

describe('timeline', () => {
  it('is derived from known_at, sorted, and collapses same-session levels', () => {
    const t = buildTimeline(objects, null)
    expect(t.map(e => e.label)).toEqual(['Previous day high marked', 'Asia range established', 'Liquidity sweep?', 'London range established'])
    expect(t.map(e => e.time)).toEqual([...t.map(e => e.time)].sort((a, b) => a - b))
  })
  it('respects the replay time', () => { expect(buildTimeline(objects, SESSION_DAY_START)).toHaveLength(1) })
})

describe('session band geometry', () => {
  const range = { from: 100, to: 200 }
  it('uses the coordinate when available', () => { expect(edgeX(150, () => 42, range, 800)).toBe(42) })
  it('clamps edges outside the visible range', () => {
    expect(edgeX(50, () => null, range, 800)).toBe(0)
    expect(edgeX(250, () => null, range, 800)).toBe(800)
  })
  it('returns null when inside the range but unresolved', () => { expect(edgeX(150, () => null, range, 800)).toBeNull() })
})
