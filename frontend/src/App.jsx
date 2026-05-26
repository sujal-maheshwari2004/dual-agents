import { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow'
import MemoryPanel from './components/MemoryPanel'
import ModelToggle from './components/ModelToggle'
import { useChat } from './hooks/useChat'
import { getHealth } from './api/client'

function StatusDot({ ok }) {
  return (
    <span
      className={[
        'inline-block w-1.5 h-1.5 rounded-full',
        ok === true  ? 'bg-accent animate-pulse-dot' :
        ok === false ? 'bg-danger' :
                       'bg-muted animate-blink',
      ].join(' ')}
    />
  )
}

export default function App() {
  const { messages, loading, model, setModel, send, clearMessages, userId } = useChat()
  const [backendOk, setBackendOk] = useState(null)

  useEffect(() => {
    getHealth()
      .then(() => setBackendOk(true))
      .catch(() => setBackendOk(false))
  }, [])

  return (
    <div className="h-full flex flex-col bg-bg text-text overflow-hidden">

      {/* ── Header ───────────────────────────────────────────── */}
      <header className="shrink-0 h-12 border-b border-border bg-surface flex items-center justify-between px-6 gap-4">
        <div className="flex items-center gap-3">
          <StatusDot ok={backendOk} />
          <span className="font-mono text-xs uppercase tracking-widest text-text">
            Dual Agents
          </span>
          <span className="hidden sm:inline font-mono text-[10px] text-muted uppercase tracking-widest border-l border-border pl-3">
            OSS × Frontier
          </span>
        </div>

        <div className="flex items-center gap-3">
          <ModelToggle model={model} onChange={setModel} />
          <button
            onClick={clearMessages}
            className="font-mono text-[10px] uppercase tracking-widest text-muted hover:text-danger transition-colors cursor-pointer px-1"
          >
            ✕ clear
          </button>
        </div>
      </header>

      {/* ── Body ─────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* Chat */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <ChatWindow messages={messages} loading={loading} onSend={send} />
        </main>

        {/* Sidebar — lg+ only */}
        <aside className="hidden lg:flex flex-col w-56 border-l border-border bg-surface shrink-0">
          <div className="p-4 border-b border-border">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted mb-2">Session</p>
            <p className="font-mono text-[10px] text-dim break-all leading-relaxed">{userId}</p>
          </div>

          <div className="p-4 border-b border-border">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted mb-1">Model</p>
            <p className="font-mono text-xs text-accent">
              {model === 'frontier' ? 'GPT-4.1' : 'Qwen 2.5-0.5B'}
            </p>
            <p className="font-mono text-[10px] text-muted uppercase tracking-widest">{model}</p>
          </div>

          <div className="p-4 border-b border-border">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted mb-1">Backend</p>
            <div className="flex items-center gap-2">
              <StatusDot ok={backendOk} />
              <span className="font-mono text-[10px] text-dim">
                {backendOk === null ? 'checking…' : backendOk ? 'connected' : 'unreachable'}
              </span>
            </div>
          </div>

          <div className="p-4">
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted mb-1">Messages</p>
            <p className="font-mono text-xs text-text">{messages.length}</p>
          </div>

          <div className="flex-1" />
          <MemoryPanel userId={userId} />
        </aside>
      </div>

      {/* ── Mobile memory strip ──────────────────────────────── */}
      <div className="lg:hidden border-t border-border">
        <MemoryPanel userId={userId} />
      </div>

    </div>
  )
}