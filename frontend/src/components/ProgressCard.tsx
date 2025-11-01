import { Loader2, CheckCircle2, XCircle } from 'lucide-react'
import type { ProgressInfo } from '../types'

interface ProgressCardProps {
  filename: string
  progress: ProgressInfo
}

function ProgressCard({ filename, progress }: ProgressCardProps) {
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const formatTime = (seconds: number | null | undefined): string => {
    if (!seconds || seconds <= 0) return '计算中...'
    if (seconds < 60) return `${Math.round(seconds)}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${Math.round(seconds % 60)}秒`
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`
  }

  const stageLabel = {
    waiting: '等待中',
    upload: '已上传',
    download: '下载中',
    downloading: '下载中',
    asr: '语音识别中',
    processing: '处理中',
    completed: '已完成'
  }[progress.stage] || '处理中'

  const getStatusIcon = () => {
    switch (progress.status) {
      case 'in-progress':
      case 'ready':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case 'completed':
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <Loader2 className="h-4 w-4 text-slate-400" />
    }
  }

  return (
    <div className="p-3 rounded-lg border border-slate-200 bg-white space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-slate-900 line-clamp-1" title={filename}>
            {filename}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {stageLabel}
          </div>
        </div>
        <div className="ml-2">
          {getStatusIcon()}
        </div>
      </div>

      {/* 进度条 */}
      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600 rounded-full transition-all duration-300"
          style={{ width: `${Math.min(progress.progress_percent, 100)}%` }}
        />
      </div>

      <div className="text-xs text-slate-600 space-y-1">
        <div className="flex justify-between">
          <span>进度：{progress.progress_percent.toFixed(1)}%</span>
          {progress.current_bytes !== undefined && progress.total_bytes !== undefined && progress.total_bytes > 0 && (
            <span>{formatBytes(progress.current_bytes)} / {formatBytes(progress.total_bytes)}</span>
          )}
        </div>
        {progress.speed && progress.speed > 0 && (
          <div className="flex justify-between">
            <span>速度：{formatBytes(progress.speed)}/s</span>
            <span>预计：{formatTime(progress.eta_seconds)}</span>
          </div>
        )}
        {progress.message && (
          <div className="text-slate-600 mt-1">{progress.message}</div>
        )}
        {progress.error && (
          <div className="text-red-600">{progress.error}</div>
        )}
      </div>
    </div>
  )
}

export default ProgressCard
