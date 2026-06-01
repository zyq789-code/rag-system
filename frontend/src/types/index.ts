export interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  document_count: number
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  knowledge_base_id: string | null
  filename: string
  original_name: string
  file_type: string
  file_size: number
  status: string
  chunk_count: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceCitation[]
}

export interface SourceCitation {
  filename: string
  chunk_text: string
  score: number
}

export interface Conversation {
  id: string
  title: string | null
  kb_id: string | null
  created_at: string
  message_count: number
}

export interface ResumeResponse {
  id: string
  filename: string
  status: string
  analysis_result: any
  created_at: string
}
