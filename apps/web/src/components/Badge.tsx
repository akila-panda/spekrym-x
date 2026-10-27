export function Badge({ children, tone = 'muted' }: { children: React.ReactNode; tone?: 'muted' | 'accent' | 'warn' }) {
  const c = tone === 'accent' ? 'var(--accent)' : tone === 'warn' ? 'var(--warn)' : 'var(--muted)'
  return <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium"
    style={{ color: c, borderColor: c }}>{children}</span>
}
