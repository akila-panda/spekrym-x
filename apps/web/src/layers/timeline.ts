import type { Obj } from '../data/sample'

export type TimelineEntry = { key: string; time: number; label: string; objectId: string }
const GROUP_LABEL: Record<string, string> = { asia: 'Asia range established', london: 'London range established', prior: 'Previous day high marked' }

// One entry per event, derived from known_at. Levels from the same session and time collapse into one entry.
export function buildTimeline(objects: Obj[], replayT: number | null): TimelineEntry[] {
  const seen = new Set<string>(), out: TimelineEntry[] = []
  for (const o of objects) {
    if (replayT !== null && o.knownAt > replayT) continue
    // FVG and order-block zones are drawn on the chart and listed in the objects panel, but kept
    // off the timeline: 43 of them flooded it and pushed the chart off the screen.
    if (o.kind === 'zone') continue
    const own = o.kind !== 'level'  // events and BOS/CHoCH lines each get their own entry
    const key = own ? o.id : `${o.session}@${o.knownAt}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ key, time: o.knownAt, label: own ? o.label : GROUP_LABEL[o.session] ?? o.label, objectId: o.id })
  }
  return out.sort((a, b) => a.time - b.time || a.key.localeCompare(b.key))
}
export const hhmm = (s: number) => new Date(s * 1000).toISOString().slice(11, 16)
export const stamp = (s: number) => new Date(s * 1000).toISOString().slice(0, 16).replace('T', ' ') + ' UTC'
