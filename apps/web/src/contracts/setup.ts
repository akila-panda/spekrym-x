import { z } from 'zod'
import { Direction, Tf, iso } from './common'

export const SetupKind = z.enum(['swing', 'bos', 'choch', 'fvg', 'order_block', 'liquidity_sweep',
  'session_level', 'support_resistance', 'candle_pattern'])
export const Setup = z.object({
  id: z.string().min(1), kind: SetupKind, instrument: z.string(), tf: Tf, direction: Direction,
  geometry: z.object({ price_low: z.number(), price_high: z.number(), t_start: iso, t_end: iso.optional() }),
  event_time: iso, known_at: iso,
  lifecycle: z.enum(['fresh', 'tested', 'mitigated', 'broken']),
  source: z.object({ library: z.string(), version: z.string(), adapter: z.string() }),
  plain_text: z.string(), invalidation: z.string(),
  status: z.enum(['causal', 'retrospective'])
}).refine(s => s.geometry.price_low <= s.geometry.price_high, 'price_low above price_high')
  .refine(s => Date.parse(s.known_at) >= Date.parse(s.event_time), 'known_at before event_time')
export type Setup = z.infer<typeof Setup>
