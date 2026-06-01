<template>
  <div class="max-w-5xl mx-auto px-6 py-8 space-y-6">
    <h1 class="page-title">知识库管理</h1>

    <KnowledgeForm @create="handleCreate" />

    <div class="space-y-3">
      <div v-for="kb in store.knowledgeBases" :key="kb.id" class="card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors" @click="toggleKb(kb.id)">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-50 to-purple-50 flex items-center justify-center">
              <BookOpen class="w-5 h-5 text-violet-500" />
            </div>
            <div>
              <span class="font-medium text-gray-800">{{ kb.name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ kb.description || '无描述' }} · {{ kb.document_count }} 篇文档</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button @click.stop="deleteKb(kb.id)" class="text-xs text-gray-400 hover:text-red-500 transition-colors px-2 py-1 rounded hover:bg-red-50">删除</button>
            <span class="text-xs text-gray-300">{{ expandedKbId === kb.id ? '收起 ▲' : '展开 ▼' }}</span>
          </div>
        </div>

        <div v-if="expandedKbId === kb.id" class="border-t border-gray-100 bg-gray-50/50">
          <div v-if="loadingDocs" class="p-6 text-sm text-gray-400 text-center">加载中...</div>
          <div v-else-if="!kbDocs.length" class="p-6 text-sm text-gray-400 text-center">暂无文档</div>
          <div v-else class="divide-y divide-gray-100">
            <div
              v-for="doc in kbDocs"
              :key="doc.id"
              class="px-5 py-3.5 flex items-center justify-between cursor-pointer hover:bg-white/80 transition-colors"
              @click="showDocContent(doc)"
            >
              <div class="flex items-center gap-3 min-w-0">
                <FileText class="w-4 h-4 text-gray-300 flex-shrink-0" />
                <div class="min-w-0">
                  <p class="text-sm text-gray-700 truncate">{{ doc.original_name }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">
                    {{ formatSize(doc.file_size) }}
                    <span v-if="doc.chunk_count"> · {{ doc.chunk_count }} 个分块</span>
                    <span v-if="doc.status === 'processing' || doc.status === 'pending'"
                      class="inline-block ml-1 w-2.5 h-2.5 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin align-middle">
                    </span>
                    <span :class="doc.status === 'completed' ? 'text-emerald-500' : 'text-yellow-500'"> · {{ doc.status }}</span>
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                <a :href="`/api/documents/${doc.id}/file`" download
                  class="text-xs text-blue-400 hover:text-blue-600 transition-colors px-2 py-1 rounded hover:bg-blue-50"
                  @click.stop>下载</a>
                <button @click.stop="deleteDoc(doc.id, kb.id)"
                  class="text-xs text-red-400 hover:text-red-600 transition-colors px-2 py-1 rounded hover:bg-red-50">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!store.knowledgeBases.length" class="text-center py-12">
        <BookOpen class="w-12 h-12 text-gray-200 mx-auto mb-3" />
        <p class="text-sm text-gray-400">暂无知识库</p>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <div v-if="previewDoc" class="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center z-50" @click.self="previewDoc = null">
      <div class="bg-white rounded-2xl w-[720px] max-h-[80vh] flex flex-col shadow-2xl m-4 overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 class="font-semibold text-gray-800 truncate flex items-center gap-2">
            <FileText class="w-4 h-4 text-indigo-500" />
            {{ previewDoc.original_name }}
          </h3>
          <button @click="previewDoc = null" class="text-gray-300 hover:text-gray-500 transition-colors text-xl">&times;</button>
        </div>
        <div class="p-6 overflow-y-auto text-sm whitespace-pre-wrap font-mono text-gray-600 leading-relaxed">
          <div v-if="loadingContent" class="text-center py-8 text-gray-300">加载中...</div>
          <div v-else-if="contentError" class="text-red-500">{{ contentError }}</div>
          <div v-else>{{ docContent }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useKnowledgeStore } from '../stores/knowledge'
import * as docApi from '../api/documents'
import type { Document } from '../types'
import KnowledgeForm from '../components/knowledge/KnowledgeForm.vue'
import { FileText, BookOpen } from 'lucide-vue-next'

const store = useKnowledgeStore()
const expandedKbId = ref<string | null>(null)
const kbDocs = ref<Document[]>([])
const loadingDocs = ref(false)
const previewDoc = ref<Document | null>(null)
const docContent = ref('')
const loadingContent = ref(false)
const contentError = ref('')
let pollingTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => store.loadAll())
onUnmounted(() => { if (pollingTimer) clearInterval(pollingTimer) })

async function handleCreate(name: string, desc?: string) {
  await store.create(name, desc)
}

function toggleKb(id: string) {
  if (expandedKbId.value === id) {
    expandedKbId.value = null
    kbDocs.value = []
    stopPolling()
    return
  }
  expandedKbId.value = id
  loadDocs(id)
  startPolling(id)
}

function startPolling(kbId: string) {
  stopPolling()
  pollingTimer = setInterval(async () => {
    const docs = await docApi.listDocuments(kbId)
    kbDocs.value = docs
    if (!docs.some(d => d.status === 'pending' || d.status === 'processing')) stopPolling()
  }, 2000)
}
function stopPolling() { if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null } }

async function loadDocs(kbId: string) {
  loadingDocs.value = true
  try { kbDocs.value = await docApi.listDocuments(kbId) } finally { loadingDocs.value = false }
}

async function deleteKb(id: string) {
  await store.remove(id)
  if (expandedKbId.value === id) { expandedKbId.value = null; kbDocs.value = [] }
}

async function deleteDoc(docId: string, kbId: string) {
  await docApi.deleteDocument(docId)
  await loadDocs(kbId)
  store.loadAll()
}

async function showDocContent(doc: Document) {
  if (doc.file_type === 'pdf') {
    previewDoc.value = null
    window.open(`/api/documents/${doc.id}/file`, '_blank')
    return
  }
  previewDoc.value = doc
  loadingContent.value = true
  contentError.value = ''
  docContent.value = ''
  try {
    const res = await docApi.getDocumentContent(doc.id)
    docContent.value = res.content || '(文件内容为空)'
  } catch (e: any) {
    contentError.value = e?.response?.data?.detail || '加载失败'
  } finally { loadingContent.value = false }
}

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>
