<template>
  <div class="max-w-5xl mx-auto px-6 py-8 space-y-6">
    <h1 class="page-title">文档管理</h1>

    <!-- 上传区 -->
    <div class="card p-4">
      <div class="flex flex-col md:flex-row md:items-center gap-4">
        <select
          v-model="selectedKbId"
          class="border border-gray-200 rounded-lg px-3 py-2.5 text-sm text-gray-600 bg-gray-50 focus:bg-white focus:border-indigo-300 transition-colors w-full md:w-auto"
        >
          <option :value="null" disabled>-- 请选择知识库 --</option>
          <option v-for="kb in kbStore.knowledgeBases" :key="kb.id" :value="kb.id">
            {{ kb.name }}
          </option>
        </select>
        <UploadZone @upload="handleUpload" />
      </div>
      <p v-if="showError" class="text-sm text-red-500 mt-2">请先选择一个知识库再上传文档</p>
    </div>

    <!-- 文档列表 -->
    <DocumentList :documents="store.documents" @delete="handleDelete" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDocumentStore } from '../stores/document'
import { useKnowledgeStore } from '../stores/knowledge'
import UploadZone from '../components/documents/UploadZone.vue'
import DocumentList from '../components/documents/DocumentList.vue'

const store = useDocumentStore()
const kbStore = useKnowledgeStore()
const selectedKbId = ref<string | null>(null)
const showError = ref(false)
let pollingTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  store.loadDocuments()
  kbStore.loadAll()
  startPolling()
})

onUnmounted(() => { if (pollingTimer) clearInterval(pollingTimer) })

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(async () => {
    const docs = await store.loadDocuments(selectedKbId.value || undefined)
    const hasPending = docs?.some((d: any) => d.status === 'pending' || d.status === 'processing')
    if (!hasPending) stopPolling()
  }, 2000)
}

function stopPolling() {
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
}

async function handleUpload(files: File[]) {
  if (!selectedKbId.value) {
    showError.value = true
    setTimeout(() => showError.value = false, 3000)
    return
  }
  showError.value = false
  for (const file of files) {
    await store.upload(file, selectedKbId.value)
  }
  await store.loadDocuments(selectedKbId.value)
  startPolling()
}

async function handleDelete(id: string) {
  await store.remove(id)
  await store.loadDocuments(selectedKbId.value || undefined)
}
</script>
