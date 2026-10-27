// Pushes label centres apart so neighbours are at least `gap` px away, within [min, max].
// Input order is irrelevant; output is aligned to the input order.
export function decollide(ys: number[], gap: number, min: number, max: number): number[] {
  const idx = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y)
  const out = idx.map(o => Math.min(max, Math.max(min, o.y)))
  for (let k = 1; k < out.length; k++) if (out[k] - out[k - 1] < gap) out[k] = out[k - 1] + gap
  for (let k = out.length - 1; k >= 0; k--) {
    const limit = k === out.length - 1 ? max : out[k + 1] - gap
    if (out[k] > limit) out[k] = limit
  }
  const res: number[] = new Array(ys.length)
  idx.forEach((o, k) => { res[o.i] = out[k] })
  return res
}
