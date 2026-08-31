<template>
  <div class="flex-1 overflow-y-auto p-2 space-y-0.5">
    <div v-for="conv in store.conversations" :key="conv.id" class="group relative">
      <button
        @click="selectConv(conv)"
        :class="[
          'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors',
          store.currentConversationId === conv.id
            ? 'bg-indigo-50 text-indigo-700 font-medium'
            : 'text-gray-600 hover:bg-gray-50'
        ]"
      >
        <span class="truncate block">{{ conv.title || '新对话' }}</span>
      </button>
      <!-- 删除按钮：桌面 hover 显示，手机常显 -->
      <button
        @click.stop="removeConv(conv.id)"
        class="absolute right-1.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-xs text-gray-300 hover:text-red-400 transition-opacity rounded hover:bg-red-50 opacity-100 md:opacity-0 md:group-hover:opacity-100"
      >
        删除
      </button>
    </div>
    <p v-if="!store.conversations.length" class="text-sm text-gray-400 text-center py-8">暂无对话</p>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '../../stores/chat'
import type { Conversation } from '../../types'

const store = useChatStore()

function selectConv(conv: Conversation) {
  store.loadMessages(conv.id)
  // 手机端选择后关闭抽屉
  store.mobileHistoryOpen = false
}

function removeConv(id: string) {
  store.removeConversation(id)
}
</script>