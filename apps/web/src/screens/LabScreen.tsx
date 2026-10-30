import { useState } from 'react'
import { Badge } from '../components/Badge'
import { Exp001Tab } from '../components/lab/Exp001Tab'
import { LabDataTab } from '../components/lab/LabDataTab'

const TABS = [['data', 'Data'], ['exp001', 'EXP-001']] as const
type Tab = (typeof TABS)[number][0]

export function LabScreen() {
  const [tab, setTab] = useState<Tab>('data')
  return (
    <section aria-label="Lab" className="h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="space-y-2">
          <h1 className="font-serif text-2xl font-semibold">Lab</h1>
          <div className="flex gap-2"><Badge>Exploratory</Badge><Badge>Not validated</Badge></div>
          <div role="tablist" aria-label="Lab sections" className="flex gap-1 border-b border-line">
            {TABS.map(([id, label]) => (
              <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
                className={`px-3 py-1.5 text-sm ${tab === id ? 'border-b-2 border-accent font-medium' : 'text-muted'}`}>{label}</button>))}
          </div>
        </header>
        <div role="tabpanel" aria-label={tab === 'data' ? 'Data' : 'EXP-001'}>{tab === 'data' ? <LabDataTab /> : <Exp001Tab />}</div>
      </div>
    </section>)
}
