import api from './client'
import type { Conversation } from '../types'

export async function listConversations(): Promise<Conversation[]> {
  const { data } = await api.get('/chat/conversations')
  return data
}

export async function getMessages(conversationId: string) {
  const { data } = await api.get(`/chat/conversations/${conversationId}/messages`)
  return data
}

export async function deleteConversation(conversationId: string) {
  await api.delete(`/chat/conversations/${conversationId}`)
}
