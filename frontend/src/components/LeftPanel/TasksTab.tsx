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
          当前没有正在处理的媒体内容。提交视频或音频URL后，处理进度会显示在这里。
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-3 p-1">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="border rounded-lg p-3 bg-white shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                {getStatusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-900 truncate">
                    {extractFilename(job.url) || job.url}
                  </div>
                  <div className="text-xs text-slate-500">
                    ID: {job.id}
                  </div>
                </div>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                {job.status}
              </div>
            </div>

            {job.progress && (
              <ProgressCard
                filename={job.progress.filename}
                progress={job.progress}
              />
            )}

            {job.error && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                {job.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}

export default TasksTab