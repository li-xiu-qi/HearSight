import type { 
  JobResponse, 
  TranscriptsResponse, 
  JobsResponse, 
  TranscriptDetailResponse, 
  SummarizeResponse,
  Segment 
} from '../types'

/**
 * 创建任务
 */
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

/**
 * 获取已处理的转写记录列表
 */
export const fetchTranscripts = async (limit = 50, offset = 0): Promise<TranscriptsResponse> => {
  const response = await fetch(`/api/transcripts?limit=${limit}&offset=${offset}`)
  
  if (!response.ok) {
    throw new Error(`获取列表失败：${response.status}`)
  }
  
  return response.json()
}

/**
 * 获取任务队列
 */
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
  
  // 去重并按 id 升序/创建时间升序方便观察排队
  const map = new Map()
  for (const item of items) {
    map.set(Number(item.id), item)
  }
  const sortedItems = Array.from(map.values()).sort((a, b) => Number(a.id) - Number(b.id))
  
  return { items: sortedItems }
}

/**
 * 获取转写记录详情
 */
export const fetchTranscriptDetail = async (id: number): Promise<TranscriptDetailResponse> => {
  const response = await fetch(`/api/transcripts/${id}`)
  
  if (!response.ok) {
    throw new Error(`获取详情失败：${response.status}`)
  }
  
  return response.json()
}

/**
 * 生成总结
 */
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

/**
 * 删除转写记录（同时删除视频文件和数据库记录）
 */
export const deleteTranscriptComplete = async (transcriptId: number): Promise<{ success: boolean; message: string }> => {
  console.log('调用 deleteTranscriptComplete API:', transcriptId)
  
  const url = `/api/transcripts/${transcriptId}`
  console.log('请求 URL:', url)
  console.log('请求方法: DELETE')
  
  const requestOptions = {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json'
    }
  }
  console.log('请求配置:', requestOptions)
  
  const response = await fetch(url, requestOptions)
  
  console.log('响应状态:', response.status, response.statusText)
  console.log('响应headers:', [...response.headers.entries()])
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('删除请求失败:', { status: response.status, statusText: response.statusText, body: errorText })
    throw new Error(`删除失败：${response.status} - ${response.statusText}`)
  }
  
  const result = await response.json()
  console.log('删除响应结果:', result)
  return result
}