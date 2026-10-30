import { z } from 'zod'

// Mirrors apps/api/src/sx_api/datasets.py (list rows) and jobs.py (job view). Checked by hand.
export const DatasetRow = z.object({
  file: z.string(), size_bytes: z.number(),
  integrity: z.enum(['ok', 'no_provenance', 'modified', 'unreadable']),
  problem: z.string().optional(),
  instrument: z.string().nullish(), tf: z.string().nullish(), n_bars: z.number().nullish(),
  first_bar: z.string().nullish(), last_bar: z.string().nullish(), label: z.string().nullish(),
  data_version: z.string().nullish(), feed_degraded: z.boolean().nullish(),
  expected_gaps: z.number().nullish(), unexpected_gaps: z.number().nullish(),
  flat_bars: z.number().nullish(), source: z.string().nullish(), verified: z.boolean().nullish(),
  in_use: z.array(z.string()).optional()
})
export type DatasetRow = z.infer<typeof DatasetRow>

export const TrashRow = z.object({ id: z.string(), file: z.string(), size_bytes: z.number(), deleted_at: z.string() })
export type TrashRow = z.infer<typeof TrashRow>

export const DatasetList = z.object({
  folder: z.string(), items: z.array(DatasetRow), trash: z.array(TrashRow).default([]), token_configured: z.boolean(),
  options: z.object({ instruments: z.array(z.string()), timeframes: z.array(z.string()), max_bars: z.number() })
})
export type DatasetList = z.infer<typeof DatasetList>

export const ImportJob = z.object({
  id: z.string(), state: z.enum(['running', 'done', 'refused', 'failed']), message: z.string(),
  elapsed_s: z.number(), request: z.record(z.string(), z.unknown()),
  result: DatasetRow.partial().nullable()
})
export type ImportJob = z.infer<typeof ImportJob>
