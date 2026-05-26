import { useCallback, useRef, useState } from 'react'
import { sendMessage } from '../api/client'

/**
 * Stable IDs for the session and user, generated once per page load.
 */
function makeId(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

const SESSION_ID = makeId('session')
const USER_ID    = makeId('user')

/**
 * @typedef {{ id: string, role: 'user'|'assistant', content: string,
 *   model?: string, latency_ms?: number, tokens_used?: number,
 *   tool_calls?: any[], guardrail_flags?: any[], ts: number }} Message
 */

export function useChat() {
  const [messages, setMessages]   = useState(/** @type {Message[]} */ ([]))
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(/** @type {string|null} */ (null))
  const [model, setModel]         = useState(/** @type {'oss'|'frontier'} */ ('frontier'))
  const abortRef                  = useRef(null)

  const appendMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { id: makeId('msg'), ts: Date.now(), ...msg }])
  }, [])

  const send = useCallback(async (text) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    setError(null)
    appendMessage({ role: 'user', content: trimmed })
    setLoading(true)

    try {
      const data = await sendMessage({
        sessionId: SESSION_ID,
        userId:    USER_ID,
        message:   trimmed,
        model,
      })

      appendMessage({
        role:            'assistant',
        content:         data.reply,
        model:           data.model,
        latency_ms:      data.latency_ms,
        tokens_used:     data.tokens_used,
        tool_calls:      data.tool_calls      ?? [],
        guardrail_flags: data.guardrail_flags ?? [],
      })
    } catch (err) {
      setError(err.message ?? 'Unknown error')
      appendMessage({
        role:    'assistant',
        content: '⚠ Request failed. Check the backend or your API keys.',
        model:   model,
      })
    } finally {
      setLoading(false)
    }
  }, [loading, model, appendMessage])

  const clearMessages = useCallback(() => setMessages([]), [])

  return {
    messages,
    loading,
    error,
    model,
    setModel,
    send,
    clearMessages,
    userId: USER_ID,
    sessionId: SESSION_ID,
  }
}