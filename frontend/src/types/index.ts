// 分句数据类型
export interface Segment {
  index: number
  spk_id: string | null
  sentence: string
  start_time: number
  end_time: number
}

// 转写记录元数据
export interface TranscriptMeta {
  id: number
  media_path: string
  created_at: string
  segment_count: number
}

// 任务项类型
export interface JobItem {
  id: number
  url: string
  status: 'pending' | 'running' | 'success' | 'failed' | string
  created_at?: string | null
  started_at?: string | null
  finished_at?: string | null
  result?: any
  error?: string | null
}

// URL解析结果类型
export type ParseResult = 
  | { kind: 'BV' | 'av' | 'ep' | 'ss' | 'md'; id: string }
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
  media_path: string
  segments: Segment[]
}

export interface SummarizeResponse {
  summaries?: Summary[]
}

// 添加ChatResponse类型
export interface ChatResponse {
  answer: string
}
