import { useCallback, useState } from 'react'
import { translateTranscriptStream, getTranslations } from '../../../services/translateService'
import { fetchTranscriptDetail } from '../../../services/transcriptService'
import { toast } from 'sonner'
import type { TranslateProgress } from '../types'
import type { Segment } from '../../../types'

export const useTranslateHandlers = (
  onTranslateComplete?: () => void,
  onSegmentsUpdate?: (segments: Segment[], targetLanguage: string) => void
) => {
  const [translateProgress, setTranslateProgress] = useState<TranslateProgress>({
    status: 'idle',
    progress: 0,
    message: '',
  })
  const [showProgressPanel, setShowProgressPanel] = useState(false)
  const [hasSavedTranslations, setHasSavedTranslations] = useState(false)
  const [savedLanguages, setSavedLanguages] = useState<string[]>([])

  const handleStartTranslate = useCallback(
    async (transcriptId: number | undefined, targetLanguage: string, forceRetranslate: boolean = false) => {
      if (!transcriptId) return

      const progressMessage = forceRetranslate ? '强制重新翻译中，请稍候...' : '翻译中，请稍候...'
      
      setTranslateProgress({
        status: 'translating',
        progress: 0,
        message: progressMessage,
        targetLanguage,
      })
      setShowProgressPanel(true)

      try {
        await translateTranscriptStream(
          transcriptId,
          targetLanguage as 'zh' | 'en',
          4096,
          async (event) => {
            if (event.type === 'progress') {
              setTranslateProgress((prev) => ({
                ...prev,
                status: 'translating',
                progress: event.progress || 0,
                message: `翻译进度：${event.translated_count}/${event.total_count}`,
              }))
            } else if (event.type === 'complete') {
              setTranslateProgress((prev) => ({
                ...prev,
                status: 'done',
                progress: 100,
                message: event.message || '翻译完成',
                targetLanguage,
              }))
              
              // 更新已保存翻译状态
              setHasSavedTranslations(true)
              setSavedLanguages(prev => {
                if (!prev.includes(targetLanguage)) {
                  return [...prev, targetLanguage]
                }
                return prev
              })
              
              toast.success(event.message || '翻译已保存')

              try {
                const detail = await fetchTranscriptDetail(transcriptId)
                onSegmentsUpdate?.(detail.segments, targetLanguage)
              } catch (err) {
                console.error('更新分段失败', err)
              }

              onTranslateComplete?.()
            } else if (event.type === 'error') {
              const errorMsg = event.message || '翻译失败'
              setTranslateProgress((prev) => ({
                ...prev,
                status: 'error',
                progress: 0,
                message: errorMsg,
              }))
              toast.error(`翻译失败：${errorMsg}`)
            }
          },
          forceRetranslate
        )
      } catch (err) {
        console.error('翻译出错', err)
        const errorMsg = (err as Error).message
        setTranslateProgress((prev) => ({
          ...prev,
          status: 'error',
          progress: 0,
          message: errorMsg,
        }))
        toast.error(`翻译失败：${errorMsg}`)
      }
    },
    [onTranslateComplete, onSegmentsUpdate]
  )

  const handleRetryTranslate = useCallback(
    (transcriptId: number | undefined) => {
      if (translateProgress.targetLanguage) {
        handleStartTranslate(transcriptId, translateProgress.targetLanguage)
      }
    },
    [translateProgress.targetLanguage, handleStartTranslate]
  )

  const loadSavedTranslations = useCallback(async (transcriptId: number) => {
    try {
      const result = await getTranslations(transcriptId)
      setHasSavedTranslations(result.has_translations)
      if (result.translations) {
        setSavedLanguages(Object.keys(result.translations))
      } else {
        setSavedLanguages([])
      }
    } catch (err) {
      console.error('加载已保存翻译失败', err)
    }
  }, [])

  return {
    translateProgress,
    showProgressPanel,
    setShowProgressPanel,
    handleStartTranslate,
    handleRetryTranslate,
    hasSavedTranslations,
    savedLanguages,
    loadSavedTranslations,
  }
}

