<template>
  <div class="space-y-2">
    <div v-for="kb in items" :key="kb.id" class="flex items-center justify-between p-4 bg-white rounded-lg border">
      <div>
        <p class="font-medium">{{ kb.name }}</p>
        <p class="text-xs text-gray-400">{{ kb.description || '无描述' }} · {{ kb.document_count }} 篇文档</p>
      </div>
      <button @click="$emit('delete', kb.id)" class="text-red-400 hover:text-red-600">
        <Trash2 class="w-4 h-4" />
      </button>
    </div>
    <p v-if="!items.length" class="text-center text-gray-400 py-8">暂无知识库</p>
  </div>
</template>

<script setup lang="ts">
import { Trash2 } from 'lucide-vue-next'
import type { KnowledgeBase } from '../../types'

defineProps<{ items: KnowledgeBase[] }>()
defineEmits<{ delete: [id: string] }>()
</script>
