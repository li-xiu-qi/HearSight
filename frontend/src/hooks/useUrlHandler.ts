import { useState } from 'react'
import { message } from '../utils/message'
import { createJob, startDownload } from '../services/api'
import { parseBilibiliUrl } from '../utils'
import type { ParseResult } from '../types'

interface UseUrlHandlerReturn {
  url: string
  setUrl: (url: string) => void
  urlError: string | null
  setUrlError: (error: string | null) => void
  urlResult: ParseResult | null
  setUrlResult: (result: ParseResult | null) => void
  submitting: boolean
  handleUrlSubmit: (url: string) => Promise<void>
  handleUrlClear: () => void
}

export const useUrlHandler = (): UseUrlHandlerReturn => {
  const [url, setUrl] = useState('')
  const [urlError, setUrlError] = useState<string | null>(null)
  const [urlResult, setUrlResult] = useState<ParseResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleUrlSubmit = async (urlToSubmit: string): Promise<void> => {
    setUrlError(null)
    setUrlResult(null)
    
    const parsed = parseBilibiliUrl(urlToSubmit)
    if ('error' in parsed) {
      setUrlError(parsed.error)
      setUrlResult(parsed)
      throw new Error(parsed.error)
    } else {
      setUrlResult(parsed)
      try {
        setSubmitting(true)
        const data = await createJob(urlToSubmit)
        if (data && typeof data.job_id === 'number') {
          message.success(`任务已创建：#${data.job_id}`)
          
          // 创建任务后立即启动下载
          try {
            await startDownload(urlToSubmit, data.job_id)
            message.info('下载已启动，请在处理情况页面查看进度')
          } catch (downloadErr: unknown) {
            const errorMessage = downloadErr instanceof Error ? downloadErr.message : '未知错误'
            message.warning(`下载启动失败: ${errorMessage}`)
          }
        } else {
          message.warning('任务创建返回异常')
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : '创建任务出错'
        setUrlError(errorMessage)
        message.error(errorMessage)
        throw e
      } finally {
        setSubmitting(false)
      }
    }
  }

  const handleUrlClear = () => {
    setUrl('')
    setUrlError(null)
    setUrlResult(null)
  }

  return {
    url,
    setUrl,
    urlError,
    setUrlError,
    urlResult,
    setUrlResult,
    submitting,
    handleUrlSubmit,
    handleUrlClear
  }
}
