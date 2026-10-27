import type { Obj } from '../data/sample'
import { presetById, type PresetId } from './presets'
import { rankByProximity } from './relevance'

export type VisibilityInput = {
  objects: Obj[]; stepIds: string[]; hidden: string[]; preset: PresetId
  refPrice: number; replayT: number | null; selected: string | null
}
export type Visibility = { available: string[]; drawn: string[]; cutByPreset: string[] }

// Causality: with a replay time t, an object is available only if known_at <= t.
export function computeVisibility(i: VisibilityInput): Visibility {
  const known = i.objects.filter(o => i.stepIds.includes(o.id) && (i.replayT === null || o.knownAt <= i.replayT))
  const available = known.map(o => o.id)
  const candidates = known.filter(o => !i.hidden.includes(o.id))
  const preset = presetById(i.preset)
  const isZone = (o: Obj) => o.kind === 'zone' || o.kind === 'structure'
  const top = new Set([
    ...rankByProximity(candidates.filter(o => !isZone(o)), i.refPrice).slice(0, preset.maxItems),
    ...rankByProximity(candidates.filter(isZone), i.refPrice).slice(0, preset.maxZones)].map(o => o.id))
  if (i.selected && candidates.some(o => o.id === i.selected)) top.add(i.selected)
  const drawn = candidates.filter(o => top.has(o.id)).map(o => o.id)
  return { available, drawn, cutByPreset: candidates.filter(o => !top.has(o.id)).map(o => o.id) }
}
