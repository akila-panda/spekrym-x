import { z } from 'zod'
import { Setup } from './setup'
import { Suggestion } from './suggestion'
import { Tf, iso } from './common'

// GET /suggestions envelope (Phase 9B). `score` inside each Suggestion is a rank, never a probability.
const Metrics = z.object({
  n: z.number(), auc: z.number(), auc_ci95_iid: z.tuple([z.number(), z.number()]),
  target_first_share_all: z.number(), top_fifth_n: z.number(), top_fifth_target_first_share: z.number()
})
const Validation = z.object({
  stage: z.string(), spec_hash: z.string().optional(), data_version: z.string().optional(),
  model_sha256: z.string(), variants_tried: z.number().optional(), metrics: Metrics,
  shuffled_auc_p95: z.number().nullable().optional(), controls_behaved: z.boolean().optional()
})
const Holdout = z.object({ stage: z.string(), metrics: Metrics, verdict: z.string().optional() })

export const SuggestionsPayload = z.object({
  status: z.enum(['ok', 'no_result', 'model_unavailable']),
  instrument: z.string(), tf: Tf, as_of: iso,
  source: z.object({ id: z.string(), name: z.string(), label: z.string(), live: z.boolean() }),
  labels: z.array(z.string()),
  scorer: z.object({ stage: z.enum(['none', 'validated', 'complete']), reading: z.string(),
    validation: Validation.nullable(), holdout: Holdout.nullable() }),
  items: z.array(z.object({ suggestion: Suggestion, labels: z.array(z.string()),
    model_version: z.string(), note: z.string() })),
  evidence: z.array(Setup),
  candles: z.array(z.object({ time: iso, open: z.number(), high: z.number(), low: z.number(), close: z.number() })),
  rejected: z.array(z.object({ setup_id: z.string(), why: z.string() })),
  note: z.string()
}).refine(p => p.items.every(i => i.suggestion.reasons.every(r =>
  i.suggestion.setup_ids.includes(r.evidence_id) || r.evidence_id === i.suggestion.forecast_id)),
  'a claim points at an id that is not one of its suggestion\'s evidence ids')
  .refine(p => p.items.every(i => i.suggestion.setup_ids.every(id => p.evidence.some(e => e.id === id))),
    'a suggestion points at a setup that is not in the evidence list')
export type SuggestionsPayload = z.infer<typeof SuggestionsPayload>
