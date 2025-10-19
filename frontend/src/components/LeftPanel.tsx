import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, FileText, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import type { TranscriptMeta, JobItem } from '../types'
import { extractFilename } from '../utils'
import { deleteTranscriptComplete } from '../services/api'
import { message } from '../utils/message'

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

  const handleDeleteTranscript = async (transcriptId: number) => {
    try {
      const result = await deleteTranscriptComplete(transcriptId)
      if (result.success) {
        message.success(result.message || '删除成功')
        onTranscriptsUpdate()
      } else {
        message.warning(result.message || '删除失败')
      }
    } catch (error: any) {
      message.error(error?.message || '删除失败')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
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
      case 'running':
        return 'bg-blue-100 text-blue-700'
      case 'success':
        return 'bg-green-100 text-green-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-slate-100 text-slate-600'
    }
  }

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
              {transcripts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-8">
                  <FileText className="h-12 w-12 text-slate-300 mb-4" />
                  <div className="text-base font-medium text-slate-700 mb-2">暂无处理记录</div>
                  <div className="text-sm text-slate-500">
                    您还没有处理过任何视频。在上方输入视频URL开始分析吧！
                  </div>
                </div>
              ) : (
                <ScrollArea className="h-full">
                  <div className="space-y-2">
                    {transcripts.map((item) => {
                      const basename = extractFilename(item.media_path)
                      const isActive = activeTranscriptId === item.id
                      
                      return (
                        // eslint-disable-next-line jsx-a11y/click-events-have-key-events,jsx-a11y/no-static-element-interactions
                        <div
                          key={item.id}
                          className={`
                            w-full text-left p-3 rounded-lg border transition-all cursor-pointer
                            ${isActive 
                              ? 'bg-blue-50 border-blue-200 shadow-sm text-blue-900' 
                              : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300 text-slate-900'
                            }
                          `}
                          onClick={() => onLoadTranscript(item.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              onLoadTranscript(item.id)
                            }
                          }}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div 
                              className="flex-1 min-w-0"
                            >
                              <div 
                                className={`
                                  text-sm font-medium line-clamp-2
                                  ${isActive ? 'text-blue-900' : 'text-slate-900'}
                                `}
                                title={basename}
                              >
                                {basename}
                              </div>
                              <div className="text-xs text-slate-500 mt-1 line-clamp-1">
                                ID {item.id} · {item.segment_count} 段 · {item.created_at}
                              </div>
                            </div>
                            {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events,jsx-a11y/no-static-element-interactions */}
                            <div onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-7 w-7 p-0"
                                  >
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem
                                    className="text-red-600"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      handleDeleteTranscript(item.id)
                                    }}
                                  >
                                    删除记录
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </ScrollArea>
              )}
            </TabsContent>
            
            <TabsContent value="tasks" className="flex-1 m-0 p-3 overflow-hidden">
              {jobs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center p-8">
                  <Clock className="h-12 w-12 text-slate-300 mb-4" />
                  <div className="text-base font-medium text-slate-700 mb-2">暂无处理任务</div>
                  <div className="text-sm text-slate-500">
                    当前没有正在处理的视频。提交视频URL后，处理进度会显示在这里。
                  </div>
                </div>
              ) : (
                <ScrollArea className="h-full">
                  <div className="space-y-2">
                    {jobs.map((item) => {
                      const shortUrl = (item.url || '').replace(/^https?:\/\//, '')
                      
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
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

export default LeftPanel
