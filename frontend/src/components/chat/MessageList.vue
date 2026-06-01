<template>
  <div ref="scrollRef" class="flex-1 overflow-y-auto px-6 py-6">
    <div class="max-w-3xl mx-auto space-y-6">
      <div v-for="(msg, i) in messages" :key="i" class="flex gap-4" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
        <!-- 头像 -->
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold',
            msg.role === 'user'
              ? 'bg-indigo-100 text-indigo-600'
              : 'bg-gray-100 text-gray-500'
          ]"
        >
          {{ msg.role === 'user' ? 'U' : 'AI' }}
        </div>

        <!-- 内容 -->
        <div class="max-w-[75%] space-y-2">
          <div
            :class="[
              'rounded-2xl px-4 py-3 leading-relaxed',
              msg.role === 'user'
                ? 'bg-indigo-500 text-white rounded-tr-md'
                : 'bg-gray-50 text-gray-700 rounded-tl-md'
            ]"
          >
            <p class="whitespace-pre-wrap text-sm">{{ msg.content || '...' }}</p>
          </div>

          <!-- 来源引用 -->
          <div v-if="msg.role === 'assistant' && msg.sources?.length" class="px-1">
            <button
              @click="toggleSources(i)"
              class="text-xs text-gray-400 hover:text-indigo-500 transition-colors"
            >
              {{ msg.sources.length }} 个引用来源
              <span class="ml-1">{{ expandedSources.has(i) ? '▲' : '▼' }}</span>
            </button>
            <div v-if="expandedSources.has(i)" class="mt-2 space-y-2">
              <SourceCard v-for="(s, j) in msg.sources" :key="j" :source="s" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, reactive } from 'vue'
import type { Message } from '../../types'
import SourceCard from './SourceCard.vue'

const props = defineProps<{ messages: Message[] }>()
const scrollRef = ref<HTMLElement | null>(null)
const expandedSources = reactive(new Set<number>())

function toggleSources(i: number) {
  if (expandedSources.has(i)) expandedSources.delete(i)
  else expandedSources.add(i)
}

// 自动滚动
watch(
  () => props.messages.map(m => m.content).join(''),
  () => nextTick(() => scrollRef.value?.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })),
  { flush: 'post' },
)
</script>
