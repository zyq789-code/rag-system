<template>
  <div class="flex h-full">
    <!-- 对话历史 · 桌面侧栏 -->
    <div class="hidden md:flex w-64 flex-shrink-0 border-r border-gray-200 bg-white flex-col">
      <div class="px-4 py-4 border-b border-gray-100">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-400">对话历史</h3>
      </div>
      <ConversationList />
    </div>

    <!-- 对话历史 · 手机抽屉 -->
    <transition name="fade">
      <div v-if="store.mobileHistoryOpen" class="md:hidden fixed inset-0 z-40">
        <div class="absolute inset-0 bg-black/30" @click="store.mobileHistoryOpen = false"></div>
        <div class="absolute left-0 top-0 bottom-0 w-72 max-w-[80vw] bg-white shadow-xl flex flex-col">
          <div class="px-4 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-xs font-semibold uppercase tracking-wider text-gray-400">对话历史</h3>
            <button
              @click="store.mobileHistoryOpen = false"
              class="text-gray-300 hover:text-gray-500 text-xl leading-none px-1"
            >&times;</button>
          </div>
          <ConversationList />
        </div>
      </div>
    </transition>

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
import ConversationList from '../components/chat/ConversationList.vue'

const store = useChatStore()
onMounted(() => store.loadConversations())
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>