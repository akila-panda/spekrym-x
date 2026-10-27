import { bars, objects, sessionBands, steps, lastClose, SESSION_DAY_START, type Bar, type Obj } from './sample'
import type { BandLike } from '../layers/replay'

export type ChecklistRow = { id: string; tf: string; text: string; knownAt: number }
export type Step = { id: number; title: string; show: string[] }
export type Dataset = {
  id: string                       // changes when the data changes (used to remount the chart)
  origin: 'api' | 'offline'
  instrument: string               // "EUR_USD"
  label: string                    // honesty label shown on every surface
  badge: string                    // short badge text
  bars: Bar[]; objects: Obj[]; bands: BandLike[]; steps: Step[]
  lastClose: number; sessionDayStart: number; asOf: number | null
  checklist: ChecklistRow[]; notDrawn: number; dataVersion: string | null
}

// The built-in frozen sample. Used when the API is off or unreachable; always labelled.
export const sampleDataset: Dataset = {
  id: 'offline-sample', origin: 'offline', instrument: 'EUR_USD',
  label: 'Sample data (offline copy, not from the API)', badge: 'Sample data',
  bars, objects, bands: sessionBands, steps, lastClose, sessionDayStart: SESSION_DAY_START,
  asOf: null, checklist: [], notDrawn: 0, dataVersion: null
}
