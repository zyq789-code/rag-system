<template>
  <div v-if="result" class="space-y-6">

    <!-- 综合评分 -->
    <div class="card p-6">
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-200">
          <span class="text-2xl font-bold text-white" style="font-family: var(--font-heading)">{{ result.overall_score ?? '-' }}</span>
        </div>
        <div>
          <h3 class="font-semibold text-gray-800">综合评分</h3>
          <p class="text-sm text-gray-500 mt-1">{{ result.summary }}</p>
        </div>
      </div>
    </div>

    <!-- 技能评估 -->
    <div v-if="result.skills?.length" class="card p-6">
      <h3 class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
        技能评估
      </h3>
      <div class="grid grid-cols-2 gap-3">
        <div v-for="skill in result.skills" :key="skill.name" class="flex items-center justify-between px-4 py-2.5 bg-gray-50 rounded-lg">
          <span class="text-sm font-medium text-gray-700">{{ skill.name }}</span>
          <span :class="[
            'text-xs px-2.5 py-0.5 rounded-full font-medium',
            skill.level === 'expert' ? 'bg-emerald-100 text-emerald-700' :
            skill.level === 'intermediate' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-200 text-gray-600'
          ]">{{ { expert: '精通', intermediate: '熟练', beginner: '入门' }[skill.level] || skill.level }}</span>
        </div>
      </div>
    </div>

    <!-- 优势与待提升 -->
    <div class="grid grid-cols-2 gap-4">
      <div v-if="result.strengths?.length" class="card p-6 border-l-4 border-l-emerald-400">
        <h3 class="font-semibold text-emerald-700 mb-3 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
          优势
        </h3>
        <ul class="space-y-2">
          <li v-for="s in result.strengths" :key="s" class="text-sm text-emerald-600 flex items-start gap-2">
            <span class="mt-0.5 w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>
            {{ s }}
          </li>
        </ul>
      </div>
      <div v-if="result.gaps?.length" class="card p-6 border-l-4 border-l-amber-400">
        <h3 class="font-semibold text-amber-700 mb-3 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          待提升
        </h3>
        <ul class="space-y-2">
          <li v-for="g in result.gaps" :key="g" class="text-sm text-amber-600 flex items-start gap-2">
            <span class="mt-0.5 w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0"></span>
            {{ g }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 面试题 -->
    <div v-if="result.interview_questions?.length" class="card p-6">
      <h3 class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
        面试题
      </h3>
      <div class="space-y-3">
        <div v-for="(q, i) in result.interview_questions" :key="i" class="border border-gray-100 rounded-xl overflow-hidden">
          <div class="p-4 bg-gray-50/50">
            <div class="flex items-start justify-between gap-3">
              <p class="text-sm font-medium text-gray-800">{{ i + 1 }}. {{ q.question }}</p>
              <button @click="toggleAnswer(i)" class="flex-shrink-0 p-1.5 rounded-lg hover:bg-gray-200 transition-colors" :title="visibleAnswers.has(i) ? '隐藏答案' : '查看答案'">
                <svg v-if="visibleAnswers.has(i)" class="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                <svg v-else class="w-4 h-4 text-gray-400 hover:text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              </button>
            </div>
            <div class="flex flex-wrap gap-2 mt-2">
              <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">{{ q.category === 'technical' ? '技术' : q.category === 'behavioral' ? '行为' : '项目' }}</span>
              <span :class="[
                'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full',
                q.difficulty === 'hard' ? 'bg-red-50 text-red-600' :
                q.difficulty === 'medium' ? 'bg-yellow-50 text-yellow-600' :
                'bg-green-50 text-green-600'
              ]">{{ { hard: '困难', medium: '中等', easy: '简单' }[q.difficulty] || q.difficulty }}</span>
            </div>
          </div>
          <!-- 答案 -->
          <div v-if="visibleAnswers.has(i) && q.expected_points?.length" class="px-4 py-3 border-t border-gray-100 bg-white animate-fadeIn">
            <p class="text-xs font-medium text-gray-500 mb-2">参考要点：</p>
            <ul class="space-y-1.5">
              <li v-for="(pt, j) in q.expected_points" :key="j" class="text-sm text-gray-600 flex items-start gap-2">
                <span class="text-indigo-400 mt-0.5 flex-shrink-0">•</span>
                {{ pt }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
  <p v-else class="text-center text-gray-400 py-12">上传简历开始分析</p>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

defineProps<{ result: any }>()
const visibleAnswers = reactive(new Set<number>())

function toggleAnswer(i: number) {
  if (visibleAnswers.has(i)) visibleAnswers.delete(i)
  else visibleAnswers.add(i)
}
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.2s ease;
}
</style>
