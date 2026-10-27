import { PRESETS } from '../layers/presets'
import { useUi } from '../state/store'

export function LayerControls() {
  const { preset, setPreset } = useUi()
  return (
    <div role="group" aria-label="Layer presets" className="flex gap-1">
      {PRESETS.map(p => (
        <button key={p.id} aria-pressed={preset === p.id} title={p.note} onClick={() => setPreset(p.id)}
          className={`rounded-md border px-2 py-1 text-xs ${preset === p.id ? 'border-accent bg-surface2 text-ink' : 'border-line text-muted hover:text-ink'}`}>{p.label}</button>))}
    </div>)
}
