import type { 
  TranscriptsResponse, 
  TranscriptDetailResponse,
  Segment
} from '../types'

export const fetchTranscripts = async (limit = 50, offset = 0): Promise<TranscriptsResponse> => {
  const response = await fetch(`/api/transcripts?limit=${limit}&offset=${offset}`)
  
  if (!response.ok) {
    throw new Error(`获取列表失败：${response.status}`)
  }
  
  return response.json()
}

export const fetchTranscriptDetail = async (id: number): Promise<TranscriptDetailResponse> => {
  const response = await fetch(`/api/transcripts/${id}`)
  
  if (!response.ok) {
    throw new Error(`获取详情失败：${response.status}`)
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