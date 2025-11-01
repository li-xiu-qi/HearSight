import { useCallback, useState } from 'react'
import type { Segment, Summary } from '../../../types'
import { generateSummary } from '../../../services/api'

export const useSummaryHandlers = () => {
  const [summaries, setSummaries] = useState<Summary[]>([])
  const [summariesLoading, setSummariesLoading] = useState(false)
  const [summariesError, setSummariesError] = useState<string | null>(null)

  const handleGenerateSummary = useCallback(async (segments: Segment[]) => {
    setSummariesError(null)
    setSummaries([])

    if (segments.length === 0) {
      setSummariesError('没有可用分句')
      return
    }

    setSummariesLoading(true)
    try {
      const data = await generateSummary(segments)
      const items = Array.isArray(data.summaries) ? data.summaries : []
      setSummaries(items)
    } catch (err: unknown) {
      setSummariesError((err as Error)?.message || '调用总结接口失败')
    } finally {
      setSummariesLoading(false)
    }
  }, [])

  return {
    summaries,
    summariesLoading,
    summariesError,
    handleGenerateSummary,
  }
}
