import type { SuggestionsPayload } from '../../contracts/suggestions'
import { num3 } from '../../suggestions/format'
import { Badge } from '../Badge'

type Scorer = SuggestionsPayload['scorer']

export function ScorerBanner({ scorer, labels, source }: { scorer: Scorer; labels: string[]; source: string }) {
  const v = scorer.validation, h = scorer.holdout
  return (
    <section aria-label="What the 9A evaluation says" className="space-y-2 rounded-md border border-line bg-surface p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        {labels.map(l => <Badge key={l}>{l}</Badge>)}<Badge tone="warn">{source}</Badge></div>
      <p><b>9A reading:</b> {scorer.reading}</p>
      {v && (
        <p className="text-xs text-muted">
          Validation (n = {v.metrics.n}): AUC {num3(v.metrics.auc)}, interval {num3(v.metrics.auc_ci95_iid[0])} to {num3(v.metrics.auc_ci95_iid[1])} (optimistic, rows overlap).
          Shuffled-label 95th AUC {v.shuffled_auc_p95 == null ? 'missing' : num3(v.shuffled_auc_p95)}.
          Among the top-scored fifth (n = {v.metrics.top_fifth_n}) the target came first in a share of {num3(v.metrics.top_fifth_target_first_share)}, against a base share of {num3(v.metrics.target_first_share_all)}.
          Negative controls {v.controls_behaved ? 'behaved as expected' : 'did NOT all behave as expected'}. Variants tried: {v.variants_tried ?? 'unknown'}.
          {h ? ` Holdout opened once (n = ${h.metrics.n}, AUC ${num3(h.metrics.auc)}).` : ' Holdout not opened.'}</p>)}
    </section>)
}
