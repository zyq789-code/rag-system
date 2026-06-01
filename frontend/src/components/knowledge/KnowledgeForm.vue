<template>
  <form @submit.prevent="handleSubmit" class="flex gap-2">
    <input v-model="name" placeholder="知识库名称" class="flex-1 border rounded-lg px-3 py-2 text-sm" required />
    <input v-model="desc" placeholder="描述（可选）" class="flex-1 border rounded-lg px-3 py-2 text-sm" />
    <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
      创建
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ create: [name: string, desc?: string] }>()
const name = ref('')
const desc = ref('')

function handleSubmit() {
  if (!name.value.trim()) return
  emit('create', name.value.trim(), desc.value.trim() || undefined)
  name.value = ''
  desc.value = ''
}
</script>
