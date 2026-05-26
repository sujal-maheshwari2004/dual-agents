const BASE = import.meta.env.VITE_API_URL ?? ''

/**
 * POST /chat
 * @param {{ sessionId: string, userId: string, message: string, model: 'oss'|'frontier' }} params
 * @returns {Promise<ChatResponse>}
 */
export async function sendMessage({ sessionId, userId, message, model }) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id:    userId,
      message,
      model,
    }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Chat request failed (${res.status}): ${text}`)
  }
  return res.json()
}

/**
 * GET /memory/:userId
 * @param {string} userId
 * @returns {Promise<MemoryResponse>}
 */
export async function getMemory(userId) {
  const res = await fetch(`${BASE}/memory/${encodeURIComponent(userId)}`)
  if (!res.ok) throw new Error(`Memory fetch failed (${res.status})`)
  return res.json()
}

/**
 * DELETE /memory/:userId
 * @param {string} userId
 * @returns {Promise<{ user_id: string, cleared: boolean }>}
 */
export async function clearMemory(userId) {
  const res = await fetch(`${BASE}/memory/${encodeURIComponent(userId)}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(`Memory clear failed (${res.status})`)
  return res.json()
}

/**
 * GET /health
 */
export async function getHealth() {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed (${res.status})`)
  return res.json()
}