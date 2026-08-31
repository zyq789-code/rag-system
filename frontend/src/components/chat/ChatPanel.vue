<template>
  <div class="flex flex-col h-full">
    <!-- 顶部栏 -->
    <div class="flex items-center justify-between px-4 md:px-6 py-3 border-b border-gray-100 bg-white/80 backdrop-blur-sm">
      <div class="flex items-center gap-1 min-w-0">
        <button
          @click="store.toggleMobileHistory()"
          class="md:hidden p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 flex-shrink-0"
          title="对话历史"
        >
          <Menu class="w-5 h-5" />
        </button>
        <h2 class="font-semibold text-gray-800 truncate" style="font-family: var(--font-heading)">智能问答</h2>
      </div>
      <div class="flex items-center gap-2 md:gap-3 flex-shrink-0">
        <div v-if="isKbLocked" class="flex items-center gap-1.5 text-xs text-indigo-600 bg-indigo-50 px-2.5 py-1.5 rounded-lg">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
          <span class="max-w-[80px] truncate">{{ kbName }}</span>
        </div>
        <select
          v-else
          v-model="selectedKbId"
          class="text-sm border border-gray-200 rounded-lg px-2 md:px-3 py-1.5 text-gray-600 bg-gray-50 focus:bg-white focus:border-indigo-300 transition-colors max-w-[110px] md:max-w-none"
        >
          <option :value="null">全部文档</option>
          <option v-for="kb in kbStore.knowledgeBases" :key="kb.id" :value="kb.id">
            {{ kb.name }}
          </option>
        </select>
        <button @click="store.clearChat()" class="text-sm text-gray-400 hover:text-gray-600 transition-colors px-2 py-1 rounded hover:bg-gray-100 whitespace-nowrap">
          新对话
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <MessageList :messages="store.messages" />

    <!-- 输入区 -->
    <div class="border-t border-gray-100 bg-white px-4 md:px-6 py-4">
      <div class="flex gap-2 md:gap-3 max-w-4xl mx-auto">
        <textarea
          v-model="input"
          @keydown.enter.prevent="handleSend"
          placeholder="输入问题..."
          class="flex-1 resize-none border border-gray-200 rounded-xl px-3 md:px-4 py-3 text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300 transition-colors bg-gray-50 hover:bg-white focus:bg-white"
          rows="1"
        />
        <button
          @click="handleSend"
          :disabled="!input.trim() || store.isStreaming"
          class="px-4 md:px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium transition-all shadow-sm hover:shadow"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useKnowledgeStore } from '../../stores/knowledge'
import MessageList from './MessageList.vue'
import { Menu } from 'lucide-vue-next'

const store = useChatStore()
const kbStore = useKnowledgeStore()
const input = ref('')
const selectedKbId = ref<string | null>(null)

onMounted(() => {
  kbStore.loadAll()
})

// 切换对话时锁定 KB 选择
watch(() => store.currentConversationId, (convId) => {
  if (!convId) { selectedKbId.value = null; return }
  const conv = store.conversations.find(c => c.id === convId)
  if (conv?.kb_id) selectedKbId.value = conv.kb_id
})

const isKbLocked = computed(() => !!store.currentConversationId && !!selectedKbId.value)
const kbName = computed(() => {
  const kb = kbStore.knowledgeBases.find(k => k.id === selectedKbId.value)
  return kb?.name || '知识库'
})

function handleSend() {
  if (!input.value.trim() || store.isStreaming) return
  store.send(input.value.trim(), selectedKbId.value || undefined)
  input.value = ''
}
</script>
