import { useCallback, useState } from 'react'
import type { Segment, Summary } from '../../../types'
import { generateSummary, saveSummaries, getSummaries } from '../../../services/api'

export const useSummaryHandlers = () => {
  const [summaries, setSummaries] = useState<Summary[]>([])
  const [summariesLoading, setSummariesLoading] = useState(false)
  const [summariesError, setSummariesError] = useState<string | null>(null)
  const [hasSavedSummaries, setHasSavedSummaries] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const handleGenerateSummary = useCallback(async (segments: Segment[], transcriptId: number) => {
    setSummariesError(null)
    setSummaries([])
    setHasSavedSummaries(false)

    if (segments.length === 0) {
      setSummariesError('没有可用分句')
      return
    }

    setSummariesLoading(true)
    try {
      const data = await generateSummary(segments)
      const items = Array.isArray(data.summaries) ? data.summaries : []
      setSummaries(items)

      // 生成完总结后自动保存到数据库
      if (items.length > 0 && transcriptId) {
        setIsSaving(true)
        try {
          const result = await saveSummaries(transcriptId, items)
          if (result.success) {
            setHasSavedSummaries(true)
          }
        } catch (err: unknown) {
          console.error('自动保存总结失败:', err)
          // 不中断流程，即使保存失败也允许用户看到总结
        } finally {
          setIsSaving(false)
        }
      }
    } catch (err: unknown) {
      setSummariesError((err as Error)?.message || '调用总结接口失败')
    } finally {
      setSummariesLoading(false)
    }
  }, [])

  const handleSaveSummaries = useCallback(async (transcriptId: number, summariesToSave: Summary[]) => {
    setIsSaving(true)
    try {
      const result = await saveSummaries(transcriptId, summariesToSave)
      if (result.success) {
        setHasSavedSummaries(true)
      }
      return result
    } catch (err: unknown) {
      setSummariesError((err as Error)?.message || '保存总结失败')
      throw err
    } finally {
      setIsSaving(false)
    }
  }, [])

  const handleLoadSavedSummaries = useCallback(async (transcriptId: number) => {
    setSummariesLoading(true)
    setSummariesError(null)
    try {
      const result = await getSummaries(transcriptId)
      if (result.has_summaries && result.summaries) {
        setSummaries(result.summaries)
        setHasSavedSummaries(true)
      } else {
        setSummaries([])
        setHasSavedSummaries(false)
      }
    } catch (err: unknown) {
      setSummariesError((err as Error)?.message || '加载已保存总结失败')
      setSummaries([])
    } finally {
      setSummariesLoading(false)
    }
  }, [])

  return {
    summaries,
    summariesLoading,
    summariesError,
    handleGenerateSummary,
    handleSaveSummaries,
    handleLoadSavedSummaries,
    hasSavedSummaries,
    isSaving,
  }
}

