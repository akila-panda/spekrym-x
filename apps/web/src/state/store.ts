import { create } from 'zustand'
import { defaultPresetFor, type PresetId } from '../layers/presets'

export type Screen = 'premarket' | 'chart' | 'suggestions' | 'paper' | 'lab' | 'journal'
export type Theme = 'dark' | 'light'
export type InspectorTab = 'insight' | 'evidence' | 'forecast'

export type UiState = {
  screen: Screen; theme: Theme; step: number; hidden: string[]; selected: string | null
  preset: PresetId; replayT: number | null; inspectorTab: InspectorTab; paletteOpen: boolean
  setScreen: (s: Screen) => void; setTheme: (t: Theme) => void; toggleTheme: () => void
  setStep: (n: number) => void; toggleHidden: (id: string) => void; select: (id: string | null) => void
  setPreset: (p: PresetId) => void; setReplay: (t: number | null) => void
  setInspectorTab: (t: InspectorTab) => void; setPalette: (open: boolean) => void
}

function readTheme(): Theme {
  try { return localStorage.getItem('sx-theme') === 'light' ? 'light' : 'dark' } catch { return 'dark' }
}
function saveTheme(t: Theme) { try { localStorage.setItem('sx-theme', t) } catch { /* storage unavailable */ } }

export const initialState = () => ({
  screen: 'premarket' as Screen, theme: readTheme(), step: 3, hidden: [] as string[], selected: 'sweep' as string | null,
  preset: 'premarket' as PresetId, replayT: null as number | null, inspectorTab: 'insight' as InspectorTab, paletteOpen: false
})

export const useUi = create<UiState>((set, get) => ({
  ...initialState(),
  // Changing screen resets replay (so a stale replay never leaks) and applies that screen's default preset.
  setScreen: screen => set({ screen, replayT: null,
    preset: screen === 'chart' || screen === 'premarket' ? defaultPresetFor(screen) : get().preset }),
  setTheme: theme => { saveTheme(theme); set({ theme }) },
  toggleTheme: () => get().setTheme(get().theme === 'dark' ? 'light' : 'dark'),
  setStep: step => set({ step: Math.min(6, Math.max(1, step)) }),
  toggleHidden: id => set(s => ({ hidden: s.hidden.includes(id) ? s.hidden.filter(x => x !== id) : [...s.hidden, id] })),
  select: selected => set({ selected }),
  setPreset: preset => set({ preset }),
  setReplay: replayT => set({ replayT }),
  setInspectorTab: inspectorTab => set({ inspectorTab }),
  setPalette: paletteOpen => set({ paletteOpen })
}))
