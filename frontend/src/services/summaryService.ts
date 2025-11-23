import type { 
  SummarizeResponse,
  Segment,
  Summary
} from '../types'

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

export const saveSummaries = async (
  transcriptId: number,
  summaries: Summary[]
): Promise<{ success: boolean; message: string; saved: boolean; transcript_id: number }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/summaries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ summaries })
  })

  if (!response.ok) {
    throw new Error(`保存总结失败：${response.status}`)
  }

  return response.json()
}

export const getSummaries = async (
  transcriptId: number
): Promise<{ summaries: Summary[] | null; has_summaries: boolean }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/summaries`)

  if (!response.ok) {
    throw new Error(`获取已保存总结失败：${response.status}`)
  }

  return response.json()
}