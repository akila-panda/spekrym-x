import { describe, expect, it } from 'vitest'
import raw from '../test/fixtures/premarket_payload.json'
import { toDataset } from './fromApi'
import { computeVisibility } from '../layers/visibility'
import { buildTimeline } from '../layers/timeline'

const ds = toDataset(raw)
const clone = () => structuredClone(raw) as Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

describe('toDataset (API payload to the web dataset)', () => {
  it('keeps the honesty label and marks the data as sample, not live', () => {
    expect(ds.origin).toBe('api')
    expect(ds.label).toBe('SAMPLE DATA — NOT LIVE')
    expect(ds.badge).toBe('Sample data')
  })
  it('draws levels, zones and structure lines; swings and patterns are counted as not drawn', () => {
    const kinds = (k: string) => ds.objects.filter(o => o.kind === k).length
    expect(kinds('level') + kinds('event')).toBe(12)
    expect(kinds('zone')).toBe(43)       // 33 FVG + 10 order blocks in the fixture
    expect(kinds('structure')).toBe(7)   // 5 BOS + 2 CHoCH
    expect(ds.notDrawn).toBe(raw.setups.length - ds.objects.length)
    expect(ds.notDrawn).toBe(58)         // 19 swings + 39 candle patterns
    expect(ds.objects.every(o => o.setupId?.startsWith('setup:'))).toBe(true)
  })
  it('zones and structure lines carry their extent, tag and orientation', () => {
    const z = ds.objects.filter(o => o.kind === 'zone' || o.kind === 'structure')
    expect(z.every(o => o.span && o.tag && o.direction && o.span.low <= o.span.high)).toBe(true)
    expect(ds.objects.filter(o => o.kind === 'structure').every(o => o.span!.low === o.span!.high)).toBe(true)
    expect(new Set(z.map(o => o.tag))).toEqual(new Set(['FVG', 'OB', 'BOS', 'CHoCH']))
  })
  it('timeline lists structure lines but not FVG or order-block zones, and stays short', () => {
    const tl = buildTimeline(ds.objects, null)
    const kindOf = (id: string) => ds.objects.find(o => o.id === id)!.kind
    expect(tl.some(e => kindOf(e.objectId) === 'zone')).toBe(false)
    expect(tl.filter(e => kindOf(e.objectId) === 'structure')).toHaveLength(7)
    expect(tl.length).toBeLessThan(25)
    expect(tl.some(e => /Previous day high marked/.test(e.label))).toBe(true)
  })
  it('the premarket preset caps zones separately so session levels are never displaced', () => {
    const ids = ds.objects.map(o => o.id)
    const v = computeVisibility({ objects: ds.objects, stepIds: ids, hidden: [], preset: 'premarket',
      refPrice: ds.lastClose, replayT: null, selected: null })
    const drawn = ds.objects.filter(o => v.drawn.includes(o.id))
    expect(drawn.filter(o => o.kind === 'zone' || o.kind === 'structure')).toHaveLength(6)
    expect(drawn.filter(o => o.kind === 'level' || o.kind === 'event')).toHaveLength(8)
  })
  it('every object, bar and checklist row is known by as_of', () => {
    expect(ds.asOf).toBe(Date.parse('2026-10-26T12:00:00Z') / 1000)
    expect(ds.objects.every(o => o.knownAt <= ds.asOf!)).toBe(true)
    expect(ds.checklist.every(c => c.knownAt <= ds.asOf!)).toBe(true)
    expect(ds.bars.every(x => x.time + 900 <= ds.asOf!)).toBe(true)
    expect(ds.bands.every(x => x.to <= ds.asOf!)).toBe(true)
  })
  it('replay hides objects whose known_at is after the replay time', () => {
    const ids = ds.objects.map(o => o.id)
    const mid = ds.objects.map(o => o.knownAt).sort()[3]
    const v = computeVisibility({ objects: ds.objects, stepIds: ids, hidden: [], preset: 'everything',
      refPrice: ds.lastClose, replayT: mid, selected: null })
    expect(v.available.length).toBeGreaterThan(0)
    expect(v.available.length).toBeLessThan(ids.length)
    expect(ds.objects.filter(o => v.available.includes(o.id)).every(o => o.knownAt <= mid)).toBe(true)
  })
  it('step 2 shows only previous-day levels and step 1 nothing', () => {
    expect(ds.steps[0].show).toEqual([])
    expect(ds.steps[1].show.length).toBe(2)
    expect(ds.objects.filter(o => ds.steps[1].show.includes(o.id)).every(o => o.session === 'prior')).toBe(true)
  })
  it('labels levels from other days with their date so names stay unique', () => {
    const labels = ds.objects.map(o => o.label)
    expect(new Set(labels).size).toBe(labels.length)
  })
  it('rejects a setup that is known after as_of', () => {
    const bad = clone(); bad.setups[0].known_at = '2026-10-27T00:00:00Z'
    expect(() => toDataset(bad)).toThrow()
  })
  it('rejects a payload without a source label or with a bad schema version', () => {
    const a = clone(); a.source.label = ''
    const b = clone(); b.schema_version = 2
    expect(() => toDataset(a)).toThrow(); expect(() => toDataset(b)).toThrow()
  })
})
