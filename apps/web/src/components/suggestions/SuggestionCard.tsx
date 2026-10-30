import type { SuggestionsPayload } from '../../contracts/suggestions'
import { price, rankText, when } from '../../suggestions/format'
import { Badge } from '../Badge'

type Item = SuggestionsPayload['items'][number]
type Props = { item: Item; rankShown: boolean; selected: boolean; evidenceId: string | null; onSelect: () => void; onEvidence: (id: string) => void }

export function SuggestionCard({ item, rankShown, selected, evidenceId, onSelect, onEvidence }: Props) {
  const s = item.suggestion
  return (
    <article aria-label={`Suggestion ${s.side} ${s.id}`} className={`space-y-2 rounded-md border p-3 text-sm ${selected ? 'border-accent' : 'border-line'}`}>
      <header className="flex flex-wrap items-center gap-2">
        <button onClick={onSelect} aria-pressed={selected} className="font-semibold uppercase">{s.side}</button>
        <span className="font-mono text-xs text-muted">{when(s.created_at)}</span>
        {item.labels.map(l => <Badge key={l}>{l}</Badge>)}</header>
      <p className="font-mono text-xs">Entry {price(s.entry)} · Stop {price(s.stop)} · Target {price(s.target)}</p>
      <p className="text-xs text-muted">{rankText(s.score, rankShown)}. Model {item.model_version}.</p>
      <ul aria-label="Reasons" className="space-y-1">
        {s.reasons.map((r, i) => (
          <li key={i}><button onClick={() => onEvidence(r.evidence_id)} aria-pressed={evidenceId === r.evidence_id}
            title="Show the linked setup on the chart" className="text-left underline decoration-dotted underline-offset-2">{r.text}</button></li>))}
      </ul>
      <ul aria-label="Risk gates" className="flex flex-wrap gap-2 text-xs">
        {s.gates.map(g => <li key={g.name} title={g.detail}><Badge tone={g.passed ? 'muted' : 'warn'}>{g.name}: {g.passed ? 'clear' : 'blocked'}</Badge></li>)}</ul>
      <p className="text-xs text-muted">Rules {s.rules_version}. Gates here are advice; they are applied again when an order is placed. No order has been placed.</p>
    </article>)
}
