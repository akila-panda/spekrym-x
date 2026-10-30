import { Badge } from '../Badge'
import type { Exp001 } from '../../contracts/exp001'
import { MAX_VARIANTS, q, stagesOf, trainVsValidation } from '../../lab/exp001Format'
import { StageCard } from './Exp001Stage'

export function Exp001Panel({ data }: { data: Exp001 }) {
  if (data.status === 'not_run' || !data.validation)
    return <p className="rounded-md border border-line p-4 text-sm text-muted">EXP-001 has not been run yet. Run <code className="font-mono text-xs">sx-lab exp001-validate</code> on the machine that holds the data.</p>
  const head = data.holdout ?? data.validation
  const diag = trainVsValidation(data.validation)
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Badge>Exploratory</Badge><Badge>Not validated</Badge><Badge>Retrospective</Badge><Badge tone="warn">{head.data_label}</Badge>
      </div>
      <section aria-label="Experiment summary" className="space-y-1 rounded-md border border-line bg-surface2 p-4">
        <h2 className="font-serif text-lg font-semibold">EXP-001: MiniMamba vs HAR and GARCH(1,1), H1 EUR/USD volatility</h2>
        {data.holdout
          ? <p className="text-sm">Holdout: <strong>{data.holdout.outcome.toUpperCase()}</strong>. Validation: <strong>{data.validation.outcome.toUpperCase()}</strong>. Both are shown below; the validation result is not hidden behind the holdout.</p>
          : <p className="text-sm">Validation: <strong>{data.validation.outcome.toUpperCase()}</strong>. The holdout has not been opened.</p>}
        <p className="text-xs text-muted">Variants tried: {head.variants_tried} of {MAX_VARIANTS} allowed. Spec <span className="font-mono">{head.spec_hash.slice(0, 16)}</span>, data <span className="font-mono">{head.data_version}</span>.
          One instrument, one period, one feed. A tie or a loss is a valid result. This is not a trading signal and makes no profit claim.</p>
      </section>
      {stagesOf(data).map(s => <StageCard key={s.stage} s={s} headline={s.stage === 'holdout'} />)}
      {diag.length > 0 && (
        <section aria-label="Training versus validation" className="space-y-1 rounded-md border border-line p-4">
          <h3 className="font-serif text-lg font-semibold">Training loss vs validation QLIKE, per seed</h3>
          <ul className="text-sm">{diag.map(d => <li key={d.seed}>{d.seed}: last-epoch training loss {q(d.train)}, validation QLIKE {q(d.validation)}</li>)}</ul>
          <p className="text-xs text-muted">Diagnostic only. The reported MiniMamba score is the mean of the three seeds' log-variance forecasts; no seed was selected (L21).</p>
        </section>)}
      <p className="text-xs text-muted">Full text: <span className="font-mono">lab/experiments/EXP-001_mamba_vs_har.md</span>{data.report_present ? '' : ' (not written yet; run sx-lab exp001-report)'}. A different training recipe is a new pre-registered experiment (EXP-002), not an edit of this one.</p>
    </div>)
}
