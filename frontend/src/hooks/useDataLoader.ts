import { useState, useEffect, useCallback } from 'react'
import { fetchJobs, fetchTranscripts, fetchTranscriptDetail, getTaskProgress } from '../services/api'
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

  const loadTranscripts = useCallback(async () => {
    try {
      const data = await fetchTranscripts()
      setTranscripts(Array.isArray(data.items) ? data.items : [])
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      console.error('获取转写记录失败:', errorMessage)
    }
  }, [])

  const loadJobs = async () => {
    try {
      const data = await fetchJobs()
      setJobs(data.items)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      console.warn('获取任务队列失败:', errorMessage)
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

  // 统一轮询任务进度和状态（避免两个轮询冲突）
  useEffect(() => {
    let prevSuccessfulJobs = new Set<number>()

    const pollJobsProgress = async () => {
      try {
        // 获取所有任务
        const data = await fetchJobs()
        const updatedJobs = Array.isArray(data.items) ? [...data.items] : []
        
        // 检测任务完成状态变化，重新加载transcripts
        const currentSuccessJobs = new Set(
          updatedJobs
            .filter(job => job.status === 'success')
            .map(job => job.id)
        )

        for (const jobId of currentSuccessJobs) {
          if (!prevSuccessfulJobs.has(jobId)) {
            // 任务新完成时，重新加载转录列表
            loadTranscripts()
            break
          }
        }

        prevSuccessfulJobs = currentSuccessJobs
        
        // 仅对处于 downloading 或 processing 状态的任务，获取详细进度信息
        const progressUpdates = await Promise.all(
          updatedJobs.map(async (job) => {
            if (job.status === 'downloading' || job.status === 'processing') {
              try {
                const progress = await getTaskProgress(job.id)
                return { jobId: job.id, progress }
              } catch (err) {
                console.debug(`获取任务 ${job.id} 的进度失败:`, err)
                return { jobId: job.id, progress: null }
              }
            }
            return { jobId: job.id, progress: null }
          })
        )
        
        // 合并进度信息到任务中
        const progressMap = new Map(
          progressUpdates
            .filter(u => u.progress !== null)
            .map(u => [u.jobId, u.progress])
        )
        
        const jobsWithProgress = updatedJobs.map(job => ({
          ...job,
          progress: progressMap.get(job.id)
        }))
        
        setJobs(jobsWithProgress)
      } catch (err) {
        console.debug('轮询任务进度时出错:', err)
      }
    }

    // 初始加载一次
    pollJobsProgress()
    
    // 之后每 1 秒轮询一次，以获得实时的进度更新
    const timer = setInterval(pollJobsProgress, 1000)
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
