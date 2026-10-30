export const price = (x: number) => x.toFixed(5)
export const num3 = (x: number) => x.toFixed(3)
export const rankText = (score: number, shown = true) => shown
  ? `Rank ${Math.round(score)} of 100 (a ranking, not a probability)`
  : `Position ${Math.round(score)} of 100 in the validation scores. 9A found no ranking skill, so this is not evidence of quality (a ranking, not a probability)`
// Skill counts as shown only when the holdout was opened AND both periods beat the shuffled range (run.py verdict).
export const rankDemonstrated = (sc: { stage: string; reading: string }) =>
  sc.stage === 'complete' && sc.reading.startsWith('Both periods rank above')
export const when = (iso: string) => iso.replace('T', ' ').replace(/:\d\dZ$/, ' UTC')
