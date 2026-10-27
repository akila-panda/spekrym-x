export type Rankable = { id: string; price: number }

// Nearest to the reference price first. Ties keep input order, so the result is deterministic.
export function rankByProximity<T extends Rankable>(items: T[], refPrice: number): T[] {
  return items
    .map((o, i) => ({ o, i, d: Math.abs(o.price - refPrice) }))
    .sort((a, b) => a.d - b.d || a.i - b.i)
    .map(x => x.o)
}
