import type { 
  JobResponse, 
  TranscriptsResponse, 
  JobsResponse, 
  TranscriptDetailResponse, 
  SummarizeResponse,
  Segment,
  ChatResponse
} from '../types'

export const createJob = async (url: string): Promise<JobResponse> => {
  const response = await fetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  })
  
  if (!response.ok) {
    throw new Error(`创建任务失败：${response.status}`)
  }
  
  return response.json()
}

export const fetchTranscripts = async (limit = 50, offset = 0): Promise<TranscriptsResponse> => {
  const response = await fetch(`/api/transcripts?limit=${limit}&offset=${offset}`)
  
  if (!response.ok) {
    throw new Error(`获取列表失败：${response.status}`)
  }
  
  return response.json()
}

export const fetchJobs = async (): Promise<JobsResponse> => {
  const results = await Promise.allSettled([
    fetch('/api/jobs?status=downloading&limit=50&offset=0'),
    fetch('/api/jobs?status=processing&limit=50&offset=0'),
  ])
  
  const items = []
  
  // 处理downloading任务
  if (results[0].status === 'fulfilled' && results[0].value.ok) {
    const data = await results[0].value.json()
    if (Array.isArray(data.items)) {
      items.push(...data.items)
    }
  }
  
  // 处理processing任务
  if (results[1].status === 'fulfilled' && results[1].value.ok) {
    const data = await results[1].value.json()
    if (Array.isArray(data.items)) {
      items.push(...data.items)
    }
  }
  
  const map = new Map()
  for (const item of items) {
    map.set(Number(item.id), item)
  }
  const sortedItems = Array.from(map.values()).sort((a, b) => Number(a.id) - Number(b.id))
  
  return { items: sortedItems }
}

export const fetchTranscriptDetail = async (id: number): Promise<TranscriptDetailResponse> => {
  const response = await fetch(`/api/transcripts/${id}`)
  
  if (!response.ok) {
    throw new Error(`获取详情失败：${response.status}`)
  }
  
  return response.json()
}

export const generateSummary = async (segments: Segment[]): Promise<SummarizeResponse> => {
  const response = await fetch('/api/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segments })
  })
  
  if (!response.ok) {
    throw new Error(`总结失败：${response.status}`)
  }
  
  return response.json()
}

export const deleteTranscriptComplete = async (transcriptId: number): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  
  if (!response.ok) {
    throw new Error(`删除失败：${response.status} - ${response.statusText}`)
  }
  
  return response.json()
}

export const chatWithSegments = async (segments: Segment[], question: string): Promise<ChatResponse> => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segments, question })
  })
  
  if (!response.ok) {
    throw new Error(`聊天失败：${response.status}`)
  }
  
  return response.json()
}
export interface TranslateResponse {
  status: string
  updated_segments: Segment[]
  new_transcript_id: number
  message: string
}

export interface TranslateProgressEvent {
  type: 'progress' | 'complete' | 'error'
  translated_count?: number
  total_count?: number
  progress?: number
  status?: string
  is_complete?: boolean
  message?: string
}

export const translateTranscript = async (
  transcriptId: number,
  targetLanguage: string = 'zh',
  maxTokens: number = 4096,
  forceRetranslate: boolean = false
): Promise<TranslateResponse> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_language: targetLanguage,
      confirmed: true,
      max_tokens: maxTokens,
      force_retranslate: forceRetranslate
    })
  })
  
  if (!response.ok) {
    throw new Error(`翻译失败：${response.status}`)
  }
  
  return response.json()
}

export const startTranslate = async (
  transcriptId: number,
  targetLanguage: string = 'zh',
  maxTokens: number = 4096,
  forceRetranslate: boolean = false
): Promise<{ status: string; transcript_id: number; total_count: number }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_language: targetLanguage,
      confirmed: true,
      max_tokens: maxTokens,
      force_retranslate: forceRetranslate
    })
  })
  
  if (!response.ok) {
    throw new Error(`翻译失败：${response.status}`)
  }
  
  return response.json()
}

export const getTranslateProgress = async (
  transcriptId: number
): Promise<{
  status: string
  progress: number
  translated_count: number
  total_count: number
  message: string
}> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translate-progress`)
  
  if (!response.ok) {
    throw new Error(`获取进度失败：${response.status}`)
  }
  
  return response.json()
}

export const translateTranscriptStream = async (
  transcriptId: number,
  targetLanguage: string = 'zh',
  maxTokens: number = 4096,
  onProgress: (event: TranslateProgressEvent) => void,
  forceRetranslate: boolean = false
): Promise<void> => {
  // 启动翻译任务
  await startTranslate(transcriptId, targetLanguage, maxTokens, forceRetranslate)
  
  // 轮询获取进度（每 5 秒查询一次）
  const pollInterval = setInterval(async () => {
    try {
      const progress = await getTranslateProgress(transcriptId)
      
      if (progress.status === 'translating') {
        onProgress({
          type: 'progress',
          progress: progress.progress,
          translated_count: progress.translated_count,
          total_count: progress.total_count
        })
      } else if (progress.status === 'completed') {
        onProgress({
          type: 'complete',
          status: 'completed',
          translated_count: progress.translated_count,
          total_count: progress.total_count,
          is_complete: true,
          message: progress.message
        })
        clearInterval(pollInterval)
      } else if (progress.status === 'error') {
        onProgress({
          type: 'error',
          message: progress.message
        })
        clearInterval(pollInterval)
      }
    } catch (err) {
      console.error('轮询进度时出错:', err)
      clearInterval(pollInterval)
    }
  }, 5000) // 每 5 秒查询一次进度
}

export const fetchThumbnail = async (
  transcriptId: number,
  startTime: number,
  endTime: number,
  width: number = 320
): Promise<string> => {
  const response = await fetch(
    `/api/thumbnails/${transcriptId}?start_time=${startTime}&end_time=${endTime}&width=${width}`
  )
  
  if (!response.ok) {
    throw new Error(`获取缩略图失败：${response.status}`)
  }
  
  const result = await response.json()
  if (!result.success || !result.data) {
    throw new Error('缩略图数据格式错误')
  }
  
  return result.data
}

export const getDownloadProgress = async (jobId: number) => {
  const response = await fetch(`/api/progress/download/${jobId}`)
  
  if (!response.ok) {
    throw new Error(`获取下载进度失败：${response.status}`)
  }
  
  return response.json()
}

export const getTaskProgress = async (jobId: number) => {
  const response = await fetch(`/api/progress/task/${jobId}`)
  
  if (!response.ok) {
    throw new Error(`获取任务进度失败：${response.status}`)
  }
  
  return response.json()
}

export const startDownload = async (
  url: string,
  jobId: number,
  sessdata?: string,
  playlist?: boolean,
  quality?: string
) => {
  const response = await fetch('/api/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      job_id: jobId,
      sessdata: sessdata || '',
      playlist: playlist || false,
      quality: quality || 'best',
      workers: 1,
    })
  })
  
  if (!response.ok) {
    throw new Error(`启动下载失败：${response.status}`)
  }
  
  return response.json()
}
