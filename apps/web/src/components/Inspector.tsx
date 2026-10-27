import { useRef } from 'react'
import type { Obj } from '../data/sample'
import { useDataset } from '../data/DataProvider'
import { barsKnownAt } from '../layers/replay'
import { ATR_PERIOD, distanceFrom, wilderAtr } from '../layers/atr'
import { semanticId } from '../data/toSetup'
import { stamp } from '../layers/timeline'
import { useUi, type InspectorTab } from '../state/store'
import { Badge } from './Badge'

const TABS: [InspectorTab, string][] = [['insight', 'Insight'], ['evidence', 'Evidence'], ['forecast', 'Forecast']]

export function Inspector() {
  const { selected, inspectorTab, setInspectorTab, replayT } = useUi()
  const ds = useDataset()
  const { objects } = ds
  const known = barsKnownAt(ds.bars, replayT)
  const refPrice = known.length ? known[known.length - 1].close : ds.lastClose
  const atr = wilderAtr(known)
  const refs = useRef<Record<string, HTMLButtonElement | null>>({})
  const sel = objects.find(o => o.id === selected)
  const move = (e: React.KeyboardEvent, i: number) => {
    const j = e.key === 'ArrowRight' ? (i + 1) % TABS.length : e.key === 'ArrowLeft' ? (i + TABS.length - 1) % TABS.length : -1
    if (j >= 0) { setInspectorTab(TABS[j][0]); refs.current[TABS[j][0]]?.focus() }
  }
  return (
    <aside aria-label="Inspector" className="w-72 shrink-0 overflow-y-auto border-l border-line p-4">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Inspector</div>
      <div role="tablist" aria-label="Inspector sections" className="mb-3 flex gap-1">
        {TABS.map(([id, label], i) => (
          <button key={id} role="tab" id={`tab-${id}`} aria-selected={inspectorTab === id} aria-controls={`panel-${id}`}
            tabIndex={inspectorTab === id ? 0 : -1} ref={el => { refs.current[id] = el }}
            onClick={() => setInspectorTab(id)} onKeyDown={e => move(e, i)}
            className={`rounded-md px-2 py-1 text-sm ${inspectorTab === id ? 'bg-surface2 text-ink' : 'text-muted hover:text-ink'}`}>{label}</button>))}
      </div>
      <div role="tabpanel" id={`panel-${inspectorTab}`} aria-labelledby={`tab-${inspectorTab}`}>
        {inspectorTab === 'forecast' ? <ForecastPlaceholder /> : !sel
          ? <p className="text-sm text-muted">Select an object to see why it was drawn.</p>
          : inspectorTab === 'insight' ? <Insight o={sel} ds={ds} refPrice={refPrice} atr={atr} /> : <Evidence o={sel} ds={ds} />}
      </div>
    </aside>
  )
}
type O = Obj
type Ds = ReturnType<typeof useDataset>

function Insight({ o, ds, refPrice, atr }: { o: O; ds: Ds; refPrice: number; atr: number | null }) {
  const d = distanceFrom(o.price, refPrice, atr, ds.instrument)
  return (
    <div className="space-y-3">
      <h2 className="font-serif text-lg font-semibold">{o.label}</h2>
      <div className="flex flex-wrap gap-2"><Badge tone="warn">{ds.badge}</Badge><Badge>Causal</Badge><Badge>Not validated</Badge></div>
      <p className="text-sm">{o.text}</p>
      <dl className="space-y-1 text-sm">
        <div><dt className="text-muted">Price</dt><dd className="font-mono">{o.span ? `${o.span.low.toFixed(5)} to ${o.span.high.toFixed(5)}` : o.price.toFixed(5)}</dd></div>
        <div><dt className="text-muted">Known at</dt><dd className="font-mono">{stamp(o.knownAt)}</dd></div>
        <div><dt className="text-muted">Distance from last close</dt><dd className="font-mono">{d.pips.toFixed(1)} pips{d.atrMultiple !== null && ` · ${d.atrMultiple.toFixed(2)} × ATR(${ATR_PERIOD}, M15)`}</dd>
          <dd className="text-xs text-muted">{d.atrPips !== null ? `ATR(${ATR_PERIOD}) is ${d.atrPips.toFixed(1)} pips on closed M15 bars. A measurement of distance, not a forecast.` : `ATR needs ${ATR_PERIOD + 1} closed bars.`}</dd></div>
        {o.lifecycle && <div><dt className="text-muted">State</dt><dd>{o.lifecycle}</dd></div>}
        <div><dt className="text-muted">What would invalidate it</dt><dd>{o.invalidation}</dd></div>
      </dl>
    </div>)
}
function Evidence({ o, ds }: { o: O; ds: Ds }) {
  const id = o.setupId ?? semanticId([o.kind === 'event' ? 'liquidity_sweep' : 'session_level', 'EUR_USD', 'M15', o.id, o.session])
  const rows: [string, string][] = [
    ['Setup id', id], ['Kind', o.setupKind ?? (o.kind === 'event' ? 'liquidity_sweep' : 'session_level')], ['Data source', ds.label],
    ['Event time', stamp(o.time ?? o.knownAt)], ['Known at', stamp(o.knownAt)],
    ['Source', o.sourceText ?? 'sample / sample-fixture (seeded random walk, seed 42)'], ['Status', `${o.status ?? 'causal'}, not validated`]]
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2"><Badge tone="warn">{ds.badge}</Badge><Badge>Causal</Badge></div>
      <dl className="space-y-1 text-sm">{rows.map(([k, v]) => <div key={k}><dt className="text-muted">{k}</dt><dd className="break-words font-mono text-xs">{v}</dd></div>)}</dl>
      <p className="text-xs text-muted">The id is a hash of semantic fields only, not of price, so it stays stable when the price moves.</p>
    </div>)
}
function ForecastPlaceholder() {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2"><Badge tone="warn">Placeholder</Badge><Badge>Exploratory</Badge><Badge>Not validated</Badge></div>
      <p className="text-sm">No forecast exists yet. The Lab module (volatility and regime forecasts with intervals) is built in a later phase.</p>
      <p className="text-xs text-muted">When it exists this tab will show an interval, the regime label, the track record and the number of variants tried. It will never show a bare probability.</p>
    </div>)
}
