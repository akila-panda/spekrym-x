import { useState } from 'react'
import { Badge } from '../components/Badge'
import { EvidenceChart } from '../components/suggestions/EvidenceChart'
import { ScorerBanner } from '../components/suggestions/ScorerBanner'
import { SuggestionCard } from '../components/suggestions/SuggestionCard'
import { apiHint } from '../data/DataProvider'
import { rankDemonstrated, when } from '../suggestions/format'
import { useSuggestions } from '../suggestions/suggestionsApi'

export function SuggestionsScreen() {
  const q = useSuggestions()
  const [pick, setPick] = useState<{ id: string; evidence: string | null } | null>(null)
  if (q.isPending) return <p className="p-6 text-sm text-muted">Loading suggestions from the API at {apiHint} …</p>
  if (q.isError) return <p role="alert" className="m-6 rounded-md border border-line bg-surface2 p-3 text-sm">
    Suggestions could not be loaded ({q.error instanceof Error ? q.error.message : 'error'}). Nothing is shown in their place.</p>
  const d = q.data
  const cur = d.items.find(i => i.suggestion.id === pick?.id) ?? d.items[0]
  const evId = pick?.evidence ?? cur?.suggestion.setup_ids[0] ?? null
  const setup = d.evidence.find(e => e.id === evId) ?? null
  const s = cur?.suggestion
  return (
    <section aria-label="Suggestions" className="h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="space-y-1">
          <h1 className="font-serif text-2xl font-semibold">Suggestions</h1>
          <p className="text-xs text-muted">{d.instrument.replace('_', '/')} {d.tf} · as of {when(d.as_of)} · every claim links to a setup. Not trade advice.</p>
        </header>
        <ScorerBanner scorer={d.scorer} labels={d.labels} source={d.source.label} />
        {d.items.length === 0 ? (
          <p role="status" className="rounded-md border border-line bg-surface2 p-3 text-sm">{d.note} <Badge>No suggestions</Badge></p>
        ) : (
          <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
            <div className="space-y-3">
              {d.items.map(i => <SuggestionCard key={i.suggestion.id} item={i} rankShown={rankDemonstrated(d.scorer)} selected={i.suggestion.id === cur.suggestion.id}
                evidenceId={evId} onSelect={() => setPick({ id: i.suggestion.id, evidence: null })}
                onEvidence={id => setPick({ id: i.suggestion.id, evidence: id })} />)}
            </div>
            <div className="space-y-2">
              <EvidenceChart candles={d.candles} setup={setup} levels={s ? { entry: s.entry, stop: s.stop, target: s.target } : null} />
              {setup && (
                <aside aria-label="Linked evidence" className="space-y-1 rounded-md border border-line bg-surface p-3 text-sm">
                  <p><b>{setup.kind.replace('_', ' ')}</b> · {setup.direction} · {setup.lifecycle} · <Badge>{setup.status === 'causal' ? 'Causal' : 'Retrospective'}</Badge></p>
                  <p>{setup.plain_text}</p>
                  <p className="text-xs text-muted">Known at {when(setup.known_at)}. Invalidation: {setup.invalidation}</p>
                </aside>)}
              <p className="text-xs text-muted">{d.note}</p>
            </div>
          </div>)}
        {d.rejected.length > 0 && <p className="text-xs text-muted">{d.rejected.length} setup(s) were rejected by the evidence rules and are not shown.</p>}
      </div>
    </section>)
}
