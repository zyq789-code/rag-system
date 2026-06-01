import api from './client'
import type { Document } from '../types'

export async function uploadDocument(file: File, kbId?: string): Promise<any> {
  const form = new FormData()
  form.append('file', file)
  if (kbId) form.append('kb_id', kbId)
  const { data } = await api.post('/documents/upload', form)
  return data
}

export async function listDocuments(kbId?: string): Promise<Document[]> {
  const params = kbId ? { kb_id: kbId } : {}
  const { data } = await api.get('/documents/', { params })
  return data
}

export async function getDocument(id: string): Promise<Document> {
  const { data } = await api.get(`/documents/${id}`)
  return data
}

export async function deleteDocument(id: string) {
  await api.delete(`/documents/${id}`)
}

export async function getDocumentContent(id: string): Promise<{ content: string | null; filename: string; file_type: string }> {
  const { data } = await api.get(`/documents/${id}/content`)
  return data
}
