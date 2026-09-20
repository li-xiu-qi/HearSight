'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { TranscriptMeta, JobItem } from '../../types'
import ProcessedTab from './ProcessedTab'
import TasksTab from './TasksTab'

interface LeftPanelProps {
  readonly transcripts: TranscriptMeta[]
  readonly jobs: JobItem[]
  readonly activeTranscriptId: number | null
  readonly onLoadTranscript: (id: number) => void
  readonly onTranscriptsUpdate: () => void
}

/**
 * 左栏：素材库 + 任务。tab 用 segmented 控件形态，trigger 上带计数。
 * 收起开关在左侧分隔条中央（见 AppLayout），此处不放第二个入口。
 */
function LeftPanel({
  transcripts,
  jobs,
  activeTranscriptId,
  onLoadTranscript,
  onTranscriptsUpdate,
}: LeftPanelProps) {
  const runningJobs = jobs.filter(j => j.status === 'processing' || j.status === 'pending').length

  return (
    <Tabs defaultValue="processed" className="h-full flex flex-col gap-0">
      <div className="px-3 pt-3 flex-shrink-0">
        <TabsList className="w-full">
          <TabsTrigger value="processed" className="flex-1 gap-1.5">
            素材库
            {transcripts.length > 0 && (
              <span className="font-mono text-[11px] text-muted-foreground">{transcripts.length}</span>
            )}
          </TabsTrigger>
          <TabsTrigger value="tasks" className="flex-1 gap-1.5">
            任务
            {runningJobs > 0 && (
              <span className="font-mono text-[11px] text-primary">{runningJobs}</span>
            )}
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="processed" className="flex-1 m-0 min-h-0 data-[state=inactive]:hidden">
        <ProcessedTab
          transcripts={transcripts}
          activeTranscriptId={activeTranscriptId}
          onLoadTranscript={onLoadTranscript}
          onTranscriptsUpdate={onTranscriptsUpdate}
        />
      </TabsContent>

      <TabsContent value="tasks" className="flex-1 m-0 min-h-0 data-[state=inactive]:hidden">
        <TasksTab jobs={jobs} />
      </TabsContent>
    </Tabs>
  )
}

export default LeftPanel
