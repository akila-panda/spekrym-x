import { apiHint } from '../../data/DataProvider'
import { useExp001 } from '../../lab/useExp001'
import { Exp001Panel } from './Exp001Panel'

export function Exp001Tab() {
  const q = useExp001()
  if (q.isPending) return <p className="text-sm text-muted">Loading EXP-001 from the API at {apiHint} …</p>
  if (q.isError) return <p role="alert" className="rounded-md border border-line bg-surface2 p-3 text-sm">
    EXP-001 results could not be loaded ({q.error instanceof Error ? q.error.message : 'error'}). Nothing is shown in their place.</p>
  return <Exp001Panel data={q.data} />
}
