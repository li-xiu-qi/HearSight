'use client'

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
        return <Loader2 className="h-3 w-3 animate-spin text-primary" />
      case 'processing':
        return <Loader2 className="h-3 w-3 animate-spin text-primary" />
      case 'success':
        return <CheckCircle2 className="h-3 w-3 text-success" />
      case 'failed':
        return <XCircle className="h-3 w-3 text-destructive" />
      default:
        return <Clock className="h-3 w-3 text-muted-foreground" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'downloading':
        return 'bg-primary/10 text-primary'
      case 'processing':
        return 'bg-primary/10 text-primary'
      case 'success':
        return 'bg-success/10 text-success'
      case 'failed':
        return 'bg-destructive/10 text-destructive'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  if (jobs.length === 0) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between px-4 pt-4 pb-2 flex-shrink-0">
          <div className="text-xs font-medium text-muted-foreground tracking-wide">处理任务</div>
        </div>
        <div className="flex flex-col items-center justify-center flex-1 text-center px-8">
          <Clock className="h-10 w-10 text-muted-foreground mb-3" />
          <div className="text-sm font-medium text-foreground mb-1">暂无处理任务</div>
          <div className="text-xs text-muted-foreground leading-5">
            提交链接或上传文件后，处理进度会显示在这里
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 pt-4 pb-2 flex-shrink-0">
        <div className="text-xs font-medium text-muted-foreground tracking-wide">处理任务</div>
        <div className="text-xs text-muted-foreground">{jobs.length} 条</div>
      </div>
      <ScrollArea className="h-full flex-1">
        <div className="space-y-3 px-3 pb-2">
        {jobs.map((job) => (
          <div
            key={job.id}
            className="border border-border rounded-lg p-3 bg-card shadow-xs"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                {getStatusIcon(job.status)}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-foreground truncate">
                    {extractFilename(job.url) || job.url}
                  </div>
                  <div className="text-xs text-muted-foreground">
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
              <div className="mt-2 p-2 bg-destructive/10 border border-destructive/30 rounded text-xs text-destructive">
                {job.error}
              </div>
            )}
          </div>
        ))}
        </div>
      </ScrollArea>
    </div>
  )
}

export default TasksTab