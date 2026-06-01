import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Document } from '../types'
import * as docApi from '../api/documents'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const isLoading = ref(false)

  async function loadDocuments(kbId?: string) {
    isLoading.value = true
    try {
      const result = await docApi.listDocuments(kbId)
      documents.value = result
      return result
    } finally {
      isLoading.value = false
    }
  }

  async function upload(file: File, kbId?: string) {
    await docApi.uploadDocument(file, kbId)
    await loadDocuments(kbId)
  }

  async function remove(id: string) {
    await docApi.deleteDocument(id)
    documents.value = documents.value.filter(d => d.id !== id)
  }

  return { documents, isLoading, loadDocuments, upload, remove }
})
