import { useCallback, useEffect, useState } from 'react'
import { clearMemory, getMemory } from '../api/client'

/**
 * MemoryPanel — collapsible sidebar panel.
 * Fetches long-term memory for the current user on open.
 */
export default function MemoryPanel({ userId }) {
  const [open, setOpen]       = useState(false)
  const [records, setRecords] = useState([])
  const [status, setStatus]   = useState('idle') // 'idle' | 'loading' | 'error'

  const load = useCallback(async () => {
    setStatus('loading')
    try {
      const data = await getMemory(userId)
      setRecords(data.memories ?? [])
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }, [userId])

  useEffect(() => {
    if (open) load()
  }, [open, load])

  const handleClear = async () => {
    setStatus('loading')
    try {
      await clearMemory(userId)
      setRecords([])
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className="border-t border-border font-mono text-xs">
      {/* Toggle row */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-dim hover:text-accent hover:bg-surface/60 transition-colors cursor-pointer"
      >
        <span className="uppercase tracking-widest">Long-term Memory</span>
        <span className="text-muted">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="border-t border-border bg-surface animate-fade-up">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-border">
            <span className="text-muted uppercase tracking-widest">
              {records.length} record{records.length !== 1 ? 's' : ''}
            </span>
            {records.length > 0 && (
              <button
                onClick={handleClear}
                disabled={status === 'loading'}
                className="text-danger hover:text-danger/70 uppercase tracking-widest transition-colors cursor-pointer disabled:opacity-40"
              >
                clear
              </button>
            )}
          </div>

          {/* Records list */}
          <div className="max-h-52 overflow-y-auto divide-y divide-border">
            {status === 'loading' && (
              <div className="px-4 py-3 text-muted">loading…</div>
            )}
            {status === 'error' && (
              <div className="px-4 py-3 text-danger">Failed to fetch memory.</div>
            )}
            {status === 'idle' && records.length === 0 && (
              <div className="px-4 py-3 text-muted">No memories stored yet.</div>
            )}
            {status === 'idle' && records.map((rec, i) => (
              <div key={i} className="px-4 py-2 flex gap-3">
                <span className="text-accent/70 shrink-0 w-28 truncate">{rec.key}</span>
                <span className="text-dim truncate">{rec.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}