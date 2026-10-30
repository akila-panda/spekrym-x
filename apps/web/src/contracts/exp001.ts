import { z } from 'zod'

// Mirrors the stage JSON written by sx-lab exp001-validate / exp001-holdout, as passed through
// apps/api/src/sx_api/exp001.py (field whitelist). Checked by hand; unknown fields are dropped.
const Mcs = z.object({
  level: z.number(), reps: z.number(), block_size: z.number(), seed: z.number(),
  included: z.array(z.string()), excluded: z.array(z.string()), pvalues: z.record(z.string(), z.number().nullable())
})
const Conformal = z.object({
  nominal: z.number(), empirical: z.number(), n: z.number(), n_calibration: z.number(),
  worst_rolling_50: z.number().nullable(), mean_width_ratio: z.number(), caveat: z.string().optional()
})
export const Exp001Stage = z.object({
  stage: z.enum(['validation', 'holdout']), labels: z.string(), spec_hash: z.string(),
  data_version: z.string(), data_label: z.string(),
  n_validation: z.number().optional(), n_holdout: z.number().optional(),
  scores: z.record(z.string(), z.object({ qlike: z.number(), rmse: z.number() })),
  mcs: Mcs, outcome: z.enum(['win', 'tie', 'loss', 'inconclusive']),
  conformal: z.record(z.string(), Conformal), variants_tried: z.number(),
  per_seed_qlike_diagnostic: z.record(z.string(), z.number()).optional(),
  train_loss_by_epoch: z.record(z.string(), z.array(z.number())).optional(),
  reason: z.string().optional()
})
export type Exp001Stage = z.infer<typeof Exp001Stage>

export const Exp001 = z.object({
  status: z.enum(['not_run', 'validated', 'complete']),
  validation: Exp001Stage.nullable(), holdout: Exp001Stage.nullable(), report_present: z.boolean()
})
export type Exp001 = z.infer<typeof Exp001>
