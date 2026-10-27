import { z } from 'zod'
import { Candle } from './candle'
import { Setup } from './setup'
import { iso } from './common'

// Mirrors the API payload of GET /premarket (docs/CONTRACTS.md, "Premarket payload").
export const ChecklistItem = z.object({ id: z.string(), tf: z.string(), text: z.string(), known_at: iso })
export const SessionBand = z.object({ id: z.string(), name: z.string(), t_start: iso, t_end: iso, complete: z.boolean() })
export const PremarketPayload = z.object({
  schema_version: z.literal(1),
  instrument: z.string(), tf: z.string(), as_of: iso, bar_seconds: z.number().int().positive(),
  source: z.object({ id: z.string(), name: z.string(), label: z.string().min(1), live: z.boolean() }),
  status_labels: z.array(z.string()).min(1), data_version: z.string(), disclaimer: z.string(),
  candles: z.array(Candle).min(1), setups: z.array(Setup), session_bands: z.array(SessionBand),
  checklist: z.array(ChecklistItem),
  timeline: z.array(z.object({ time: iso, setup_id: z.string(), text: z.string() }))
}).refine(p => p.setups.every(s => Date.parse(s.known_at) <= Date.parse(p.as_of)), 'a setup is known after as_of')
  .refine(p => p.checklist.every(c => Date.parse(c.known_at) <= Date.parse(p.as_of)), 'a checklist item is known after as_of')
export type PremarketPayload = z.infer<typeof PremarketPayload>
