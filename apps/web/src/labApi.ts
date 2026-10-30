import { API_URL } from './api'
import { DatasetList, ImportJob } from './contracts/datasets'
import { Exp001 } from './contracts/exp001'
import { describeApiError, type Range } from './lab/importForm'

async function json(res: Response): Promise<unknown> {
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new Error(describeApiError(res.status, body))
  return body
}

export async function fetchDatasets(signal?: AbortSignal, base: string = API_URL): Promise<DatasetList> {
  return DatasetList.parse(await json(await fetch(`${base}/lab/datasets`, { signal })))
}

export async function startImport(p: { instrument: string; tf: string } & Range, base: string = API_URL): Promise<ImportJob> {
  const res = await fetch(`${base}/lab/datasets/oanda`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p)
  })
  return ImportJob.parse(await json(res))
}

export async function fetchJob(id: string, signal?: AbortSignal, base: string = API_URL): Promise<ImportJob> {
  return ImportJob.parse(await json(await fetch(`${base}/lab/datasets/jobs/${encodeURIComponent(id)}`, { signal })))
}

export async function fetchExp001(signal?: AbortSignal, base: string = API_URL): Promise<Exp001> {
  return Exp001.parse(await json(await fetch(`${base}/lab/exp001`, { signal })))
}

// Delete moves the file to the data folder's .trash (the API refuses files a locked experiment or saved model uses).
const act = async (method: string, path: string, base: string) => { await json(await fetch(`${base}/lab/datasets/${path}`, { method })) }
export const deleteDataset = (file: string, base: string = API_URL) => act('DELETE', encodeURIComponent(file), base)
export const restoreDataset = (id: string, base: string = API_URL) => act('POST', `trash/${encodeURIComponent(id)}/restore`, base)
export const purgeDataset = (id: string, base: string = API_URL) => act('DELETE', `trash/${encodeURIComponent(id)}`, base)
