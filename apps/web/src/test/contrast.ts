import { readFileSync } from 'node:fs'

export type Tokens = Record<string, string>
const hexToRgb = (h: string) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255)
const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const lum = (h: string) => { const [r, g, b] = hexToRgb(h).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
export const ratio = (a: string, b: string) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05) }

// Reads the CSS custom properties from index.css for one theme block.
export function readTokens(theme: 'dark' | 'light'): Tokens {
  const css = readFileSync('src/index.css', 'utf8')
  const block = (theme === 'dark' ? /:root, \[data-theme='dark'\] \{([^}]*)\}/ : /\[data-theme='light'\] \{([^}]*)\}/).exec(css)![1]
  const out: Tokens = {}
  for (const m of block.matchAll(/--([\w-]+):\s*(#[0-9A-Fa-f]{6})/g)) out[m[1]] = m[2]
  return out
}
