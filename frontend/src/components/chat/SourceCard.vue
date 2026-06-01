<template>
  <div class="flex items-start gap-2.5 p-3 rounded-lg bg-white border border-gray-100 shadow-xs">
    <div class="w-7 h-7 rounded-md bg-indigo-50 flex items-center justify-center flex-shrink-0 mt-0.5">
      <svg class="w-3.5 h-3.5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    </div>
    <div class="min-w-0">
      <p class="text-xs font-medium text-gray-600 truncate">{{ source.filename }}</p>
      <p class="text-xs text-gray-400 mt-0.5 line-clamp-2">{{ source.chunk_text }}</p>
      <p class="text-xs text-gray-300 mt-1">相关度: {{ (source.score * 100).toFixed(0) }}%</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SourceCitation } from '../../types'

defineProps<{ source: SourceCitation }>()
</script>
