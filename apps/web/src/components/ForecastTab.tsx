import { useUi } from '../state/store'
import { useExp001 } from '../lab/useExp001'
import { Badge } from './Badge'

/** The Inspector's Forecast tab. No live forecast exists for a chart object; this shows the one
 *  Lab result there is (EXP-001), with both stages, and never a bare probability. */
export function ForecastTab() {
  const setScreen = useUi(s => s.setScreen)
  const q = useExp001()
  const d = q.data
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2"><Badge>Exploratory</Badge><Badge>Not validated</Badge><Badge>Retrospective</Badge></div>
      <p className="text-sm">No forecast exists yet for this object. No live forecast is produced; the Lab has only evaluated volatility models on past data.</p>
      {q.isPending && <p className="text-xs text-muted">Loading Lab results …</p>}
      {q.isError && <p role="alert" className="text-xs text-muted">Lab results are unavailable (API not reachable).</p>}
      {d && d.validation && (
        <dl className="space-y-1 text-sm">
          <div><dt className="text-muted">EXP-001 holdout</dt><dd>{d.holdout ? d.holdout.outcome.toUpperCase() : 'not opened'}</dd></div>
          <div><dt className="text-muted">EXP-001 validation</dt><dd>{d.validation.outcome.toUpperCase()}</dd></div>
          <div><dt className="text-muted">Variants tried</dt><dd>{(d.holdout ?? d.validation).variants_tried} of 20</dd></div>
          <div><dt className="text-muted">Data</dt><dd className="break-words text-xs">{(d.holdout ?? d.validation).data_label}</dd></div>
        </dl>)}
      {d && d.status === 'not_run' && <p className="text-xs text-muted">EXP-001 has not been run.</p>}
      <button onClick={() => setScreen('lab')} className="rounded-md border border-line px-3 py-1 text-sm hover:bg-surface2">Open Lab results</button>
    </div>)
}
