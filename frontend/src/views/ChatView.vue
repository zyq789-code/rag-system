<template>
  <div class="flex h-full">
    <!-- 对话历史侧栏 -->
    <div class="w-64 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
      <div class="px-4 py-4 border-b border-gray-100">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-400">对话历史</h3>
      </div>
      <div class="flex-1 overflow-y-auto p-2 space-y-0.5">
        <div
          v-for="conv in store.conversations"
          :key="conv.id"
          class="group relative"
        >
          <button
            @click="store.loadMessages(conv.id)"
            :class="[
              'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors',
              store.currentConversationId === conv.id
                ? 'bg-indigo-50 text-indigo-700 font-medium'
                : 'text-gray-600 hover:bg-gray-50'
            ]"
          >
            <span class="truncate block">{{ conv.title || '新对话' }}</span>
          </button>
          <button
            @click.stop="store.removeConversation(conv.id)"
            class="absolute right-1.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-xs text-gray-300 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-red-50"
          >
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天主区域 -->
    <div class="flex-1 flex flex-col bg-white">
      <ChatPanel />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useChatStore } from '../stores/chat'
import ChatPanel from '../components/chat/ChatPanel.vue'

const store = useChatStore()
onMounted(() => store.loadConversations())
</script>
