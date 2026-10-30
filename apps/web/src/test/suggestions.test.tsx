import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import payload from './fixtures/suggestions_payload.json'
import empty from './fixtures/suggestions_empty.json'
import { SuggestionsPayload } from '../contracts/suggestions'
import { SuggestionsScreen } from '../screens/SuggestionsScreen'

const serve = (body: unknown, ok = true) =>
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok, status: ok ? 200 : 500, json: async () => body })))
const show = () => render(<QueryClientProvider client={new QueryClient()}><SuggestionsScreen /></QueryClientProvider>)
afterEach(() => vi.unstubAllGlobals())

describe('suggestions contract', () => {
  it('parses a valid payload', () => expect(SuggestionsPayload.parse(payload).items).toHaveLength(2))
  it('rejects a claim whose evidence id is not one of its suggestion ids', () => {
    const bad = structuredClone(payload)
    bad.items[0].suggestion.reasons[1].evidence_id = 'setup:t2'
    expect(SuggestionsPayload.safeParse(bad).success).toBe(false)
  })
  it('rejects a suggestion whose setup is missing from the evidence list', () => {
    expect(SuggestionsPayload.safeParse({ ...payload, evidence: [payload.evidence[1]] }).success).toBe(false)
  })
  it('rejects a status other than not_validated', () => {
    const bad = structuredClone(payload) as { items: { suggestion: { status: string } }[] }
    bad.items[0].suggestion.status = 'validated'
    expect(SuggestionsPayload.safeParse(bad).success).toBe(false)
  })
})

describe('Suggestions screen', () => {
  it('shows labels, the 9A reading, a rank that is not a probability, gates and the source label', async () => {
    serve(payload); const { container } = show()
    await screen.findByRole('article', { name: /Suggestion long/ })
    for (const l of ['Exploratory', 'Not validated', 'Retrospective']) expect(screen.getAllByText(l).length).toBeGreaterThan(0)
    expect(screen.getByText('TEST FIXTURE - NOT REAL SUGGESTIONS')).toBeInTheDocument()
    expect(screen.getByText(/NOT above the shuffled-label range/)).toBeInTheDocument()
    expect(screen.getAllByText(/a ranking, not a probability/).length).toBe(2)
    expect(within(screen.getAllByRole('list', { name: 'Risk gates' })[0]).getByText(/news_blackout: clear/)).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/%|chance|likel|win rate/i)
    expect(container.textContent?.replace(/not a probability/g, '')).not.toMatch(/probabilit/i)
  })
  it('clicking a reason highlights the linked setup on the chart and in the evidence panel', async () => {
    serve(payload); show()
    await screen.findByRole('article', { name: /Suggestion long/ })
    expect(within(screen.getByRole('complementary', { name: 'Linked evidence' })).getByText(/Test fvg/)).toBeInTheDocument()
    const second = within(screen.getByRole('article', { name: /Suggestion short/ }))
    await userEvent.click(second.getByRole('button', { name: /Test order_block zone/ }))
    expect(within(screen.getByRole('complementary', { name: 'Linked evidence' })).getByText(/Test order_block/)).toBeInTheDocument()
    expect(screen.getByTestId('evidence-box')).toBeInTheDocument()
  })
  it('shows an honest empty state when there is no 9A result', async () => {
    serve(empty); show()
    expect(await screen.findByText(/No 9A validation result exists yet/)).toBeInTheDocument()
    expect(screen.getByText(/run the 9A validation first/)).toBeInTheDocument()
    expect(screen.queryByRole('article')).toBeNull()
  })
  it('shows an error and nothing in its place when the API fails', async () => {
    serve({}, false); show()
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Nothing is shown in their place/))
  })
})

describe('evidence chart (9B polish)', () => {
  it('keeps Entry, Stop and Target labels apart even when the prices are almost equal', async () => {
    const { EvidenceChart } = await import('../components/suggestions/EvidenceChart')
    const candles = Array.from({ length: 6 }, (_, i) => ({ time: `2026-10-26T0${i}:00:00Z`, open: 1.08, high: 1.081, low: 1.079, close: 1.08 }))
    const { container } = render(<EvidenceChart candles={candles} setup={null} levels={{ entry: 1.07967, stop: 1.07914, target: 1.07975 }} />)
    const ys = Array.from(container.querySelectorAll('text')).map(t => Number(t.getAttribute('y'))).sort((a, b) => a - b)
    expect(ys).toHaveLength(3)
    expect(ys[1] - ys[0]).toBeGreaterThanOrEqual(13)
    expect(ys[2] - ys[1]).toBeGreaterThanOrEqual(13)
  })
  it('gives a weekend gap one bar of width, not a long flat stretch', async () => {
    const { EvidenceChart } = await import('../components/suggestions/EvidenceChart')
    const times = ['2026-10-23T20:00:00Z', '2026-10-23T21:00:00Z', '2026-10-26T00:00:00Z', '2026-10-26T01:00:00Z']
    const candles = times.map(time => ({ time, open: 1.08, high: 1.081, low: 1.079, close: 1.08 }))
    const { container } = render(<EvidenceChart candles={candles} setup={null} levels={null} />)
    const xs = (container.querySelector('path')!.getAttribute('d')!.match(/[ML]([\d.]+),/g) ?? []).map(m => Number(m.slice(1, -1)))
    const steps = xs.slice(1).map((v, i) => v - xs[i])
    expect(Math.max(...steps) - Math.min(...steps)).toBeLessThan(0.5)
  })
})
