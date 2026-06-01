<template>
  <div class="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer hover:border-gray-400" @click="openPicker">
    <input ref="fileInput" type="file" class="hidden" accept=".pdf,.docx,.txt" @change="handleSelect" />
    <p class="text-gray-500">上传简历文件进行 AI 分析</p>
    <p class="text-xs text-gray-400 mt-1">支持 PDF、DOCX、TXT</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ upload: [file: File] }>()
const fileInput = ref<HTMLInputElement>()

function openPicker() { fileInput.value?.click() }

function handleSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) emit('upload', input.files[0])
}
</script>
