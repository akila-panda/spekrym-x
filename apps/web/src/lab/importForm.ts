// Pure helpers for the import form (no React, no network).
export type Range = { start: string; end: string }
export const PRESETS: { id: string; label: string; months: number }[] = [
  { id: '6m', label: '6 months', months: 6 }, { id: '1y', label: '1 year', months: 12 },
  { id: '2y', label: '2 years', months: 24 }, { id: '3y', label: '3 years', months: 36 }
]
const MINUTES: Record<string, number> = { M5: 5, M15: 15, M30: 30, H1: 60 }

export const ymd = (d: Date) => d.toISOString().slice(0, 10)
export const todayUtc = (now: Date = new Date()) => ymd(now)

/** The last day is EXCLUDED (like the CLI), so a preset ending today holds only closed days. */
export function presetRange(months: number, now: Date = new Date()): Range {
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()))
  const start = new Date(end)
  start.setUTCMonth(start.getUTCMonth() - months)
  return { start: ymd(start), end: ymd(end) }
}

/** Same rough formula as the API: days x bars per day x 5/7 (weekends closed). */
export function estimateBars(r: Range, tf: string): number {
  const m = MINUTES[tf]
  const days = Math.round((Date.parse(r.end) - Date.parse(r.start)) / 86_400_000)
  return m && days > 0 ? Math.floor(days * (1440 / m) * 5 / 7) : 0
}

export function rangeProblem(r: Range, tf: string, maxBars: number, now: Date = new Date()): string | null {
  if (!r.start || !r.end) return 'Choose a start and an end date.'
  if (r.end <= r.start) return 'The end date must be after the start date.'
  if (r.start < '2005-01-01') return 'The start date must be 2005-01-01 or later.'
  if (r.end > ymd(new Date(now.getTime() + 86_400_000))) return 'The end date cannot be in the future.'
  if (estimateBars(r, tf) > maxBars) return `About ${estimateBars(r, tf).toLocaleString('en-US')} bars is too many (limit ${maxBars.toLocaleString('en-US')}). Shorten the range or use a longer timeframe.`
  return null
}

/** The file the API will write; used to warn before clicking when it already exists. */
export const fileNameFor = (instrument: string, tf: string, r: Range) =>
  `${instrument.toLowerCase()}_${tf.toLowerCase()}_${r.start.replace(/-/g, '')}_${r.end.replace(/-/g, '')}.parquet`

export function describeApiError(status: number, body: unknown): string {
  const d = (body as { detail?: unknown } | null)?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map(x => (x as { msg?: string }).msg ?? 'invalid value').join('; ').replace(/Value error, /g, '')
  return `The API answered ${status}.`
}
