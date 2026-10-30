import { useQuery } from '@tanstack/react-query'
import { API_URL } from '../api'
import { SuggestionsPayload } from '../contracts/suggestions'

export async function fetchSuggestions(signal?: AbortSignal, base: string = API_URL, instrument = 'EUR_USD'): Promise<SuggestionsPayload> {
  const res = await fetch(`${base}/suggestions?instrument=${encodeURIComponent(instrument)}`, { signal })
  if (!res.ok) throw new Error(`API answered ${res.status} for /suggestions`)
  return SuggestionsPayload.parse(await res.json())   // a bad payload throws, nothing half-valid is shown
}

export const useSuggestions = () =>
  useQuery({ queryKey: ['suggestions'], queryFn: ({ signal }) => fetchSuggestions(signal), retry: false, staleTime: 60_000 })
