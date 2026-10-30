import { useState } from 'react'
import { Badge } from '../Badge'
import type { DatasetRow } from '../../contracts/datasets'

const btn = 'rounded-md border border-line px-2 py-1 text-xs hover:bg-surface2 disabled:opacity-50'

// Delete is two steps (button, then confirm). Files a locked experiment or saved model uses cannot be deleted here.
export function DatasetActions({ row, onDelete }: { row: DatasetRow; onDelete: (file: string) => Promise<void> }) {
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  if ((row.in_use ?? []).length > 0)
    return <div className="space-y-1"><span title={`Used by: ${(row.in_use ?? []).join(', ')}`}><Badge tone="accent">In use</Badge></span>
      <p className="max-w-[14rem] text-xs text-muted">Used by {(row.in_use ?? []).join(', ')}. Cannot be deleted from here.</p></div>
  const run = async () => {
    setBusy(true); setError(null)
    try { await onDelete(row.file) } catch (e) { setError(e instanceof Error ? e.message : 'Delete failed'); setBusy(false); setAsking(false) }
  }
  return (
    <div className="space-y-1">
      {!asking ? <button className={btn} onClick={() => setAsking(true)} aria-label={`Delete ${row.file}`}>Delete</button> : (
        <div className="flex flex-wrap items-center gap-1 text-xs">
          <span>Move to trash?</span>
          <button className={`${btn} text-bear`} disabled={busy} onClick={run}>Confirm</button>
          <button className={btn} disabled={busy} onClick={() => setAsking(false)}>Cancel</button></div>)}
      {error && <p role="alert" className="max-w-[14rem] text-xs text-bear">{error}</p>}
    </div>)
}
