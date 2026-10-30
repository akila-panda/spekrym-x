import { useEffect, useMemo, useState } from 'react'
import { Badge } from '../Badge'
import { fetchJob, startImport } from '../../labApi'
import type { DatasetList, ImportJob } from '../../contracts/datasets'
import { PRESETS, estimateBars, fileNameFor, presetRange, rangeProblem, type Range } from '../../lab/importForm'

type Props = { options: DatasetList['options']; existing: string[]; tokenConfigured: boolean; onFinished: () => void }
const field = 'rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-ink'

export function ImportWidget({ options, existing, tokenConfigured, onFinished }: Props) {
  const [instrument, setInstrument] = useState(options.instruments[0] ?? 'EUR_USD')
  const [tf, setTf] = useState(options.timeframes.includes('H1') ? 'H1' : options.timeframes[0] ?? 'H1')
  const [range, setRange] = useState<Range>(() => presetRange(24))
  const [job, setJob] = useState<ImportJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const running = job?.state === 'running'

  const problem = rangeProblem(range, tf, options.max_bars)
  const file = fileNameFor(instrument, tf, range)
  const exists = existing.includes(file)
  const bars = useMemo(() => estimateBars(range, tf), [range, tf])
  const blocked = !tokenConfigured || running || problem !== null || exists

  useEffect(() => {
    if (!job || job.state !== 'running') return
    const ctl = new AbortController()
    const timer = setTimeout(async () => {
      try {
        const next = await fetchJob(job.id, ctl.signal)
        setJob(next)
        if (next.state !== 'running') onFinished()
      } catch (e) {
        if (!ctl.signal.aborted) { setError(e instanceof Error ? e.message : String(e)); setJob(null) }
      }
    }, 1000)
    return () => { clearTimeout(timer); ctl.abort() }
  }, [job, onFinished])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try { setJob(await startImport({ instrument, tf, ...range })) }
    catch (err) { setError(err instanceof Error ? err.message : String(err)) }
  }

  return (
    <section aria-labelledby="import-h" className="space-y-4 rounded-md border border-line p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="import-h" className="font-serif text-lg font-semibold">Import data</h2>
        <div className="flex gap-2"><Badge tone="warn">OANDA practice feed</Badge><Badge>Not independently verified</Badge></div>
      </div>
      {!tokenConfigured && <p role="alert" className="rounded-md border border-line bg-surface2 p-3 text-sm">
        No OANDA token found. Add <span className="font-mono">OANDA_TOKEN=…</span> to your <span className="font-mono">.env</span> and restart the API. The token stays on the server and is never sent to this page.</p>}
      <form onSubmit={submit} className="space-y-4">
        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1 text-xs text-muted">Instrument
            <select className={field} value={instrument} onChange={e => setInstrument(e.target.value)}>
              {options.instruments.map(i => <option key={i} value={i}>{i.replace('_', '/')}</option>)}</select></label>
          <label className="flex flex-col gap-1 text-xs text-muted">Timeframe
            <select className={field} value={tf} onChange={e => setTf(e.target.value)}>
              {options.timeframes.map(t => <option key={t}>{t}</option>)}</select></label>
          <label className="flex flex-col gap-1 text-xs text-muted">Start (UTC)
            <input type="date" className={field} value={range.start} onChange={e => setRange({ ...range, start: e.target.value })} /></label>
          <label className="flex flex-col gap-1 text-xs text-muted">End (UTC, excluded)
            <input type="date" className={field} value={range.end} onChange={e => setRange({ ...range, end: e.target.value })} /></label>
        </div>
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Quick ranges ending today">
          <span className="text-xs text-muted">Last</span>
          {PRESETS.map(p => <button key={p.id} type="button" onClick={() => setRange(presetRange(p.months))}
            className="rounded-md border border-line px-2 py-1 text-xs text-muted hover:text-ink">{p.label}</button>)}
        </div>
        <p className="text-xs text-muted">About <span className="font-mono text-ink">{bars.toLocaleString('en-US')}</span> bars → <span className="font-mono text-ink">{file}</span></p>
        {problem && <p role="alert" className="text-sm text-bear">{problem}</p>}
        {exists && <p role="alert" className="text-sm text-bear">That file already exists (see Datasets on disk below). Delete it there if it is not in use, or choose another range, so a locked experiment never points at a replaced file.</p>}
        <div className="flex items-center gap-3">
          <button type="submit" disabled={blocked} className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-bg disabled:opacity-40">
            {running ? 'Downloading…' : 'Download'}</button>
          <span className="text-xs text-muted">Closed bars only. Quality is checked before anything is saved.</span>
        </div>
      </form>
      <div role="status" aria-live="polite">
        {error && <p className="text-sm text-bear">{error}</p>}
        {job && <JobView job={job} />}
      </div>
    </section>
  )
}

function JobView({ job }: { job: ImportJob }) {
  if (job.state === 'running') return <p className="text-sm">Downloading from the OANDA practice API… {Math.floor(job.elapsed_s)} s. This can take a minute for long ranges.</p>
  if (job.state !== 'done')
    return <div className="rounded-md border border-line bg-surface2 p-3 text-sm"><b className="text-bear">{job.state === 'refused' ? 'Refused' : 'Failed'}:</b> {job.message}. Nothing was saved.</div>
  const r = job.result
  return (
    <div className="space-y-1 rounded-md border border-line bg-surface2 p-3 text-sm">
      <b>Saved {r?.file}</b>
      <div className="font-mono text-xs">{(r?.n_bars ?? 0).toLocaleString('en-US')} bars · {r?.first_bar?.slice(0, 10)} → {r?.last_bar?.slice(0, 10)} · {r?.data_version}</div>
      <div className="text-xs text-muted">{r?.expected_gaps} expected gaps, {r?.unexpected_gaps} unexpected, {r?.flat_bars} flat bars. {r?.label}</div>
    </div>
  )
}
