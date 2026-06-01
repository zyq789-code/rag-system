import { ref } from 'vue'
import type { Message, SourceCitation } from '../types'

export function useStreaming() {
  const isStreaming = ref(false)
  const error = ref<string | null>(null)

  async function sendMessage(
    content: string,
    conversationId?: string,
    kbId?: string,
    onToken: (token: string) => void,
    onSources: (sources: SourceCitation[]) => void,
    onDone: (convId: string) => void,
    onError?: (err: string) => void,
  ) {
    isStreaming.value = true
    error.value = null

    try {
      const response = await fetch('/api/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId || null,
          kb_id: kbId || null,
        }),
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      if (!response.body) {
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let receivedDone = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.token) onToken(data.token)
              if (data.sources) onSources(data.sources)
              if (data.done) {
                receivedDone = true
                onDone(data.conversation_id)
              }
            } catch { /* skip malformed */ }
          }
        }
      }

      if (!receivedDone) {
        onDone(conversationId || '')
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '未知错误'
      error.value = message
      onError?.(message)
    } finally {
      isStreaming.value = false
    }
  }

  return { isStreaming, error, sendMessage }
}
