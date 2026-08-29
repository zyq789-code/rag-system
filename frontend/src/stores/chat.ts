import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Message, Conversation, SourceCitation } from '../types'
import * as chatApi from '../api/chat'
import { useStreaming } from '../composables/useStreaming'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const { isStreaming, error, sendMessage: streamSend } = useStreaming()

  async function loadConversations() {
    conversations.value = await chatApi.listConversations()
  }

  async function loadMessages(conversationId: string) {
    currentConversationId.value = conversationId
    messages.value = await chatApi.getMessages(conversationId)
  }

  async function send(content: string, kbId?: string) {
    messages.value.push({ role: 'user', content })
    const assistantMsg: Message = { role: 'assistant', content: '', sources: [] }
    messages.value.push(assistantMsg)
    const idx = messages.value.length - 1

    await streamSend(
      content,
      (token) => { messages.value[idx].content += token },
      (sources) => { messages.value[idx].sources = sources },
      (convId) => {
        currentConversationId.value = convId
        loadConversations()
      },
      currentConversationId.value || undefined,
      kbId,
      (errMsg) => {
        messages.value[idx].content = `请求失败: ${errMsg}`
      },
    )
  }

  async function removeConversation(id: string) {
    await chatApi.deleteConversation(id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      messages.value = []
    }
    await loadConversations()
  }

  function clearChat() {
    currentConversationId.value = null
    messages.value = []
  }

  return {
    conversations, currentConversationId, messages, isLoading, isStreaming, error,
    loadConversations, loadMessages, send, removeConversation, clearChat,
  }
})
