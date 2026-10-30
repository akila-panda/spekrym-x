import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'
import { DatasetTable } from '../components/lab/DatasetTable'
import type { DatasetRow } from '../contracts/datasets'

// jsdom has no canvas; the chart is covered elsewhere (same mock as app.test.tsx).
vi.mock('../components/Chart', () => ({ Chart: () => <div data-testid="chart" /> }))

const wrap = (ui: React.ReactElement) =>
  <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>

describe('X17: premarket sample labels on the Lab screen', () => {
  it('shows them on the premarket screen and hides them on the Lab screen', async () => {
    render(wrap(<App />))
    expect(screen.getAllByText('Sample data').length).toBeGreaterThan(0)
    expect(screen.getByText(/last \d\.\d{5}/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Lab' }))
    expect(screen.queryByText('Sample data')).toBeNull()
    expect(screen.queryByText(/SAMPLE DATA/)).toBeNull()
    expect(screen.queryByText(/last \d\.\d{5}/)).toBeNull()
    expect(screen.getByText(/each panel shows the provenance/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Premarket' }))
    expect(screen.getAllByText('Sample data').length).toBeGreaterThan(0)
  })
  it('the Data tab shows each dataset its own label, and says so when there is none', () => {
    const base = { file: 'a.parquet', size_bytes: 10, integrity: 'ok' as const }
    const rows: DatasetRow[] = [
      { ...base, label: 'OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED' },
      { ...base, file: 'b.parquet', label: 'SYNTHETIC TEST DATA' }, { ...base, file: 'c.parquet' }]
    render(<DatasetTable rows={rows} folder="lab/outputs/data" onDelete={async () => {}} />)
    expect(screen.getByText('OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED')).toBeInTheDocument()
    expect(screen.getByText('SYNTHETIC TEST DATA')).toBeInTheDocument()
    expect(screen.getByText('No label recorded')).toBeInTheDocument()
  })
})
