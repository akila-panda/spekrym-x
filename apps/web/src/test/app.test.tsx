import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'
import { useUi } from '../state/store'
import { objects } from '../data/sample'

// jsdom has no canvas; the chart itself is covered by the pure-logic tests and the Playwright smoke test.
vi.mock('../components/Chart', () => ({
  Chart: (p: { visible: string[]; replayT: number | null }) =>
    <div data-testid="chart" data-visible={p.visible.join(',')} data-replay={String(p.replayT)} />
}))

const drawn = () => (screen.getByTestId('chart').dataset.visible ?? '').split(',').filter(Boolean)

describe('shell', () => {
  it('shows honesty labels and the paper status line', () => {
    render(<App />)
    expect(screen.getAllByText('Sample data').length).toBeGreaterThan(0)
    expect(screen.getByText('PAPER')).toBeInTheDocument()
  })
  it('switches screens and marks the current one', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Chart' }))
    expect(screen.getByRole('button', { name: 'Chart' })).toHaveAttribute('aria-current', 'page')
    await userEvent.click(screen.getByRole('button', { name: 'Journal' }))
    expect(screen.getByText(/Not built yet/)).toBeInTheDocument()
  })
  it('toggles and persists the theme', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Light mode' }))
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(localStorage.getItem('sx-theme')).toBe('light')
  })
})

describe('command palette', () => {
  it('opens with Ctrl+K and runs a command', async () => {
    render(<App />)
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true })
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByText('Preset: Clean'))
    expect(useUi.getState().preset).toBe('clean')
    expect(useUi.getState().paletteOpen).toBe(false)
  })
  it('opens with Cmd+K', async () => {
    render(<App />)
    fireEvent.keyDown(window, { key: 'k', metaKey: true })
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
  })
  it('can hide a layer and switch the theme', async () => {
    render(<App />)
    useUi.getState().setPalette(true)
    await userEvent.click(await screen.findByText('Hide Previous day high'))
    expect(useUi.getState().hidden).toContain('pdh')
    useUi.getState().setPalette(true)
    await userEvent.click(await screen.findByText('Switch to light theme'))
    expect(useUi.getState().theme).toBe('light')
  })
  it('offers no instrument or timeframe commands while P3/P4 are Proposed', async () => {
    render(<App />)
    useUi.getState().setPalette(true)
    await screen.findByRole('dialog')
    expect(screen.queryByText(/timeframe|instrument/i)).toBeNull()
  })
})

describe('premarket workspace', () => {
  it('steps change which objects are drawn', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /2\. Key price levels/ }))
    expect(drawn()).toEqual(['pdh'])
    await userEvent.click(screen.getByRole('button', { name: /1\. Market context/ }))
    expect(drawn()).toEqual([])
  })
  it('hide and show toggles an object', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Hide Asia high' }))
    expect(drawn()).not.toContain('asiaH')
    await userEvent.click(screen.getByRole('button', { name: 'Show Asia high' }))
    expect(drawn()).toContain('asiaH')
  })
  it('timeline entries select their object', async () => {
    render(<App />)
    await userEvent.click(within(screen.getByRole('region', { name: 'Session timeline' })).getByText(/Asia range established/))
    expect(useUi.getState().selected).toBe('asiaH')
  })
  it('step 6 shows the printable plan and hides the chart', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /6\. Final session plan/ }))
    expect(screen.getByRole('region', { name: 'Final session plan' })).toBeInTheDocument()
    expect(screen.queryByTestId('chart')).toBeNull()
    expect(screen.getByRole('button', { name: 'Print plan' })).toBeInTheDocument()
    expect(screen.getByText(/not a trading signal/i)).toBeInTheDocument()
  })
})

describe('inspector', () => {
  it('has Insight, Evidence and Forecast tabs', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))))
    render(<QueryClientProvider client={new QueryClient()}><App /></QueryClientProvider>)
    expect(screen.getByRole('tab', { name: 'Insight', selected: true })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Evidence' }))
    expect(screen.getByText('Setup id')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Forecast' }))
    expect(screen.getByText(/No forecast exists yet/)).toBeInTheDocument()
    expect(screen.getByText('Not validated')).toBeInTheDocument()
  })
  it('arrow keys move between tabs', async () => {
    render(<App />)
    screen.getByRole('tab', { name: 'Insight' }).focus()
    await userEvent.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Evidence', selected: true })).toHaveFocus()
  })
})

describe('chart screen replay', () => {
  it('scrubbing hides objects not yet known and Live restores them', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Chart' }))
    await userEvent.click(screen.getByRole('button', { name: 'Everything' }))
    expect(drawn()).toHaveLength(objects.length)
    const asiaKnown = objects.find(o => o.id === 'asiaH')!.knownAt
    fireEvent.change(screen.getByLabelText('Replay'), { target: { value: String(asiaKnown) } })
    expect(drawn().sort()).toEqual(['asiaH', 'asiaL', 'pdh'])
    await userEvent.click(screen.getByRole('button', { name: 'Live' }))
    expect(drawn()).toHaveLength(objects.length)
  })
  it('execution preset caps what is drawn and says so in the list', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Chart' }))
    expect(drawn()).toHaveLength(4)
    expect(screen.getAllByText(/not drawn: preset/)).toHaveLength(2)
  })
  it('leaving the screen resets replay', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: 'Chart' }))
    useUi.getState().setReplay(objects[0].knownAt)
    await userEvent.click(within(screen.getByRole('navigation', { name: 'Screens' })).getByRole('button', { name: 'Premarket' }))
    expect(useUi.getState().replayT).toBeNull()
  })
})
