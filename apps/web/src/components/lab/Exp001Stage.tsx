import { Badge } from '../Badge'
import type { Exp001Stage } from '../../contracts/exp001'
import { cov, nRows, OUTCOME_TEXT, q, r } from '../../lab/exp001Format'

const NAME: Record<string, string> = { har: 'HAR', garch11: 'GARCH(1,1)', minimamba: 'MiniMamba',
  historical_mean: 'Historical mean', persistence: 'Persistence' }
const label = (m: string) => NAME[m] ?? m

export function StageCard({ s, headline }: { s: Exp001Stage; headline: boolean }) {
  const title = s.stage === 'holdout' ? 'Holdout (opened once)' : 'Validation'
  const inc = new Set(s.mcs.included)
  const rows = Object.entries(s.scores).sort((a, b) => a[1].qlike - b[1].qlike)
  return (
    <article aria-label={`${title} result`} className="space-y-3 rounded-md border border-line p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-serif text-lg font-semibold">{title} · n = {nRows(s).toLocaleString('en-US')}</h3>
        <div className="flex gap-2">{headline && <Badge tone="accent">Headline (L22)</Badge>}
          <Badge tone="warn">Outcome: {s.outcome.toUpperCase()}</Badge></div>
      </header>
      <p className="text-sm text-muted">{OUTCOME_TEXT[s.outcome]}</p>
      <div className="overflow-x-auto rounded-md border border-line">
        <table className="w-full text-sm">
          <caption className="sr-only">{title} scores and model confidence set</caption>
          <thead className="bg-surface2 text-left text-muted"><tr>
            {['Model', 'QLIKE (lower is better)', 'RMSE', 'In confidence set', 'MCS p-value'].map(h =>
              <th key={h} scope="col" className="whitespace-nowrap px-3 py-2 font-medium">{h}</th>)}</tr></thead>
          <tbody>{rows.map(([m, sc]) => { const p = s.mcs.pvalues[m]
            return (<tr key={m} className="border-t border-line">
              <th scope="row" className="px-3 py-2 text-left font-medium">{label(m)}</th>
              <td className="px-3 py-2 font-mono text-xs">{q(sc.qlike)}</td>
              <td className="px-3 py-2 font-mono text-xs">{r(sc.rmse)}</td>
              <td className="px-3 py-2">{inc.has(m) ? 'Yes' : 'No'}</td>
              <td className="px-3 py-2 font-mono text-xs">{p == null ? '–' : p.toFixed(3)}</td></tr>) })}</tbody>
        </table>
      </div>
      <p className="text-xs text-muted">Confidence set: level {s.mcs.level}, {s.mcs.reps} repetitions, block {s.mcs.block_size}, seed {s.mcs.seed}.
        Being in the set means the data could not rule the model out; it is not a ranking by win rate.</p>
      <div>
        <h4 className="text-sm font-medium">Interval coverage (split-conformal, nominal {cov(Object.values(s.conformal)[0]?.nominal ?? 0.8)})</h4>
        <ul className="mt-1 space-y-1 text-sm">{Object.entries(s.conformal).map(([m, c]) => (
          <li key={m}><span className="font-medium">{label(m)}</span>: measured {cov(c.empirical)} on {c.n.toLocaleString('en-US')} rows
            (calibrated on {c.n_calibration.toLocaleString('en-US')}; mean width ratio {c.mean_width_ratio.toFixed(2)}
            {c.worst_rolling_50 !== null && `; worst rolling-50 ${c.worst_rolling_50.toFixed(2)}`})</li>))}</ul>
        <p className="mt-1 text-xs text-muted">Volatility breaks the exchangeability that split-conformal assumes, so coverage is measured, never assumed.</p>
      </div>
    </article>)
}
