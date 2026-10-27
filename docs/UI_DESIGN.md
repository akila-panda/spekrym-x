# UI Design

Goal: a modern, SaaS-quality desk that feels calm, dense where it should be, and honest. Warm Claude Code character, dark and light themes.

## Principles
1. Show less, explain every item. Rank by relevance, cap what is drawn, hide the rest behind layers.
2. Every object explains itself: what it is, why it was drawn, when it became knowable, what invalidates it.
3. Honesty is visible: status badges are always on screen, never in a tooltip only.
4. Colour never carries meaning alone. Pair with shape, label or pattern.
5. Keyboard first: everything reachable, Cmd+K for anything.

## Tokens

### Dark (default)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#1A1918` | App background |
| `--surface` | `#232120` | Cards, panels |
| `--surface-2` | `#2B2927` | Raised, hover |
| `--border` | `#3A3734` | Dividers |
| `--text` | `#ECE8E1` | Primary text |
| `--text-muted` | `#A39D93` | Secondary text |
| `--accent` | `#D97757` | Brand, actions, focus, selection |

### Light
| Token | Value |
|---|---|
| `--bg` | `#FAF9F5` |
| `--surface` | `#FFFFFF` |
| `--surface-2` | `#F2EFE7` |
| `--border` | `#E4DFD3` |
| `--text` | `#1F1E1D` |
| `--text-muted` | `#6B665D` |
| `--accent` | `#C15F3C` |

### Semantic colours (separate from the accent)
Terracotta means "action / selected", never bullish or bearish.

| Meaning | Dark | Light |
|---|---|---|
| Bullish | `#5BB98C` | `#2E8B64` |
| Bearish | `#E0685E` | `#C2453B` |
| Asia session | `#5FA8B8` | `#3B8394` |
| London session | `#D4A94F` | `#A9812A` |
| New York session | `#9B8AE0` | `#6F5CC4` |
| Warning | `#E3B341` | `#B7881B` |

### Type
- UI: Inter (fallback system sans).
- Numbers, prices, times, ids: JetBrains Mono, tabular figures.
- Written brief: a serif (Source Serif 4) for long-form reading.
- Scale: 12 / 13 / 14 / 16 / 20 / 28. Spacing on a 4px grid. Radius 8 for cards, 6 for controls.

## App shell
- **Left rail** (56px): Premarket, Chart, Suggestions, Paper, Lab, Journal, and Settings at the bottom.
- **Top bar**: instrument selector, timeframe switch, session clock (Asia / London / NY with the active one marked), data-health indicator, theme toggle, Cmd+K hint.
- **Status line** (bottom, terminal-style): mode (`PAPER`), data status, last update, selected object id.
- **Command palette** (Cmd+K): navigate, switch instrument and timeframe, toggle layers and theme.

## Screens

### Premarket (home)
- Left: 6-step workflow stepper with progress: Market context, Key levels, Session liquidity, Structure and momentum, Scenarios and risk, Session plan.
- Centre: chart that changes with the step (the step decides which layers show).
- Right inspector with tabs: Insight, Evidence, Forecast.
- Below the chart: a timeline of what happened this session.
- Session objects list with eye toggles. Clicking an item highlights its geometry, zooms to it, and opens its evidence.
- Final step: a one-page session plan, exportable.

### Chart
- Large Lightweight Charts view (about 70% of width), session bands, level lines, zone boxes, event markers.
- Layer presets: Premarket, Execution, Clean, Everything.
- Relevance ranking: only the top items near price are drawn by default.
- Right inspector as above. Replay scrubber for causal replay.

### Suggestions, Paper, Lab, Journal
Placeholder screens at first, each with an honest empty state and a sample-data badge.

## Components
Button, IconButton, Badge (status), Card, Tabs, Stepper, Toggle, Tooltip, Kbd, Command palette, Inspector panel, Timeline, Empty state, Skeleton.

## Object styling
- Level: line. Session high/low dashed in the session colour.
- Zone: box. Fresh is solid tint, tested is lighter, mitigated fades to outline, broken is removed.
- Event: small marker with a label.
- Selected: accent outline plus inspector open.
- Retrospective items use a hatched pattern and a **Retrospective** badge.

## Stack
Vite, React, TypeScript, Tailwind, Radix UI primitives, cmdk, Zustand (UI state), TanStack Query (API data), Zod (contract validation), Lightweight Charts, Vitest, Playwright.

## Accessibility and quality
Keyboard reachable, visible focus ring in the accent, accessible names, contrast checked in both themes, responsive down to a 13-inch laptop, loading and empty states for every panel.
