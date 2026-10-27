import { useDataset } from '../data/DataProvider'
import { stamp } from '../layers/timeline'
import { Badge } from '../components/Badge'

export function SessionPlan() {
  const { objects, badge, label } = useDataset()
  const day = new Date((objects[0]?.knownAt ?? 0) * 1000).toISOString().slice(0, 10)
  const levels = objects.filter(o => o.kind === 'level').sort((a, b) => b.price - a.price)
  const events = objects.filter(o => o.kind === 'event')
  return (
    <section aria-label="Final session plan" className="print-area min-w-0 flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        <header className="space-y-2">
          <div className="no-print flex justify-end">
            <button className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-surface2" onClick={() => window.print()}>Print plan</button></div>
          <h1 className="font-serif text-2xl font-semibold">New York session plan</h1>
          <p className="font-mono text-sm">EUR/USD · M15 · prepared from data of {day}</p>
          <div className="flex flex-wrap gap-2"><Badge tone="warn">{badge}</Badge><Badge>Causal</Badge><Badge>Not validated</Badge></div>
          <p className="text-sm text-muted">{label}. These notes describe what already happened in the data shown. They are not a trading signal and carry no probability.</p>
        </header>
        <div>
          <h2 className="mb-2 font-serif text-lg font-semibold">Reference levels</h2>
          <table className="w-full text-sm">
            <thead className="text-left text-muted"><tr><th className="py-1 pr-3 font-medium">Level</th><th className="pr-3 font-medium">Price</th><th className="pr-3 font-medium">Known at</th><th className="font-medium">What would invalidate it</th></tr></thead>
            <tbody>{levels.map(o => (
              <tr key={o.id} className="border-t border-line align-top">
                <td className="py-1.5 pr-3">{o.label}</td><td className="pr-3 font-mono">{o.price.toFixed(5)}</td>
                <td className="pr-3 font-mono text-xs">{stamp(o.knownAt)}</td><td>{o.invalidation}</td></tr>))}</tbody>
          </table>
        </div>
        <div>
          <h2 className="mb-2 font-serif text-lg font-semibold">Session observations</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm">{events.map(o => <li key={o.id}><b>{o.label}</b> {o.text} <span className="text-muted">Invalidated by: {o.invalidation}</span></li>)}</ul>
        </div>
        <div>
          <h2 className="mb-2 font-serif text-lg font-semibold">Before the New York open</h2>
          <ul className="space-y-1 text-sm">{['Check each level above on the chart.', 'Note the invalidation condition for each item you rely on.',
            'Confirm the data feed is live and not sample data (check the label above).'].map(t => <li key={t}>☐ {t}</li>)}</ul>
        </div>
      </div>
    </section>)
}
