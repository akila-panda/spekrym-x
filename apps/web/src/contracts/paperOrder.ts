import { z } from 'zod'
import { iso } from './common'

export const PaperOrder = z.object({
  id: z.string(), suggestion_id: z.string(), backend: z.enum(['sim', 'oanda_practice', 'ib_paper']),
  side: z.enum(['long', 'short']), units: z.number(), entry: z.number(), stop: z.number(), target: z.number(),
  intended_fill: z.number(), actual_fill: z.number().optional(), slippage: z.number().optional(),
  state: z.enum(['pending', 'filled', 'closed', 'rejected', 'cancelled']),
  opened_at: iso.optional(), closed_at: iso.optional(), pnl: z.number().optional(), rules_version: z.string()
})
export type PaperOrder = z.infer<typeof PaperOrder>
