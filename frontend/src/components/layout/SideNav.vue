<template>
  <!-- 桌面侧边栏（md 及以上） -->
  <aside class="hidden md:flex w-64 flex-shrink-0 flex-col h-screen" style="background: var(--color-sidebar-bg)">
    <!-- Logo -->
    <div class="px-5 h-16 flex items-center gap-3 border-b border-white/10">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      </div>
      <div>
        <div class="text-sm font-semibold text-white" style="font-family: var(--font-heading)">RAG 知识库</div>
        <div class="text-xs text-white/40">智能问答系统</div>
      </div>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 px-3 py-4 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
        :class="$route.path === item.path
          ? 'text-white shadow-sm' + getActiveBg(item.color)
          : 'text-white/60 hover:text-white hover:bg-white/5'"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- 底部 -->
    <div class="px-4 py-4 border-t border-white/10">
      <div class="flex items-center gap-3 text-xs text-white/30">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div>
        <span>系统在线</span>
      </div>
    </div>
  </aside>

  <!-- 手机底部导航（md 以下） -->
  <nav
    class="md:hidden fixed bottom-0 inset-x-0 z-40 flex bg-white border-t border-gray-200 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]"
    style="padding-bottom: env(safe-area-inset-bottom)"
  >
    <router-link
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="flex-1 flex flex-col items-center justify-center py-2.5 text-[11px] font-medium transition-colors"
      :class="$route.path === item.path ? 'text-indigo-600' : 'text-gray-400'"
    >
      <component :is="item.icon" class="w-5 h-5 mb-0.5" />
      <span>{{ item.label }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
import { MessageSquare, FileText, BookOpen, User } from 'lucide-vue-next'

const navItems = [
  { path: '/chat', label: '智能问答', icon: MessageSquare, color: 'indigo' },
  { path: '/documents', label: '文档管理', icon: FileText, color: 'blue' },
  { path: '/knowledge', label: '知识库', icon: BookOpen, color: 'violet' },
  { path: '/resume', label: '简历分析', icon: User, color: 'sky' },
]

function getActiveBg(color: string) {
  const colors: Record<string, string> = {
    indigo: ' bg-indigo-500/20',
    blue: ' bg-blue-500/20',
    violet: ' bg-violet-500/20',
    sky: ' bg-sky-500/20',
  }
  return colors[color] || ' bg-indigo-500/20'
}
</script>
