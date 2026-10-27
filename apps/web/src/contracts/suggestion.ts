import { z } from 'zod'
import { Tf, iso } from './common'

// `score` is a heuristic ranking, never a probability.
export const Suggestion = z.object({
  id: z.string(), instrument: z.string(), tf: Tf, created_at: iso,
  setup_ids: z.array(z.string()), forecast_id: z.string().optional(),
  side: z.enum(['long', 'short']), entry: z.number(), stop: z.number(), target: z.number(),
  score: z.number(),
  reasons: z.array(z.object({ text: z.string(), evidence_id: z.string().min(1) })),
  gates: z.array(z.object({ name: z.string(), passed: z.boolean(), detail: z.string() })),
  rules_version: z.string(), status: z.literal('not_validated')
})
export type Suggestion = z.infer<typeof Suggestion>
