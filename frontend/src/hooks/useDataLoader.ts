import { useState, useEffect, useCallback } from 'react'
import { fetchTranscripts, fetchTranscriptDetail } from '../services/api'
import { extractFilename } from '../utils'
import type { Segment, TranscriptMeta, JobItem } from '../types'

interface UseDataLoaderReturn {
  segments: Segment[]
  loading: boolean
  transcripts: TranscriptMeta[]
  jobs: JobItem[]
  videoSrc: string | null
  mediaType: string
  activeTranscriptId: number | null
  loadTranscripts: () => Promise<void>
  loadTranscriptDetail: (id: number) => Promise<void>
  setSegments: (segments: Segment[]) => void
  setVideoSrc: (src: string | null) => void
  setMediaType: (type: string) => void
  setActiveTranscriptId: (id: number | null) => void
}

export const useDataLoader = (): UseDataLoaderReturn => {
  const [segments, setSegments] = useState<Segment[]>([])
  const [loading, setLoading] = useState(false)
  const [transcripts, setTranscripts] = useState<TranscriptMeta[]>([])
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [mediaType, setMediaType] = useState<string>('video')
  const [activeTranscriptId, setActiveTranscriptId] = useState<number | null>(null)

  const loadTranscripts = useCallback(async () => {
    try {
      const data = await fetchTranscripts()
      setTranscripts(Array.isArray(data.items) ? data.items : [])
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      console.error('获取转写记录失败:', errorMessage)
    }
  }, [])

  const loadTranscriptDetail = async (id: number) => {
    try {
      setLoading(true)
      const data = await fetchTranscriptDetail(id)
      const basename = extractFilename(data.video_path || data.audio_path || '')
      if (basename) {
        setVideoSrc(`/static/${basename}`)
      }
      setMediaType(data.media_type || 'audio')
      setSegments(Array.isArray(data.segments) ? data.segments : [])
      setActiveTranscriptId(id)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      console.error('获取转写记录详情失败:', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 初始加载转写列表
  useEffect(() => {
    loadTranscripts()
  }, [loadTranscripts])

  // 监听SSE更新jobs
  useEffect(() => {
    const eventSource = new EventSource('/api/progress/stream-all')
    eventSource.onmessage = (evt) => {
      try {
        const progress = JSON.parse(evt.data)
        const jobId = progress.job_id
        setJobs(prev => {
          const idx = prev.findIndex(j => j.id === jobId)
          if (idx >= 0) {
            const newJobs = [...prev]
            newJobs[idx] = { ...newJobs[idx], status: (progress.status as any) || newJobs[idx].status, progress }
            return newJobs
          }
          // 若 job 不存在，插入新条目
          const url = (progress.url as string) || ''
          return [{ id: jobId, url, status: (progress.status as any) || 'processing', progress }, ...prev]
        })
      } catch (err) {
        console.debug('解析SSE事件出错', err)
      }
    }
    eventSource.onerror = (err) => {
      console.debug('SSE错误', err)
    }
    return () => {
      eventSource.close()
    }
  }, [])

  return {
    segments,
    loading,
    transcripts,
    jobs,
    videoSrc,
    mediaType,
    activeTranscriptId,
    loadTranscripts,
    loadTranscriptDetail,
    setSegments,
    setVideoSrc,
    setMediaType,
    setActiveTranscriptId
  }
}
