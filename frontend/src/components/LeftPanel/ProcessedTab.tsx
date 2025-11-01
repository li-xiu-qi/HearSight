import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, FileText } from 'lucide-react'
import type { TranscriptMeta } from '../../types'
import { extractFilename } from '../../utils'
import { deleteTranscriptComplete } from '../../services/api'
import { message } from '../../utils/message'
import FileRenameDialog from '../FileRenameDialog'

interface ProcessedTabProps {
  readonly transcripts: TranscriptMeta[]
  readonly activeTranscriptId: number | null
  readonly onLoadTranscript: (id: number) => void
  readonly onTranscriptsUpdate: () => void
}

function ProcessedTab({
  transcripts,
  activeTranscriptId,
  onLoadTranscript,
  onTranscriptsUpdate,
}: ProcessedTabProps) {

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const handleDeleteTranscript = async (transcriptId: number) => {
    try {
      const result = await deleteTranscriptComplete(transcriptId)
      if (result.success) {
        message.success(result.message || '删除成功')
        onTranscriptsUpdate()
      } else {
        message.warning(result.message || '删除失败')
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '删除失败'
      message.error(errorMessage)
    }
  }

  if (transcripts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <FileText className="h-12 w-12 text-slate-300 mb-4" />
        <div className="text-base font-medium text-slate-700 mb-2">暂无处理记录</div>
        <div className="text-sm text-slate-500">
          您还没有处理过任何视频。在上方输入视频URL开始分析吧！
        </div>
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2">
        {transcripts.map((item) => {
          const basename = extractFilename(item.media_path)
          const isActive = activeTranscriptId === item.id
          
          return (
             
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
                <div className="flex-1 min-w-0">
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
                    {formatDate(item.created_at)}
                  </div>
                </div>
                { }
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
                      <div className="p-0">
                        <FileRenameDialog
                          oldFilename={basename}
                          onRenameSuccess={() => {
                            onTranscriptsUpdate()
                          }}
                        />
                      </div>
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
  )
}

export default ProcessedTab
