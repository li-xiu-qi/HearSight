import { Card, CardContent } from '@/components/ui/card'
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

function LeftPanel({
  transcripts,
  jobs,
  activeTranscriptId,
  onLoadTranscript,
  onTranscriptsUpdate,
}: LeftPanelProps) {

  return (
    <div className="h-full flex flex-col">
      <Card className="h-full flex flex-col">
        <CardContent className="flex-1 p-0 min-h-0">
          <Tabs defaultValue="processed" className="h-full flex flex-col">
            <TabsList className="w-full rounded-none border-b">
              <TabsTrigger value="processed" className="flex-1">已处理</TabsTrigger>
              <TabsTrigger value="tasks" className="flex-1">处理情况</TabsTrigger>
            </TabsList>
            
            <TabsContent value="processed" className="flex-1 m-0 p-3 overflow-hidden">
              <ProcessedTab
                transcripts={transcripts}
                activeTranscriptId={activeTranscriptId}
                onLoadTranscript={onLoadTranscript}
                onTranscriptsUpdate={onTranscriptsUpdate}
              />
            </TabsContent>
            
            <TabsContent value="tasks" className="flex-1 m-0 p-3 overflow-hidden">
              <TasksTab jobs={jobs} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

export default LeftPanel
