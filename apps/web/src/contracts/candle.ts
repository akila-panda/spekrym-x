import { z } from 'zod'
import { Tf, iso } from './common'

export const Candle = z.object({
  instrument: z.string(), tf: Tf, time: iso,
  open: z.number(), high: z.number(), low: z.number(), close: z.number(), volume: z.number(),
  bid_close: z.number().optional(), ask_close: z.number().optional(), complete: z.boolean()
}).refine(c => c.high >= Math.max(c.open, c.close) && c.low <= Math.min(c.open, c.close), 'OHLC out of order')
export type Candle = z.infer<typeof Candle>
