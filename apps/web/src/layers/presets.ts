export type PresetId = 'premarket' | 'execution' | 'clean' | 'everything'
export type Preset = { id: PresetId; label: string; maxItems: number; maxZones: number; note: string }

// maxItems caps session levels and events; maxZones caps zones and structure lines separately,
// so many small zones can never push session levels off the chart. maxItems caps how many objects are drawn; the nearest to price win. Selected objects are always drawn.
export const PRESETS: Preset[] = [
  { id: 'premarket', label: 'Premarket', maxItems: 8, maxZones: 6, note: 'Session levels and events for preparation' },
  { id: 'execution', label: 'Execution', maxItems: 4, maxZones: 4, note: 'Only the 4 items nearest price' },
  { id: 'clean', label: 'Clean', maxItems: 2, maxZones: 0, note: 'Only the 2 items nearest price' },
  { id: 'everything', label: 'Everything', maxItems: Infinity, maxZones: Infinity, note: 'Every available object' }
]
export const presetById = (id: PresetId): Preset => PRESETS.find(p => p.id === id)!
export const defaultPresetFor = (mode: 'premarket' | 'chart'): PresetId => (mode === 'premarket' ? 'premarket' : 'execution')
