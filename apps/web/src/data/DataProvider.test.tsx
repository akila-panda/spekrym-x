import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import raw from '../test/fixtures/premarket_payload.json'
import { DataProvider, useData } from './DataProvider'

function Probe() {
  const { status, dataset, error } = useData()
  return <div data-testid="p">{status}|{dataset.label}|{dataset.origin}|{error ?? ''}</div>
}
const mount = () => render(
  <QueryClientProvider client={new QueryClient()}><DataProvider><Probe /></DataProvider></QueryClientProvider>)

afterEach(() => vi.unstubAllGlobals())

describe('DataProvider', () => {
  it('without a provider the labelled offline sample is used', () => {
    render(<Probe />)
    expect(screen.getByTestId('p').textContent).toContain('offline|Sample data (offline copy')
  })
  it('loads the API payload and keeps its SAMPLE label', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify(raw), { status: 200 })))
    mount()
    await waitFor(() => expect(screen.getByTestId('p').textContent).toContain('api|SAMPLE DATA — NOT LIVE|api'))
  })
  it('falls back to the labelled offline sample when the API is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('connection refused') }))
    mount()
    await waitFor(() => expect(screen.getByTestId('p').textContent).toContain('error|Sample data (offline copy'))
    expect(screen.getByTestId('p').textContent).toContain('connection refused')
  })
  it('treats a non-200 answer and an invalid payload as errors, never as data', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{}', { status: 500 })))
    mount()
    await waitFor(() => expect(screen.getByTestId('p').textContent).toContain('error|'))
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ schema_version: 1 }), { status: 200 })))
    mount()
    await waitFor(() => expect(screen.getAllByTestId('p').some(e => e.textContent!.startsWith('error|'))).toBe(true))
  })
})
