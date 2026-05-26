import { useState } from 'react'

const TOOL_ICONS = {
  web_search:  '⌕',
  calculator:  '∑',
  wikipedia:   'W',
  translation: '⇄',
}

/**
 * ToolCallBadge — shown below assistant messages when tool calls were made.
 * Clicking expands to show input/output details.
 */
export default function ToolCallBadge({ toolCall }) {
  const [open, setOpen] = useState(false)
  const icon = TOOL_ICONS[toolCall.name] ?? '◆'

  return (
    <div className="mt-1 font-mono text-[11px]">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-1.5 px-2 py-0.5 border border-border text-dim hover:text-accent hover:border-accent/40 transition-colors cursor-pointer"
      >
        <span className="text-accent/70">{icon}</span>
        <span className="uppercase tracking-widest">{toolCall.name}</span>
        <span className="ml-1 text-muted">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="mt-1 border border-border bg-surface p-2 space-y-1 text-[11px] animate-fade-up">
          {toolCall.input && Object.keys(toolCall.input).length > 0 && (
            <div>
              <span className="text-muted uppercase tracking-widest">in </span>
              <span className="text-dim">{JSON.stringify(toolCall.input)}</span>
            </div>
          )}
          {toolCall.output != null && (
            <div>
              <span className="text-muted uppercase tracking-widest">out </span>
              <span className="text-text/70 break-all">
                {typeof toolCall.output === 'string'
                  ? toolCall.output.slice(0, 300) + (toolCall.output.length > 300 ? '…' : '')
                  : JSON.stringify(toolCall.output).slice(0, 300)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}