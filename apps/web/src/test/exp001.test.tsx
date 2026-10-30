import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import payload from './fixtures/exp001_payload.json'
import { Exp001 } from '../contracts/exp001'
import { Exp001Panel } from '../components/lab/Exp001Panel'
import { LabScreen } from '../screens/LabScreen'
import { trainVsValidation } from '../lab/exp001Format'

const data = Exp001.parse(payload)

describe('EXP-001 contract', () => {
  it('parses the API payload and rejects an unknown outcome', () => {
    expect(data.holdout?.outcome).toBe('tie')
    expect(Exp001.safeParse({ ...payload, validation: { ...payload.validation, outcome: 'victory' } }).success).toBe(false)
  })
  it('pairs last-epoch training loss with validation QLIKE per seed', () => {
    const rows = trainVsValidation(data.validation!)
    expect(rows).toHaveLength(3)
    expect(rows[0]).toEqual({ seed: 'seed1', train: 0.1, validation: 0.3 })
  })
})

describe('EXP-001 panel', () => {
  it('shows holdout and validation outcomes side by side, with labels and variants', () => {
    render(<Exp001Panel data={data} />)
    const summary = screen.getByRole('region', { name: 'Experiment summary' })
    expect(within(summary).getByText('TIE')).toBeInTheDocument()
    expect(within(summary).getByText('LOSS')).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Holdout (opened once) result' })).getByText('Headline (L22)')).toBeInTheDocument()
    expect(screen.getByRole('article', { name: 'Validation result' })).toBeInTheDocument()
    for (const l of ['Exploratory', 'Not validated', 'Retrospective']) expect(screen.getByText(l)).toBeInTheDocument()
    expect(screen.getByText(/Variants tried: 3 of 20/)).toBeInTheDocument()
    expect(screen.getByText('TEST FIXTURE - NOT EXP-001 RESULTS')).toBeInTheDocument()
  })
  it('marks MCS membership per model in the validation table', () => {
    render(<Exp001Panel data={data} />)
    const v = within(screen.getByRole('article', { name: 'Validation result' }))
    expect(within(v.getByRole('row', { name: /HAR/ })).getByText('Yes')).toBeInTheDocument()
    expect(within(v.getByRole('row', { name: /MiniMamba/ })).getByText('No')).toBeInTheDocument()
  })
  it('never shows a percentage or probability wording', () => {
    const { container } = render(<Exp001Panel data={data} />)
    expect(container.textContent).not.toMatch(/%|probabilit/i)
  })
  it('says so plainly when nothing has been run', () => {
    render(<Exp001Panel data={{ status: 'not_run', validation: null, holdout: null, report_present: false }} />)
    expect(screen.getByText(/has not been run yet/)).toBeInTheDocument()
  })
})

describe('Lab screen EXP-001 tab', () => {
  it('loads from the API and renders the result', async () => {
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(new Response(
      JSON.stringify(url.endsWith('/lab/exp001') ? payload : { detail: 'x' }), { status: 200 }))))
    render(<QueryClientProvider client={new QueryClient()}><LabScreen /></QueryClientProvider>)
    await userEvent.click(screen.getByRole('tab', { name: 'EXP-001' }))
    await waitFor(() => expect(screen.getByRole('region', { name: 'Experiment summary' })).toBeInTheDocument())
  })
  it('shows an error and no numbers when the API is down', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('offline'))))
    render(<QueryClientProvider client={new QueryClient()}><LabScreen /></QueryClientProvider>)
    await userEvent.click(screen.getByRole('tab', { name: 'EXP-001' }))
    await waitFor(() => expect(screen.getByText(/could not be loaded/)).toBeInTheDocument())
    expect(screen.queryByText(/QLIKE/)).toBeNull()
  })
})
