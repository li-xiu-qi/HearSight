import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import type { JobItem } from '../../types'
import { extractFilename } from '../../utils'
import ProgressCard from '../ProgressCard'

interface TasksTabProps {
  readonly jobs: JobItem[]
}

function TasksTab({ jobs }: TasksTabProps) {

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'downloading':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
      case 'processing':
        return <Loader2 className="h-3 w-3 animate-spin text-purple-600" />
      case 'success':
        return <CheckCircle2 className="h-3 w-3 text-green-600" />
      case 'failed':
        return <XCircle className="h-3 w-3 text-red-600" />
      default:
        return <Clock className="h-3 w-3 text-slate-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'bg-blue-100 text-blue-700'
      case 'processing':
        return 'bg-purple-100 text-purple-700'
      case 'success':
        return 'bg-green-100 text-green-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-100 text-slate-600'
    }
  }
  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <Clock className="h-12 w-12 text-slate-300 mb-4" />
        <div className="text-base font-medium text-slate-700 mb-2">暂无处理任务</div>
        <div className="text-sm text-slate-500">
          当前没有正在处理的视频。提交视频URL后，处理进度会显示在这里。
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2">
        {jobs.map((item) => {
          const shortUrl = (item.url || '').replace(/^https?:\/\//, '')
          const filename = item.progress?.filename || extractFilename(item.url || '') || `任务 #${item.id}`
          
          // 对于下载中或处理中的任务，显示进度卡片
          if (item.status === 'downloading' || item.status === 'processing') {
            return (
              <ProgressCard
                key={item.id}
                filename={filename}
                progress={item.progress || {
                  stage: item.status === 'downloading' ? 'downloading' : 'processing',
                  status: 'in-progress',
                  progress_percent: 0,
                  filename: filename,
                  timestamp: new Date().toISOString(),
                }}
              />
            )
          }
          
          // 对于已完成或失败的任务，显示普通卡片
          return (
            <div
              key={item.id}
              className="p-3 rounded-lg border border-slate-200 bg-white"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div 
                    className="text-sm font-medium text-slate-900 line-clamp-2" 
                    title={item.url}
                  >
                    {shortUrl}
                  </div>
                  <div className="text-xs text-slate-500 mt-1 line-clamp-1">
                    # {item.id} · {item.created_at || item.started_at || ''}
                  </div>
                </div>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.status)}`}>
                  {getStatusIcon(item.status)}
                  {item.status}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </ScrollArea>
  )
}

export default TasksTab
