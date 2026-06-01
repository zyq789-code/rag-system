<template>
  <div class="card divide-y divide-gray-100 overflow-hidden">
    <div v-for="doc in documents" :key="doc.id" class="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors">
      <div class="flex items-center gap-4 min-w-0">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center flex-shrink-0">
          <FileText class="w-5 h-5 text-indigo-500" />
        </div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-gray-700 truncate">{{ doc.original_name }}</p>
          <p class="text-xs text-gray-400 mt-0.5">
            {{ formatSize(doc.file_size) }}
            <span v-if="doc.chunk_count"> · {{ doc.chunk_count }} 个分块</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-3 flex-shrink-0 ml-4">
        <!-- 状态 -->
        <div class="flex items-center gap-1.5">
          <span v-if="doc.status === 'processing' || doc.status === 'pending'"
            class="inline-block w-3 h-3 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin">
          </span>
          <span :class="[
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
            doc.status === 'completed' ? 'bg-emerald-50 text-emerald-600' :
            doc.status === 'processing' ? 'bg-blue-50 text-blue-600' :
            doc.status === 'failed' ? 'bg-red-50 text-red-600' :
            'bg-gray-100 text-gray-500'
          ]">{{ statusLabel(doc.status) }}</span>
        </div>
        <button @click="$emit('delete', doc.id)"
          class="p-1.5 rounded-lg text-gray-300 hover:text-red-400 hover:bg-red-50 transition-colors">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>
    <div v-if="!documents.length" class="text-center py-12">
      <FileText class="w-12 h-12 text-gray-200 mx-auto mb-3" />
      <p class="text-sm text-gray-400">暂无文档</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileText, Trash2 } from 'lucide-vue-next'
import type { Document } from '../../types'

defineProps<{ documents: Document[] }>()
defineEmits<{ delete: [id: string] }>()

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function statusLabel(status: string) {
  return { pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败' }[status] || status
}
</script>
