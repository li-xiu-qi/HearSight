'use client'

import type { TranscriptMeta, JobItem } from '../../types'
import type { LeftView } from '@/features/app/components/AppLayout'
import ProcessedTab from './ProcessedTab'
import TasksTab from './TasksTab'

interface LeftPanelProps {
  readonly view: LeftView
  readonly transcripts: TranscriptMeta[]
  readonly jobs: JobItem[]
  readonly activeTranscriptId: number | null
  readonly onLoadTranscript: (id: number) => void
  readonly onTranscriptsUpdate: () => void
}

/**
 * 左栏内容容器。视图切换与宽度控制已上移到活动条（AppLayout），
 * 这里只按 view 渲染对应列表，各自带自己的头部行，不再有 tab 行。
 */
function LeftPanel({
  view,
  transcripts,
  jobs,
  activeTranscriptId,
  onLoadTranscript,
  onTranscriptsUpdate,
}: LeftPanelProps) {
  if (view === 'tasks') {
    return <TasksTab jobs={jobs} />
  }
  return (
    <ProcessedTab
      transcripts={transcripts}
      activeTranscriptId={activeTranscriptId}
      onLoadTranscript={onLoadTranscript}
      onTranscriptsUpdate={onTranscriptsUpdate}
    />
  )
}

export default LeftPanel
