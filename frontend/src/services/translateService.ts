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
  // 启动异步翻译任务
  await startTranslate(transcriptId, targetLanguage, maxTokens, forceRetranslate, sourceLanguage, sourceLangDisplayName, targetLangDisplayName)

  // 使用SSE等待翻译完成
  return new Promise((resolve, reject) => {
    translateTranscriptStream(
      transcriptId,
      targetLanguage,
      maxTokens,
      async (event) => {
        if (event.type === 'complete') {
          // 获取翻译结果
          const translations = await getTranslations(transcriptId)
          if (translations.translations && translations.translations[targetLanguage]) {
            resolve({
              status: 'completed',
              updated_segments: translations.translations[targetLanguage],
              new_transcript_id: transcriptId,
              message: '翻译完成'
            })
          } else {
            reject(new Error('无法获取翻译结果'))
          }
        } else if (event.type === 'error') {
          reject(new Error(event.message || '翻译失败'))
        }
      },
      forceRetranslate
    ).catch(reject)

    // 设置超时（5分钟）
    setTimeout(() => {
      reject(new Error('翻译超时'))
    }, 5 * 60 * 1000)
  })
}

export const startTranslate = async (
  transcriptId: number,
  targetLanguage: string = 'zh',
  maxTokens: number = 4096,
  forceRetranslate: boolean = false,
  sourceLanguage?: string,
  sourceLangDisplayName?: string,
  targetLangDisplayName?: string
): Promise<{ status: string; transcript_id: number }> => {
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
    throw new Error(`启动翻译失败：${response.status}`)
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
        // 启动异步翻译任务
        await startTranslate(transcriptId, targetLanguage, maxTokens, forceRetranslate)

        // 连接SSE流
        const eventSource = new EventSource(`/api/transcripts/${transcriptId}/translate/stream`)

        eventSource.onmessage = (event) => {
          try {
            const data: TranslateProgressEvent = JSON.parse(event.data)

            if (data.type === 'progress') {
              onProgress({
                type: 'progress',
                progress: data.progress,
                translated_count: data.translated_count,
                total_count: data.total_count
              })
            } else if (data.type === 'complete') {
              onProgress({
                type: 'complete',
                status: 'completed',
                translated_count: data.translated_count,
                total_count: data.total_count,
                is_complete: true,
                message: data.message
              })
              eventSource.close()
              resolve()
            } else if (data.type === 'error') {
              onProgress({
                type: 'error',
                message: data.message
              })
              eventSource.close()
              reject(new Error(data.message))
            }
          } catch (error) {
            console.error('SSE消息解析错误:', error)
            eventSource.close()
            reject(error)
          }
        }

        eventSource.onerror = (error) => {
          console.error('SSE连接错误:', error)
          eventSource.close()
          reject(new Error('SSE连接失败'))
        }

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