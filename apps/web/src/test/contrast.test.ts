import { describe, expect, it } from 'vitest'
import { ratio, readTokens } from './contrast'

// Light-theme tokens below 4.5:1 as text, measured against --bg. These are the documented tokens from
// docs/UI_DESIGN.md; changing a colour is an owner decision. The test pins the list so changes are noticed.
const LIGHT_BELOW_AA = ['accent', 'asia', 'bull', 'london', 'warn']
const TEXT = ['text', 'muted', 'accent', 'bull', 'bear', 'asia', 'london', 'ny', 'warn']

describe('token contrast', () => {
  it('dark theme: every text token meets 4.5:1 on bg and surface', () => {
    const t = readTokens('dark')
    for (const k of TEXT) { expect(ratio(t[k], t.bg), k).toBeGreaterThanOrEqual(4.5); expect(ratio(t[k], t.surface), k).toBeGreaterThanOrEqual(4.5) }
  })
  it('light theme: primary and muted text meet 4.5:1', () => {
    const t = readTokens('light')
    for (const k of ['text', 'muted', 'bear', 'ny']) expect(ratio(t[k], t.bg), k).toBeGreaterThanOrEqual(4.5)
  })
  it('light theme: known sub-AA tokens are exactly the documented list and all keep 3:1', () => {
    const t = readTokens('light')
    const below = TEXT.filter(k => ratio(t[k], t.bg) < 4.5).sort()
    expect(below).toEqual(LIGHT_BELOW_AA)
    for (const k of below) expect(ratio(t[k], t.bg), k).toBeGreaterThanOrEqual(3)
  })
})
