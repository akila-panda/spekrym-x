import type { SuggestionsPayload } from '../../contracts/suggestions'
import { decollide } from '../../layers/decollide'
import { price } from '../../suggestions/format'

type Props = { candles: SuggestionsPayload['candles']; setup: SuggestionsPayload['evidence'][number] | null
  levels: { entry: number; stop: number; target: number } | null }
const W = 640, H = 240, PAD = 8

// Closes as a line, the highlighted setup as a box, the suggestion's levels as dashed lines. Colours are tokens only.
export function EvidenceChart({ candles, setup, levels }: Props) {
  if (candles.length < 2) return <p className="text-sm text-muted">Not enough bars to draw.</p>
  const t = candles.map(c => Date.parse(c.time)), t0 = t[0], t1 = t[t.length - 1]
  const vals = [...candles.flatMap(c => [c.high, c.low]), ...(setup ? [setup.geometry.price_low, setup.geometry.price_high] : []),
    ...(levels ? [levels.entry, levels.stop, levels.target] : [])]
  const lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1
  // x is the bar index, not clock time, so a weekend gap takes one bar of width instead of a long flat stretch.
  const n = candles.length
  const pos = (ms: number) => {
    if (ms <= t0) return 0
    if (ms >= t1) return n - 1
    let k = 0
    while (k < n - 2 && t[k + 1] <= ms) k++
    return k + (ms - t[k]) / (t[k + 1] - t[k])
  }
  const x = (ms: number) => PAD + (pos(ms) / (n - 1)) * (W - 2 * PAD)
  const y = (p: number) => H - PAD - ((p - lo) / span) * (H - 2 * PAD)
  const path = candles.map((c, i) => `${i ? 'L' : 'M'}${x(t[i]).toFixed(1)},${y(c.close).toFixed(1)}`).join(' ')
  const g = setup?.geometry
  const rows = levels ? [
    { p: levels.target, color: 'var(--bull)', label: 'Target' },
    { p: levels.entry, color: 'var(--muted)', label: 'Entry' },
    { p: levels.stop, color: 'var(--bear)', label: 'Stop' }] : []
  // Lines stay at their true price; only the text is pushed apart so neighbours stay readable.
  const textY = decollide(rows.map(r => y(r.p) - 3), 13, 12, H - 4)
  const line = (r: (typeof rows)[number], i: number) => (
    <g key={r.label}><line x1={PAD} x2={W - PAD} y1={y(r.p)} y2={y(r.p)} stroke={r.color} strokeDasharray="5 4" />
      <text x={W - PAD - 2} y={textY[i]} textAnchor="end" fontSize="11" fill={r.color}>{r.label} {price(r.p)}</text></g>)
  return (
    <svg role="img" aria-label="Evidence chart: closes, the highlighted setup and the suggestion levels" viewBox={`0 0 ${W} ${H}`} className="w-full rounded-md border border-line bg-surface">
      {g && <rect data-testid="evidence-box" x={x(Date.parse(g.t_start))} y={y(g.price_high)} width={Math.max(2, x(g.t_end ? Date.parse(g.t_end) : t1) - x(Date.parse(g.t_start)))}
        height={Math.max(2, y(g.price_low) - y(g.price_high))} fill="var(--accent)" fillOpacity="0.18" stroke="var(--accent)" />}
      <path d={path} fill="none" stroke="var(--muted)" strokeWidth="1.5" />
      {rows.map(line)}
    </svg>)
}
