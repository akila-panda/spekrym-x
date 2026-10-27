import { Chart } from '../components/Chart'
import { Badge } from '../components/Badge'
import { Inspector } from '../components/Inspector'
import { LayerControls } from '../components/LayerControls'
import { ReplayBar } from '../components/ReplayBar'
import { SessionObjects } from '../components/SessionObjects'
import { Stepper } from '../components/Stepper'
import { Timeline } from '../components/Timeline'
import { SessionPlan } from './SessionPlan'
import { MtfStrip } from '../components/MtfStrip'
import { useDataset } from '../data/DataProvider'
import { barsKnownAt } from '../layers/replay'
import { computeVisibility } from '../layers/visibility'
import { useUi } from '../state/store'

export function Workspace({ mode }: { mode: 'premarket' | 'chart' }) {
  const { step, hidden, selected, preset, replayT, theme } = useUi()
  const ds = useDataset()
  const { bars, lastClose, objects, steps } = ds
  const stepIds = mode === 'premarket' ? steps[step - 1].show : objects.map(o => o.id)
  const known = barsKnownAt(bars, replayT)
  const refPrice = known.length ? known[known.length - 1].close : lastClose
  const vis = computeVisibility({ objects, stepIds, hidden, preset, refPrice, replayT, selected })
  const plan = mode === 'premarket' && step === 6

  return (
    <div className="flex h-full min-h-0">
      <aside aria-label="Workflow and objects" className="no-print w-64 shrink-0 space-y-4 overflow-y-auto border-r border-line p-4">
        {mode === 'premarket' && <Stepper />}
        <SessionObjects available={vis.available} drawn={vis.drawn} />
      </aside>
      {plan ? <SessionPlan /> : (
        <>
          <section aria-label="Chart" className="flex min-w-0 flex-1 flex-col">
            <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-2">
              <span className="font-mono text-sm">{ds.instrument.replace('_', '')} · M15</span>
              <LayerControls />
              <Badge tone="warn">{ds.badge}</Badge></div>
            {mode === 'premarket' && <MtfStrip />}
            <div className="min-h-0 flex-1"><Chart key={ds.id} visible={vis.drawn} selected={selected} theme={theme} replayT={replayT} /></div>
            {mode === 'premarket' ? <Timeline /> : <ReplayBar />}
          </section>
          <Inspector />
        </>)}
    </div>
  )
}
