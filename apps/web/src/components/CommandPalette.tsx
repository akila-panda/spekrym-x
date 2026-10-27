import { Command } from 'cmdk'
import { useDataset } from '../data/DataProvider'
import { PRESETS } from '../layers/presets'
import { useUi, type Screen } from '../state/store'

const SCREENS: [Screen, string][] = [['premarket', 'Premarket'], ['chart', 'Chart'], ['suggestions', 'Suggestions'], ['paper', 'Paper'], ['lab', 'Lab'], ['journal', 'Journal']]
// Instrument and timeframe switching is intentionally absent: decisions P3 and P4 are still Proposed.

export function CommandPalette() {
  const ui = useUi()
  const { objects, steps } = useDataset()
  const run = (f: () => void) => () => { f(); ui.setPalette(false) }
  return (
    <Command.Dialog open={ui.paletteOpen} onOpenChange={ui.setPalette} label="Command palette"
      overlayClassName="fixed inset-0 bg-black/50" contentClassName="fixed left-1/2 top-24 w-[34rem] max-w-[92vw] -translate-x-1/2 overflow-hidden rounded-lg border border-line bg-surface shadow-xl">
      <Command.Input placeholder="Type a command…" aria-label="Search commands" className="w-full border-b border-line bg-transparent px-4 py-3 text-sm outline-none" />
      <Command.List className="max-h-80 overflow-y-auto p-2">
        <Command.Empty className="px-3 py-2 text-sm text-muted">No matching command.</Command.Empty>
        <Command.Group heading="Go to">
          {SCREENS.map(([id, label]) => <Item key={id} onSelect={run(() => ui.setScreen(id))}>{label}</Item>)}
        </Command.Group>
        <Command.Group heading="Premarket steps">
          {steps.map(s => <Item key={s.id} onSelect={run(() => { ui.setScreen('premarket'); ui.setStep(s.id) })}>Step {s.id}: {s.title}</Item>)}
        </Command.Group>
        <Command.Group heading="Layer presets">
          {PRESETS.map(p => <Item key={p.id} onSelect={run(() => ui.setPreset(p.id))}>Preset: {p.label}</Item>)}
        </Command.Group>
        <Command.Group heading="Layers">
          {objects.map(o => <Item key={o.id} onSelect={run(() => ui.toggleHidden(o.id))}>{ui.hidden.includes(o.id) ? 'Show' : 'Hide'} {o.label}</Item>)}
        </Command.Group>
        <Command.Group heading="View">
          <Item onSelect={run(() => ui.toggleTheme())}>Switch to {ui.theme === 'dark' ? 'light' : 'dark'} theme</Item>
          <Item onSelect={run(() => ui.setReplay(null))}>Replay: back to live</Item>
        </Command.Group>
      </Command.List>
    </Command.Dialog>)
}
const Item = ({ children, onSelect }: { children: React.ReactNode; onSelect: () => void }) =>
  <Command.Item onSelect={onSelect} className="cursor-pointer rounded-md px-3 py-2 text-sm data-[selected=true]:bg-surface2">{children}</Command.Item>
