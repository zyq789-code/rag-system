import api from './client'
import type { ResumeResponse } from '../types'

export async function uploadResume(file: File): Promise<ResumeResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/resume/upload', form)
  return data
}

export async function getResume(id: string): Promise<ResumeResponse> {
  const { data } = await api.get(`/resume/${id}`)
  return data
}

export async function generateInterviewQuestions(id: string) {
  const { data } = await api.post(`/resume/${id}/interview`)
  return data
}
