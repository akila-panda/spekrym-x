import { toDataset } from './data/fromApi'
import type { Dataset } from './data/dataset'

// VITE_DATA_SOURCE=sample forces the built-in offline sample (no network). Default: ask the API.
export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
export const FORCE_SAMPLE: boolean = import.meta.env.VITE_DATA_SOURCE === 'sample'

export async function fetchPremarket(signal?: AbortSignal, base: string = API_URL, instrument = 'EUR_USD'): Promise<Dataset> {
  const res = await fetch(`${base}/premarket?instrument=${encodeURIComponent(instrument)}`, { signal })
  if (!res.ok) throw new Error(`API answered ${res.status} for /premarket`)
  return toDataset(await res.json())   // zod validation happens here; a bad payload throws
}
