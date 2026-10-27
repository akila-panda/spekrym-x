import { z } from 'zod'
import { iso } from './common'

export const LedgerEntry = z.object({
  ts: iso, kind: z.string(), payload: z.record(z.string(), z.unknown()),
  data_version: z.string(), rules_version: z.string().optional(), hash: z.string()
})
export type LedgerEntry = z.infer<typeof LedgerEntry>
