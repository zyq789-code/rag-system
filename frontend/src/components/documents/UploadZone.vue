<template>
  <div
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
    @click="openPicker"
    :class="[
      'flex-1 border-2 border-dashed rounded-xl py-6 px-4 text-center transition-all cursor-pointer',
      isDragging ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
    ]"
  >
    <input ref="fileInput" type="file" class="hidden" accept=".pdf,.docx,.txt,.md" @change="handleSelect" multiple />
    <div class="flex items-center justify-center gap-2 text-sm text-gray-400">
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
      <span>拖拽文件到此处或点击上传</span>
      <span class="text-xs text-gray-300">| PDF、DOCX、TXT、MD</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ upload: [files: File[]] }>()
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement>()

function openPicker() { fileInput.value?.click() }

function handleDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files) emit('upload', Array.from(e.dataTransfer.files))
}

function handleSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) emit('upload', Array.from(input.files))
}
</script>
