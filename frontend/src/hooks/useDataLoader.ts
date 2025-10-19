import { useState, useEffect } from 'react'
import { fetchJobs, fetchTranscripts, fetchTranscriptDetail } from '../services/api'
import { extractFilename } from '../utils'
import type { Segment, TranscriptMeta, JobItem } from '../types'

interface UseDataLoaderReturn {
  segments: Segment[]
  loading: boolean
  transcripts: TranscriptMeta[]
  jobs: JobItem[]
  videoSrc: string | null
  activeTranscriptId: number | null
  loadTranscripts: () => Promise<void>
  loadJobs: () => Promise<void>
  loadTranscriptDetail: (id: number) => Promise<void>
  setSegments: (segments: Segment[]) => void
  setVideoSrc: (src: string | null) => void
  setActiveTranscriptId: (id: number | null) => void
}

export const useDataLoader = (): UseDataLoaderReturn => {
  const [segments, setSegments] = useState<Segment[]>([])
  const [loading, setLoading] = useState(false)
  const [transcripts, setTranscripts] = useState<TranscriptMeta[]>([])
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [activeTranscriptId, setActiveTranscriptId] = useState<number | null>(null)

  const loadTranscripts = async () => {
    try {
      const data = await fetchTranscripts()
      setTranscripts(Array.isArray(data.items) ? data.items : [])
    } catch (err: any) {
      console.error('获取转写记录失败:', err?.message || err)
    }
  }

  const loadJobs = async () => {
    try {
      const data = await fetchJobs()
      setJobs(data.items)
    } catch (err: any) {
      console.warn('获取任务队列失败:', err?.message || err)
    }
  }

  const loadTranscriptDetail = async (id: number) => {
    try {
      setLoading(true)
      const data = await fetchTranscriptDetail(id)
      const basename = extractFilename(data.media_path)
      if (basename) {
        setVideoSrc(`/static/${basename}`)
      }
      setSegments(Array.isArray(data.segments) ? data.segments : [])
      setActiveTranscriptId(id)
    } catch (err: any) {
      console.error('获取转写记录详情失败:', err?.message || err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTranscripts()
    const timer = setInterval(() => { loadTranscripts() }, 5000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    loadJobs()
    const timer = setInterval(() => { loadJobs() }, 5000)
    return () => clearInterval(timer)
  }, [])

  return {
    segments,
    loading,
    transcripts,
    jobs,
    videoSrc,
    activeTranscriptId,
    loadTranscripts,
    loadJobs,
    loadTranscriptDetail,
    setSegments,
    setVideoSrc,
    setActiveTranscriptId
  }
}
