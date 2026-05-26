import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'

const PLACEHOLDER_HINTS = [
  'Ask anything…',
  'Try: "translate hello to Japanese"',
  'Try: "what is 144 * 37?"',
  'Try: "who was Ada Lovelace?"',
  'Try: "search: latest AI news"',
]

/**
 * ChatWindow — full-height flex column.
 * Top:    scrollable message list, auto-scrolls to bottom.
 * Bottom: pinned composer with send button.
 */
export default function ChatWindow({ messages, loading, onSend }) {
  const [input, setInput]       = useState('')
  const [hint]                  = useState(() => PLACEHOLDER_HINTS[Math.floor(Math.random() * PLACEHOLDER_HINTS.length)])
  const bottomRef               = useRef(null)
  const textareaRef             = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const submit = () => {
    if (!input.trim() || loading) return
    onSend(input)
    setInput('')
    textareaRef.current?.focus()
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-2">
              <p className="font-mono text-xs uppercase tracking-widest text-muted">
                dual agents / ready
              </p>
              <p className="text-dim text-sm">
                Send a message to begin.
              </p>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex items-center gap-2 animate-fade-up">
            <div className="flex gap-1 ml-4">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 bg-accent/60 rounded-full animate-pulse-dot"
                  style={{ animationDelay: `${i * 0.22}s` }}
                />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div className="border-t border-border bg-surface px-4 py-3 flex gap-3 items-end">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={hint}
          disabled={loading}
          className={[
            'flex-1 resize-none bg-transparent text-text text-sm leading-relaxed',
            'placeholder:text-muted outline-none font-sans',
            'max-h-32 overflow-y-auto',
            'disabled:opacity-50',
          ].join(' ')}
          style={{ fieldSizing: 'content' }}
        />

        <button
          onClick={submit}
          disabled={!input.trim() || loading}
          className={[
            'font-mono text-xs uppercase tracking-widest px-4 py-2',
            'border transition-colors duration-150 cursor-pointer',
            input.trim() && !loading
              ? 'border-accent text-accent hover:bg-accent hover:text-bg'
              : 'border-border text-muted cursor-not-allowed',
          ].join(' ')}
        >
          Send
        </button>
      </div>
    </div>
  )
}