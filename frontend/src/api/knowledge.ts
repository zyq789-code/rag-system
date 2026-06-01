import api from './client'
import type { KnowledgeBase } from '../types'

export async function createKnowledgeBase(name: string, description?: string): Promise<KnowledgeBase> {
  const { data } = await api.post('/knowledge-bases/', { name, description })
  return data
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  const { data } = await api.get('/knowledge-bases/')
  return data
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBase> {
  const { data } = await api.get(`/knowledge-bases/${id}`)
  return data
}

export async function updateKnowledgeBase(id: string, name?: string, description?: string): Promise<KnowledgeBase> {
  const { data } = await api.put(`/knowledge-bases/${id}`, { name, description })
  return data
}

export async function deleteKnowledgeBase(id: string) {
  await api.delete(`/knowledge-bases/${id}`)
}
