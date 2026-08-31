<template>
  <div class="min-h-screen flex items-center justify-center px-4" style="background: var(--color-sidebar-bg)">
    <div class="w-full max-w-sm">
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <div class="text-center mb-6">
          <div class="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-3">
            <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 class="text-xl font-semibold text-gray-800">RAG 知识库智能问答</h1>
          <p class="text-sm text-gray-400 mt-1">{{ isRegister ? '注册新账号' : '登录系统' }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1.5">用户名</label>
            <input
              v-model="username"
              autocomplete="username"
              class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300 transition-colors"
              placeholder="3-50 个字符"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1.5">密码</label>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300 transition-colors"
              placeholder="至少 6 位"
            />
          </div>
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          <button
            type="submit"
            :disabled="loading || !username.trim() || !password"
            class="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium transition-all shadow-sm hover:shadow"
          >
            {{ loading ? '请稍候...' : (isRegister ? '注册并登录' : '登录') }}
          </button>
        </form>

        <p class="text-center text-sm text-gray-400 mt-5">
          {{ isRegister ? '已有账号？' : '还没有账号？' }}
          <button @click="isRegister = !isRegister" class="text-indigo-600 hover:text-indigo-700 font-medium">
            {{ isRegister ? '去登录' : '去注册' }}
          </button>
        </p>
      </div>
      <p class="text-center text-xs text-white/30 mt-4">个人知识库 · 聊天记录按用户隔离</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!username.value.trim() || !password.value) return
  error.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register(username.value.trim(), password.value)
    } else {
      await auth.login(username.value.trim(), password.value)
    }
    router.push((route.query.redirect as string) || '/chat')
  } catch (e: any) {
    error.value = e?.response?.data?.error || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
