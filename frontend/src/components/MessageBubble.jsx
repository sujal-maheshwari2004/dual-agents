import ToolCallBadge from './ToolCallBadge'

const SEVERITY_COLOR = {
  block:   'text-danger border-danger/40',
  warning: 'text-warn  border-warn/40',
}

/**
 * MessageBubble — renders a single conversation turn.
 * User messages: right-aligned, accent-tinted border.
 * Assistant messages: left-aligned, surface bg, metadata row beneath.
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-up">
        <div className="max-w-[72%] px-4 py-2.5 border-r-2 border-accent/60 bg-surface text-text text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  // Assistant
  const hasTools  = message.tool_calls?.length > 0
  const hasFlags  = message.guardrail_flags?.length > 0

  return (
    <div className="flex flex-col gap-1 animate-fade-up">
      {/* Content */}
      <div className="max-w-[88%] px-4 py-2.5 border-l-2 border-border bg-surface text-text text-sm leading-relaxed whitespace-pre-wrap">
        {message.content}
      </div>

      {/* Tool calls */}
      {hasTools && (
        <div className="ml-4 flex flex-wrap gap-1">
          {message.tool_calls.map((tc, i) => (
            <ToolCallBadge key={i} toolCall={tc} />
          ))}
        </div>
      )}

      {/* Guardrail flags */}
      {hasFlags && (
        <div className="ml-4 flex flex-wrap gap-1">
          {message.guardrail_flags.map((flag, i) => (
            <span
              key={i}
              className={`font-mono text-[10px] px-2 py-0.5 border uppercase tracking-widest ${SEVERITY_COLOR[flag.severity] ?? 'text-dim border-border'}`}
            >
              {flag.source}:{flag.code}
            </span>
          ))}
        </div>
      )}

      {/* Metadata row */}
      {(message.model || message.latency_ms != null) && (
        <div className="ml-4 flex items-center gap-3 font-mono text-[10px] text-muted uppercase tracking-widest">
          {message.model && <span>{message.model}</span>}
          {message.latency_ms != null && <span>{message.latency_ms}ms</span>}
          {message.tokens_used > 0 && <span>{message.tokens_used} tok</span>}
        </div>
      )}
    </div>
  )
}