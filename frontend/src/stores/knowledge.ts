import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KnowledgeBase } from '../types'
import * as kbApi from '../api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const isLoading = ref(false)

  async function loadAll() {
    isLoading.value = true
    try {
      knowledgeBases.value = await kbApi.listKnowledgeBases()
    } finally {
      isLoading.value = false
    }
  }

  async function create(name: string, description?: string) {
    await kbApi.createKnowledgeBase(name, description)
    await loadAll()
  }

  async function remove(id: string) {
    await kbApi.deleteKnowledgeBase(id)
    knowledgeBases.value = knowledgeBases.value.filter(k => k.id !== id)
  }

  return { knowledgeBases, isLoading, loadAll, create, remove }
})
