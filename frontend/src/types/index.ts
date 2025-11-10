// 分句数据类型
export interface Segment {
  index: number
  spk_id: string | null
  sentence: string
  start_time: number
  end_time: number
  translation?: { [language: string]: string } | null
}

// 转写记录元数据
export interface TranscriptMeta {
  id: number
  media_path: string
  media_type?: string
  created_at: string
  segment_count: number
}

// 下载/处理进度信息
export interface ProgressInfo {
  stage: 'waiting' | 'upload' | 'download' | 'downloading' | 'asr' | 'processing' | 'completed'
  status: 'idle' | 'ready' | 'in-progress' | 'completed' | 'failed' | 'success'
  progress_percent: number
  current_bytes?: number
  total_bytes?: number
  speed?: number
  eta_seconds?: number | null
  filename: string
  message?: string
  error?: string
  timestamp?: string
  job_id?: number
}

// 任务项类型
export interface JobItem {
  id: number
  url: string
  status: 'downloading' | 'processing' | 'success' | 'failed' | string
  created_at?: string | null
  started_at?: string | null
  finished_at?: string | null
  result?: unknown
  error?: string | null
  progress?: ProgressInfo
}

// URL解析结果类型
export type ParseResult = 
  | { kind: 'BV' | 'av' | 'ep' | 'ss' | 'md'; id: string }
  | { kind: 'url'; id: string; platform: string }
  | { error: string }

// 总结数据类型
export interface Summary {
  topic: string
  summary: string
  start_time?: number
  end_time?: number
}

// API响应类型
export interface JobResponse {
  job_id: number
}

export interface TranscriptsResponse {
  items: TranscriptMeta[]
}

export interface JobsResponse {
  items: JobItem[]
}

export interface TranscriptDetailResponse {
  id?: number
  media_path: string
  media_type?: string
  segments: Segment[]
  summaries?: Summary[] | null
  translations?: Record<string, Translation[]> | null
}

// 翻译数据类型
export interface Translation {
  index: number
  sentence: string
  translation: string
  start_time?: number
  end_time?: number
}

// 保存总结响应类型
export interface SaveSummariesResponse {
  success: boolean
  message: string
  saved: boolean
  transcript_id: number
}

// 获取已保存总结响应类型
export interface GetSummariesResponse {
  summaries?: Summary[] | null
  has_summaries: boolean
}

// 获取已保存翻译响应类型
export interface GetTranslationsResponse {
  translations?: Record<string, Translation[]> | null
  has_translations: boolean
}

export interface SummarizeResponse {
  summaries?: Summary[]
}

// 添加ChatResponse类型
export interface ChatResponse {
  answer: string
}

// Chat消息类型
export interface ChatMessage {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: number
}
