import { useDataset } from '../data/DataProvider'
import { buildTimeline, hhmm } from '../layers/timeline'
import { useUi } from '../state/store'

export function Timeline() {
  const { replayT, select, selected } = useUi()
  const { objects } = useDataset()
  const entries = buildTimeline(objects, replayT)
  return (
    <section aria-label="Session timeline" className="border-t border-line px-4 py-2">
      <div className="mb-1 flex items-center justify-between text-xs text-muted">
        <span className="font-medium uppercase tracking-wide">Timeline</span><span>Derived from when each item became knowable</span></div>
      {entries.length === 0 ? <p className="text-sm text-muted">Nothing is known yet at this time.</p> : (
        <ol className="flex max-h-24 flex-wrap gap-2 overflow-y-auto">
          {entries.map(e => (
            <li key={e.key}><button onClick={() => select(e.objectId)} aria-pressed={selected === e.objectId}
              className={`rounded-md border px-2 py-1 text-left text-xs ${selected === e.objectId ? 'border-accent bg-surface2' : 'border-line'}`}>
              <span className="mr-2 font-mono text-muted">{hhmm(e.time)}</span>{e.label}</button></li>))}
        </ol>)}
    </section>
  )
}
