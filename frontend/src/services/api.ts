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
  const [pendingResponse, runningResponse] = await Promise.all([
    fetch('/api/jobs?status=pending&limit=50&offset=0'),
    fetch('/api/jobs?status=running&limit=50&offset=0'),
  ])
  
  if (!pendingResponse.ok) {
    throw new Error(`获取待处理任务失败：${pendingResponse.status}`)
  }
  if (!runningResponse.ok) {
    throw new Error(`获取进行中任务失败：${runningResponse.status}`)
  }
  
  const [pendingJobs, runningJobs] = await Promise.all([
    pendingResponse.json(),
    runningResponse.json()
  ])
  
  const items = [
    ...(Array.isArray(pendingJobs.items) ? pendingJobs.items : []),
    ...(Array.isArray(runningJobs.items) ? runningJobs.items : []),
  ]
  
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
    throw new Error(`summarize failed: ${response.status}`)
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
    const errorText = await response.text()
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
    throw new Error(`chat failed: ${response.status}`)
  }
  
  return response.json()
}
