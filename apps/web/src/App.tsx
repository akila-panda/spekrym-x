import { useEffect, useLayoutEffect } from 'react'
import { LabScreen } from './screens/LabScreen'
import { SuggestionsScreen } from './screens/SuggestionsScreen'
import { Workspace } from './screens/Workspace'
import { Badge } from './components/Badge'
import { CommandPalette } from './components/CommandPalette'
import { Kbd } from './components/Kbd'
import { apiHint, useData } from './data/DataProvider'
import { useUi, type Screen } from './state/store'

const NAV: [Screen, string][] = [['premarket', 'Premarket'], ['chart', 'Chart'], ['suggestions', 'Suggestions'], ['paper', 'Paper'], ['lab', 'Lab'], ['journal', 'Journal']]

export default function App() {
  const { screen, setScreen, theme, toggleTheme, paletteOpen, setPalette } = useUi()
  const { dataset, status, error } = useData()
  // X17: the premarket sample badge and status text describe the chart sample, not the Lab.
  const onLab = screen === 'lab'
  useLayoutEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPalette(!useUi.getState().paletteOpen) }
    }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [setPalette])

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <header className="no-print flex h-12 shrink-0 items-center gap-4 border-b border-line px-4">
        <span className="font-semibold"><span className="text-accent">▍</span>spekrym-x</span>
        <span className="font-mono text-sm">EUR/USD</span>
        <span className="rounded-md bg-surface2 px-2 py-0.5 font-mono text-xs">M15</span>
        <span className="text-xs text-muted">Asia · London · <b className="text-ink">New York</b> next</span>
        <div className="ml-auto flex items-center gap-3">
          {!onLab && <Badge tone="warn">{dataset.badge}</Badge>}
          <button aria-label="Open command palette" aria-expanded={paletteOpen} onClick={() => setPalette(true)}
            className="flex items-center gap-2 rounded-md border border-line px-2 py-1 text-xs text-muted hover:text-ink">Commands <Kbd>⌘K</Kbd></button>
          <button className="rounded-md border border-line px-2 py-1 text-xs text-muted hover:text-ink" onClick={toggleTheme}>
            {theme === 'dark' ? 'Light' : 'Dark'} mode</button>
        </div>
      </header>
      {status !== 'api' && (
        <div role="status" className="no-print border-b border-line bg-surface2 px-4 py-1 text-xs">
          {status === 'loading' ? `Loading from the API at ${apiHint} …` : status === 'error'
            ? `API not reachable (${error}). Showing the built-in offline sample, not API data. Start it with: python -m uvicorn sx_api.main:create_app --factory --port 8000`
            : 'Offline sample mode (VITE_DATA_SOURCE=sample).'}</div>)}
      <div className="flex min-h-0 flex-1">
        <nav aria-label="Screens" className="no-print flex w-36 shrink-0 flex-col gap-1 border-r border-line p-2">
          {NAV.map(([id, label]) => (
            <button key={id} onClick={() => setScreen(id)} aria-current={screen === id ? 'page' : undefined}
              className={`rounded-md px-3 py-2 text-left text-sm ${screen === id ? 'bg-surface2 text-ink' : 'text-muted hover:text-ink'}`}>
              {screen === id && <span className="mr-1 text-accent" aria-hidden="true">▍</span>}{label}</button>))}
        </nav>
        <main className="min-w-0 flex-1">
          {screen === 'premarket' || screen === 'chart' ? <Workspace key={screen} mode={screen} /> : screen === 'lab' ? <LabScreen /> : screen === 'suggestions' ? <SuggestionsScreen /> : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
              <h1 className="font-serif text-xl">{NAV.find(n => n[0] === screen)![1]}</h1>
              <p className="max-w-sm text-sm text-muted">Not built yet. This screen will use real data once the backend exists.</p>
              <Badge tone="warn">Placeholder</Badge></div>)}
        </main>
      </div>
      <footer className="no-print flex h-7 shrink-0 items-center gap-4 border-t border-line px-4 font-mono text-xs text-muted">
        <span className="text-accent">PAPER</span>
        {onLab ? <span>Lab: each panel shows the provenance of its own data</span>
          : <><span>{dataset.label}</span><span>last {dataset.lastClose.toFixed(5)}</span></>}
      </footer>
      <CommandPalette />
    </div>
  )
}
