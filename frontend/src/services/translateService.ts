import type { 
  Segment
} from '../types'

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
  forceRetranslate: boolean = false,
  sourceLanguage?: string,
  sourceLangDisplayName?: string,
  targetLangDisplayName?: string
): Promise<TranslateResponse> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_lang_code: targetLanguage,
      source_lang_code: sourceLanguage,
      confirmed: true,
      max_tokens: maxTokens,
      source_lang_display_name: sourceLangDisplayName,
      target_lang_display_name: targetLangDisplayName,
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
  forceRetranslate: boolean = false,
  sourceLanguage?: string,
  sourceLangDisplayName?: string,
  targetLangDisplayName?: string
): Promise<{ status: string; transcript_id: number; total_count: number }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_lang_code: targetLanguage,
      source_lang_code: sourceLanguage,
      confirmed: true,
      max_tokens: maxTokens,
      source_lang_display_name: sourceLangDisplayName,
      target_lang_display_name: targetLangDisplayName,
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
  return new Promise((resolve, reject) => {
    (async () => {
      try {
        await startTranslate(transcriptId, targetLanguage, maxTokens, forceRetranslate)

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
              resolve()
            } else if (progress.status === 'error') {
              onProgress({
                type: 'error',
                message: progress.message
              })
              clearInterval(pollInterval)
              reject(new Error(progress.message))
            }
          } catch (err) {
            console.error('轮询进度时出错:', err)
            clearInterval(pollInterval)
            reject(err)
          }
        }, 5000)
      } catch (err) {
        reject(err)
      }
    })()
  })
}

export const getTranslations = async (
  transcriptId: number
): Promise<{ translations: Record<string, Segment[]> | null; has_translations: boolean }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/translations`)

  if (!response.ok) {
    throw new Error(`获取已保存翻译失败：${response.status}`)
  }

  return response.json()
}