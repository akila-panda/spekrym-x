import { useState } from 'react'
import type { TrashRow } from '../../contracts/datasets'

const btn = 'rounded-md border border-line px-2 py-1 text-xs hover:bg-surface2 disabled:opacity-50'
const kb = (b: number) => (b > 1e6 ? `${(b / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1e3))} KB`)
type Props = { rows: TrashRow[]; onRestore: (id: string) => Promise<void>; onPurge: (id: string) => Promise<void> }

// Trash: restore, or delete for good (second confirmation). Nothing here is ever used by an experiment.
export function TrashTable({ rows, onRestore, onPurge }: Props) {
  const [asking, setAsking] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (rows.length === 0) return null
  const run = async (fn: (id: string) => Promise<void>, id: string) => {
    setError(null)
    try { await fn(id) } catch (e) { setError(e instanceof Error ? e.message : 'Action failed') }
    setAsking(null)
  }
  return (
    <div className="space-y-2">
      <h2 className="font-serif text-lg font-semibold">Trash</h2>
      <p className="text-xs text-muted">Deleted files stay here until you delete them for good. Restore puts the file and its provenance record back.</p>
      {error && <p role="alert" className="text-sm text-bear">{error}</p>}
      <ul aria-label="Trash" className="divide-y divide-line rounded-md border border-line text-sm">
        {rows.map(r => (
          <li key={r.id} className="flex flex-wrap items-center gap-3 px-3 py-2">
            <span className="font-mono text-xs">{r.file}</span>
            <span className="text-xs text-muted">{kb(r.size_bytes)} · deleted {r.deleted_at.slice(0, 16).replace('T', ' ')} UTC</span>
            <span className="ml-auto flex items-center gap-1 text-xs">
              {asking === r.id ? <><span>Delete for good?</span>
                <button className={`${btn} text-bear`} onClick={() => void run(onPurge, r.id)}>Confirm</button>
                <button className={btn} onClick={() => setAsking(null)}>Cancel</button></>
                : <><button className={btn} onClick={() => void run(onRestore, r.id)} aria-label={`Restore ${r.file}`}>Restore</button>
                  <button className={btn} onClick={() => setAsking(r.id)} aria-label={`Delete ${r.file} for good`}>Delete for good</button></>}
            </span>
          </li>))}
      </ul>
    </div>)
}
