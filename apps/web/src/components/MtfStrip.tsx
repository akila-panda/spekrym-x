import { useDataset } from '../data/DataProvider'
import { useUi } from '../state/store'

// Higher-timeframe facts (D and H4) from closed bars. Facts only: no bias verdict, no score.
export function MtfStrip() {
  const { checklist, origin } = useDataset()
  const { replayT } = useUi()
  const rows = checklist.filter(c => replayT === null || c.knownAt <= replayT)
  return (
    <section aria-label="Higher-timeframe checklist" className="border-b border-line px-4 py-2">
      <div className="mb-1 flex items-center justify-between text-xs text-muted">
        <span className="font-medium uppercase tracking-wide">Daily and H4 context</span><span>Facts from closed bars, not a forecast</span></div>
      {rows.length === 0 ? (
        <p className="text-sm text-muted">{origin === 'offline' ? 'Not available in the offline sample. Start the API to see D and H4 facts.' : 'Nothing is known yet at this time.'}</p>
      ) : (
        <ul className="grid gap-1 md:grid-cols-2">{rows.map(c => (
          <li key={c.id} className="flex gap-2 text-sm"><span className="mt-0.5 h-5 shrink-0 rounded-md bg-surface2 px-1.5 font-mono text-xs leading-5">{c.tf}</span><span>{c.text}</span></li>))}</ul>)}
    </section>)
}
