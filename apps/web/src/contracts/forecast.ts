import { z } from 'zod'
import { Tf, iso } from './common'

export const Forecast = z.object({
  id: z.string(), instrument: z.string(), tf: Tf, issued_at: iso, horizon_end: iso,
  target: z.enum(['realized_vol', 'range']), point: z.number(),
  interval: z.object({ low: z.number(), high: z.number(), nominal_coverage: z.number().gt(0).lt(1) }),
  regime: z.enum(['quiet', 'normal', 'expanding', 'extreme']).optional(),
  model: z.object({ name: z.string(), version: z.string(), params_hash: z.string() }),
  baseline_comparison: z.object({ baseline: z.string(), metric: z.string(), delta: z.number() }).optional(),
  track_record: z.object({ n: z.number().int().nonnegative(), empirical_coverage: z.number(), variants_tried: z.number().int().nonnegative() }),
  status: z.enum(['exploratory', 'not_validated'])
}).refine(f => f.interval.low <= f.point && f.point <= f.interval.high, 'point outside interval')
export type Forecast = z.infer<typeof Forecast>
