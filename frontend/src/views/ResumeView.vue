<template>
  <div class="max-w-5xl mx-auto px-6 py-8 space-y-6">
    <h1 class="page-title">简历分析</h1>

    <ResumeUpload @upload="handleUpload" />

    <div v-if="isLoading" class="flex items-center justify-center gap-3 py-12">
      <svg class="animate-spin h-5 w-5 text-indigo-500" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
      <span class="text-sm text-gray-400">AI 正在分析简历...</span>
    </div>

    <div v-if="error" class="card p-6 flex items-center gap-3 text-red-600 bg-red-50 border-red-100">
      <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span class="text-sm">{{ error }}</span>
    </div>

    <AnalysisView v-if="resume && !isLoading" :result="resume.analysis_result" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import * as resumeApi from '../api/resume'
import type { ResumeResponse } from '../types'
import ResumeUpload from '../components/resume/ResumeUpload.vue'
import AnalysisView from '../components/resume/AnalysisView.vue'

const isLoading = ref(false)
const resume = ref<ResumeResponse | null>(null)
const error = ref<string | null>(null)

async function handleUpload(file: File) {
  isLoading.value = true
  error.value = null
  resume.value = null
  try {
    const result = await resumeApi.uploadResume(file)
    resume.value = await resumeApi.getResume(result.id)
  } catch (e: any) {
    error.value = e?.message || '分析失败，请重试'
  } finally { isLoading.value = false }
}
</script>
