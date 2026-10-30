import type { Exp001, Exp001Stage } from '../contracts/exp001'

export const MAX_VARIANTS = 20 // from the locked spec (max_variants); shown next to the count tried

export const OUTCOME_TEXT: Record<Exp001Stage['outcome'], string> = {
  win: 'MiniMamba is in the confidence set and HAR and GARCH are both out.',
  tie: 'MiniMamba is in the confidence set together with HAR and/or GARCH, so the data cannot separate them.',
  loss: 'MiniMamba is out of the confidence set while HAR or GARCH is in.',
  inconclusive: 'The result matches none of the win, tie or loss rules.'
}

export const q = (v: number) => v.toFixed(5)
export const r = (v: number) => v.toExponential(3)
export const cov = (v: number) => v.toFixed(3)
export const nRows = (s: Exp001Stage) => s.n_holdout ?? s.n_validation ?? 0

/** Stages in display order: the holdout headline first (L22), the validation always beside it. */
export function stagesOf(d: Exp001): Exp001Stage[] {
  return [d.holdout, d.validation].filter((s): s is Exp001Stage => s !== null)
}

/** Last-epoch training loss per seed next to that seed's validation QLIKE: a plain fact, no verdict. */
export function trainVsValidation(v: Exp001Stage): { seed: string; train: number; validation: number }[] {
  const out: { seed: string; train: number; validation: number }[] = []
  for (const [seed, losses] of Object.entries(v.train_loss_by_epoch ?? {})) {
    const val = v.per_seed_qlike_diagnostic?.[seed]
    const train = losses[losses.length - 1]
    if (val !== undefined && train !== undefined) out.push({ seed, train, validation: val })
  }
  return out
}
