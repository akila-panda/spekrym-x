import { describe, expect, it } from 'vitest'
import { rankDemonstrated, rankText } from './format'

describe('rank wording (S7)', () => {
  it('treats a null or unconfirmed 9A result as no demonstrated skill', () => {
    expect(rankDemonstrated({ stage: 'complete', reading: 'NULL: neither period ranks above the shuffled-label range.' })).toBe(false)
    expect(rankDemonstrated({ stage: 'validated', reading: 'Validation only: AUC is above the shuffled-label range.' })).toBe(false)
    expect(rankDemonstrated({ stage: 'none', reading: 'No 9A validation result exists yet.' })).toBe(false)
    expect(rankDemonstrated({ stage: 'complete', reading: 'Both periods rank above the shuffled-label range (Exploratory only).' })).toBe(true)
  })
  it('mutes the rank when skill is not shown, and never says probability-like words', () => {
    const muted = rankText(83, false)
    expect(muted).toMatch(/no ranking skill/)
    expect(muted).toMatch(/not a probability/)
    expect(muted).not.toMatch(/%|chance|likel|win rate/i)
    expect(rankText(83, true)).toMatch(/^Rank 83 of 100/)
  })
})
