import { useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiHint } from '../../data/DataProvider'
import { deleteDataset, fetchDatasets, purgeDataset, restoreDataset } from '../../labApi'
import { DatasetTable } from './DatasetTable'
import { ImportWidget } from './ImportWidget'
import { TrashTable } from './TrashTable'

export function LabDataTab() {
  const q = useQuery({ queryKey: ['lab-datasets'], queryFn: ({ signal }) => fetchDatasets(signal), retry: false })
  const { refetch } = q
  const refresh = useCallback(() => { void refetch() }, [refetch])
  const then = (fn: (x: string) => Promise<void>) => async (x: string) => { await fn(x); await refetch() }
  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">Download candles for experiments. Files are saved with a provenance record so an experiment can be tied to exactly this data.</p>
      {q.isPending && <p className="text-sm text-muted">Loading from the API at {apiHint} …</p>}
      {q.isError && <p role="alert" className="rounded-md border border-line bg-surface2 p-3 text-sm">
        The API is not reachable ({q.error instanceof Error ? q.error.message : 'error'}). Start it with:
        <code className="mt-1 block font-mono text-xs">python -m uvicorn sx_api.main:create_app --factory --port 8000</code></p>}
      {q.data && <>
        <ImportWidget options={q.data.options} existing={q.data.items.map(i => i.file)}
          tokenConfigured={q.data.token_configured} onFinished={refresh} />
        <div className="space-y-2">
          <h2 className="font-serif text-lg font-semibold">Datasets on disk</h2>
          <DatasetTable rows={q.data.items} folder={q.data.folder} onDelete={then(deleteDataset)} />
        </div>
        <TrashTable rows={q.data.trash} onRestore={then(restoreDataset)} onPurge={then(purgeDataset)} />
      </>}
    </div>)
}
