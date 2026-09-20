/** 与后端 PG 时代的 schemas.py 对齐的领域类型 */

export interface Segment {
  index: number
  sentence: string
  start_time: number // 毫秒
  end_time: number // 毫秒
  spk_id?: string | null
  translation?: Record<string, string> | null
}

export interface SummaryItem {
  topic: string
  summary: string
  start_time: number
  end_time: number
}

export interface TranslationEntry {
  index: number
  sentence: string
  translation: string
  start_time: number
  end_time: number
}

export interface TranscriptMeta {
  id: number
  audio_path: string
  video_path: string | null
  media_type: string
  created_at: string
  segment_count: number
  /** 展示名（文件名去扩展名）。原后端不返回，聊天/列表按 basename 派生 */
  title?: string
}

export interface TranscriptDetail {
  id: number
  audio_path: string
  video_path: string | null
  media_type: string
  created_at: string
  segments: Segment[]
  summaries: SummaryItem[] | null
  translations: Record<string, TranslationEntry[]> | null
}

export interface ProgressInfo {
  job_id: number | string
  status: string // idle | ready | in-progress | processing | completed | success | failed
  stage: string
  progress_percent: number
  filename?: string
  current_bytes?: number
  total_bytes?: number
  speed?: number
  eta_seconds?: number | null
  message?: string
  error?: string
  timestamp?: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: number // epoch ms
}
