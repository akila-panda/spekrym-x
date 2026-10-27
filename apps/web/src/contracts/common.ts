import { z } from 'zod'

export const iso = z.iso.datetime()
export const Tf = z.enum(['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D'])
export const Direction = z.enum(['bullish', 'bearish', 'neutral'])
// Honesty labels from docs/CONTRACTS.md. Records carry the subset their contract allows.
export const StatusLabel = z.enum(['sample', 'exploratory', 'not_validated', 'retrospective', 'causal'])
export type StatusLabel = z.infer<typeof StatusLabel>
