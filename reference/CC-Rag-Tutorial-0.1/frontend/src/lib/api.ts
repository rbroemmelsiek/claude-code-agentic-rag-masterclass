import { supabase } from './supabase'
import type { Thread, Message } from '@/types'

const API_URL = import.meta.env.VITE_API_URL

async function getAuthHeaders(): Promise<HeadersInit> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    throw new Error('Not authenticated')
  }
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

// Thread API
export async function listThreads(): Promise<Thread[]> {
  return fetchApi<Thread[]>('/threads')
}

export async function createThread(title?: string): Promise<Thread> {
  return fetchApi<Thread>('/threads', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export async function getThread(threadId: string): Promise<Thread> {
  return fetchApi<Thread>(`/threads/${threadId}`)
}

export async function updateThread(threadId: string, title: string): Promise<Thread> {
  return fetchApi<Thread>(`/threads/${threadId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
}

export async function deleteThread(threadId: string): Promise<void> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${API_URL}/threads/${threadId}`, {
    method: 'DELETE',
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }
}

// Messages API
export async function getMessages(threadId: string): Promise<Message[]> {
  return fetchApi<Message[]>(`/threads/${threadId}/messages`)
}

export interface SendMessageOptions {
  threadId: string
  content: string
  onTextDelta: (text: string) => void
  onDone: () => void
  onError: (error: string) => void
  signal?: AbortSignal
}

export async function sendMessage(options: SendMessageOptions): Promise<void> {
  const { threadId, content, onTextDelta, onDone, onError, signal } = options

  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_URL}/threads/${threadId}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
    signal,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No response body')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      console.log('[SSE] Chunk received:', chunk.length, 'bytes at', Date.now())
      buffer += chunk
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          const eventType = line.slice(7).trim()
          if (eventType === 'done') {
            onDone()
          }
          continue
        }
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              onTextDelta(parsed.content)
            }
            if (parsed.error) {
              onError(parsed.error)
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
