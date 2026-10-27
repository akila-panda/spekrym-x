import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { API_URL, FORCE_SAMPLE, fetchPremarket } from '../api'
import { sampleDataset, type Dataset } from './dataset'

export type DataStatus = 'api' | 'loading' | 'error' | 'offline'
export type DataState = { dataset: Dataset; status: DataStatus; error?: string }

// No provider (unit tests, or a forced offline run) means the labelled offline sample.
const Ctx = createContext<DataState>({ dataset: sampleDataset, status: 'offline' })
export const useData = () => useContext(Ctx)
export const useDataset = () => useContext(Ctx).dataset

export function DataProvider({ children }: { children: ReactNode }) {
  const q = useQuery({ queryKey: ['premarket', 'EUR_USD'], queryFn: ({ signal }) => fetchPremarket(signal),
    enabled: !FORCE_SAMPLE, retry: false, staleTime: 60_000 })
  const value = useMemo<DataState>(() => {
    if (FORCE_SAMPLE) return { dataset: sampleDataset, status: 'offline' }
    if (q.data) return { dataset: q.data, status: 'api' }
    if (q.isError) return { dataset: sampleDataset, status: 'error', error: q.error instanceof Error ? q.error.message : String(q.error) }
    return { dataset: sampleDataset, status: 'loading' }
  }, [q.data, q.isError, q.error])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export const apiHint = API_URL
