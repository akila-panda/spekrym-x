export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)', surface: 'var(--surface)', surface2: 'var(--surface-2)',
        line: 'var(--border)', ink: 'var(--text)', muted: 'var(--muted)', accent: 'var(--accent)',
        bull: 'var(--bull)', bear: 'var(--bear)'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        serif: ['Source Serif 4', 'Georgia', 'serif']
      }
    }
  }
}
