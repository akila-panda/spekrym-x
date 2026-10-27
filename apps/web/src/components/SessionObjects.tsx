import { useDataset } from '../data/DataProvider'
import { useUi } from '../state/store'

export function SessionObjects({ available, drawn }: { available: string[]; drawn: string[] }) {
  const { selected, select, hidden, toggleHidden } = useUi()
  const { objects, notDrawn } = useDataset()
  const list = objects.filter(o => available.includes(o.id))
  return (
    <div>
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Session objects</div>
      <ul className="max-h-80 space-y-1 overflow-y-auto">
        {list.map(o => {
          const off = hidden.includes(o.id), cut = !off && !drawn.includes(o.id)
          return (
            <li key={o.id} className={`flex items-center justify-between rounded-md px-2 py-1.5 ${selected === o.id ? 'bg-surface2' : ''}`}>
              <button className="flex-1 text-left text-sm" aria-pressed={selected === o.id} onClick={() => select(o.id)}>
                {o.label}{cut && <span className="ml-1 text-xs text-muted">(not drawn: preset)</span>}</button>
              <button aria-label={`${off ? 'Show' : 'Hide'} ${o.label}`} className="text-xs text-muted hover:text-ink" onClick={() => toggleHidden(o.id)}>
                {off ? 'show' : 'hide'}</button></li>)
        })}
        {list.length === 0 && <li className="px-2 text-sm text-muted">No objects known at this step or time.</li>}
      </ul>
      {notDrawn > 0 && <p className="mt-2 px-2 text-xs text-muted">{notDrawn} other detected objects (swings, trendlines, candle patterns) are in the data but not drawn yet.</p>}
    </div>)
}
