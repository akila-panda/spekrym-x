import { BAR_SECONDS } from '../data/sample'
import { useDataset } from '../data/DataProvider'
import { stamp } from '../layers/timeline'
import { useUi } from '../state/store'

export function ReplayBar() {
  const { replayT, setReplay } = useUi()
  const { bars, sessionDayStart } = useDataset()
  const MAX = bars[bars.length - 1].time + BAR_SECONDS
  const value = replayT ?? MAX
  return (
    <section aria-label="Causal replay" className="flex items-center gap-3 border-t border-line px-4 py-2 text-xs">
      <label htmlFor="replay" className="font-medium uppercase tracking-wide text-muted">Replay</label>
      <input id="replay" type="range" className="flex-1 accent-[var(--accent)]" min={sessionDayStart} max={MAX} step={BAR_SECONDS}
        value={value} aria-valuetext={replayT === null ? 'Live, all data' : stamp(replayT)}
        onChange={e => { const v = Number(e.target.value); setReplay(v >= MAX ? null : v) }} />
      <span className="w-40 text-right font-mono">{replayT === null ? 'Live (all data)' : stamp(replayT)}</span>
      <button className="rounded-md border border-line px-2 py-1 text-muted hover:text-ink disabled:opacity-50" disabled={replayT === null}
        onClick={() => setReplay(null)}>Live</button>
    </section>
  )
}
