import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DatasetTable } from '../components/lab/DatasetTable'
import { TrashTable } from '../components/lab/TrashTable'
import { DatasetList } from '../contracts/datasets'

const base = { size_bytes: 10, integrity: 'ok' as const, label: 'OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED' }

describe('dataset delete', () => {
  it('needs a confirmation, then calls delete with the file name', async () => {
    const onDelete = vi.fn().mockResolvedValue(undefined)
    render(<DatasetTable rows={[{ ...base, file: 'a.parquet' }]} folder="f" onDelete={onDelete} />)
    await userEvent.click(screen.getByRole('button', { name: 'Delete a.parquet' }))
    expect(onDelete).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(onDelete).toHaveBeenCalledWith('a.parquet')
  })
  it('cancel does nothing, and an API refusal is shown, not hidden', async () => {
    const onDelete = vi.fn().mockRejectedValue(new Error('a.parquet is in use by exp/EXP-001.yaml.'))
    render(<DatasetTable rows={[{ ...base, file: 'a.parquet' }]} folder="f" onDelete={onDelete} />)
    await userEvent.click(screen.getByRole('button', { name: 'Delete a.parquet' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onDelete).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Delete a.parquet' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('in use by exp/EXP-001.yaml')
  })
  it('an in-use dataset has no delete button and says what uses it', () => {
    render(<DatasetTable rows={[{ ...base, file: 'locked.parquet', in_use: ['prereg/EXP-001.yaml'] }]} folder="f" onDelete={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /Delete/ })).toBeNull()
    expect(screen.getByText('In use')).toBeInTheDocument()
    expect(screen.getByText(/Used by prereg\/EXP-001.yaml/)).toBeInTheDocument()
  })
  it('the list contract still accepts an API that sends no trash or in_use field', () => {
    const ok = DatasetList.parse({ folder: 'f', items: [{ file: 'a.parquet', size_bytes: 1, integrity: 'ok' }], token_configured: true,
      options: { instruments: ['EUR_USD'], timeframes: ['H1'], max_bars: 10 } })
    expect(ok.trash).toEqual([])
  })
})

describe('trash', () => {
  const rows = [{ id: '20261028T101500Z__a.parquet', file: 'a.parquet', size_bytes: 5000, deleted_at: '2026-10-28T10:15:00Z' }]
  it('restores in one click and deletes for good only after a confirmation', async () => {
    const onRestore = vi.fn().mockResolvedValue(undefined), onPurge = vi.fn().mockResolvedValue(undefined)
    render(<TrashTable rows={rows} onRestore={onRestore} onPurge={onPurge} />)
    await userEvent.click(screen.getByRole('button', { name: 'Restore a.parquet' }))
    expect(onRestore).toHaveBeenCalledWith(rows[0].id)
    await userEvent.click(screen.getByRole('button', { name: 'Delete a.parquet for good' }))
    expect(onPurge).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(onPurge).toHaveBeenCalledWith(rows[0].id)
  })
  it('renders nothing when the trash is empty', () => {
    const { container } = render(<TrashTable rows={[]} onRestore={vi.fn()} onPurge={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })
})
