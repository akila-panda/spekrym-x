import { Badge } from '../Badge'
import type { DatasetRow } from '../../contracts/datasets'
import { DatasetActions } from './DatasetActions'

const n = (v: number | null | undefined) => (v ?? 0).toLocaleString('en-US')
const day = (iso?: string | null) => (iso ? iso.slice(0, 10) : '?')
const kb = (b: number) => (b > 1e6 ? `${(b / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1e3))} KB`)

const PROBLEM: Record<string, string> = {
  modified: 'File changed after download; re-download before using it.',
  no_provenance: 'Not downloaded here (no provenance record).',
  unreadable: 'Provenance record is not valid.'
}

function Quality({ r }: { r: DatasetRow }) {
  if (r.integrity !== 'ok')
    return <Badge tone="warn">{r.integrity === 'modified' ? 'Changed since import' : r.integrity === 'no_provenance' ? 'No provenance' : 'Unreadable'}</Badge>
  return r.feed_degraded ? <Badge tone="warn">Degraded</Badge> : <Badge>Checked</Badge>
}

type Props = { rows: DatasetRow[]; folder: string; onDelete: (file: string) => Promise<void> }

export function DatasetTable({ rows, folder, onDelete }: Props) {
  if (rows.length === 0)
    return <p className="rounded-md border border-line p-4 text-sm text-muted">No datasets yet. Download one above; it is saved in <span className="font-mono">{folder}</span>.</p>
  return (
    <div className="overflow-x-auto rounded-md border border-line">
      <table className="w-full text-sm">
        <caption className="sr-only">Datasets on disk</caption>
        <thead className="bg-surface2 text-left text-muted">
          <tr>{['File', 'Range (UTC)', 'Bars', 'Gaps (exp / unexp)', 'Quality', 'Source label', 'Data version', 'Actions'].map(h => <th key={h} scope="col" className="whitespace-nowrap px-3 py-2 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>{rows.map(r => (
          <tr key={r.file} className="border-t border-line align-top">
            <td className="px-3 py-2"><div className="whitespace-nowrap font-mono text-xs">{r.file}</div>
              <div className="text-xs text-muted">{kb(r.size_bytes)}{r.integrity !== 'ok' ? ` · ${PROBLEM[r.integrity]}` : ''}</div></td>
            <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{r.first_bar ? `${day(r.first_bar)} → ${day(r.last_bar)}` : '—'}</td>
            <td className="px-3 py-2 font-mono text-xs">{r.n_bars != null ? n(r.n_bars) : '—'}</td>
            <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{r.n_bars != null ? `${n(r.expected_gaps)} / ${n(r.unexpected_gaps)}` : '—'}</td>
            <td className="whitespace-nowrap px-3 py-2"><Quality r={r} /></td>
            <td className="px-3 py-2 text-xs">{r.label ?? 'No label recorded'}</td>
            <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{r.data_version ?? '—'}</td>
            <td className="px-3 py-2"><DatasetActions row={r} onDelete={onDelete} /></td>
          </tr>))}</tbody>
      </table>
    </div>
  )
}
