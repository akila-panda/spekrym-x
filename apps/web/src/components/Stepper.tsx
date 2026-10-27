import { useDataset } from '../data/DataProvider'
import { useUi } from '../state/store'

export function Stepper() {
  const { step, setStep } = useUi()
  const { steps } = useDataset()
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-muted"><span>New York preparation</span><span>Step {step} of 6</span></div>
      <div className="mb-3 h-1 rounded bg-surface2" role="progressbar" aria-label="Analysis workflow progress" aria-valuemin={0} aria-valuemax={6} aria-valuenow={step}>
        <div className="h-1 rounded bg-accent" style={{ width: `${(step / 6) * 100}%` }} /></div>
      <ol className="space-y-1">
        {steps.map(s => (
          <li key={s.id}><button onClick={() => setStep(s.id)} aria-current={step === s.id ? 'step' : undefined}
            className={`w-full rounded-md px-2 py-1.5 text-left text-sm ${step === s.id ? 'bg-surface2 text-ink' : 'text-muted hover:text-ink'}`}>
            {s.id}. {s.title}{s.id < step && <span className="ml-1 text-bull" aria-label="done">✓</span>}</button></li>))}
      </ol>
    </div>)
}
