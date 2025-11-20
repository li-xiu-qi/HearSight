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
import FileRenameDialog from '../FileRenameDialog'

interface TranscriptsTabProps {
  transcripts: TranscriptMeta[]
  activeTranscriptId: number | null
  onLoadTranscript: (id: number) => void
  onDeleteTranscript: (id: number) => void
  onTranscriptsUpdate: () => void
}

function TranscriptsTab({
  transcripts,
  activeTranscriptId,
  onLoadTranscript,
  onDeleteTranscript,
  onTranscriptsUpdate,
}: TranscriptsTabProps) {
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
          const basename = extractFilename(item.audio_path || item.video_path || '')
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
              role="button"
              tabIndex={0}
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
                    ID {item.id} · {item.segment_count} 段 · {item.created_at}
                  </div>
                </div>
                <div 
                  onClick={(e) => e.stopPropagation()} 
                  onKeyDown={(e) => e.stopPropagation()}
                  role="button"
                  tabIndex={-1}
                >
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
                          onDeleteTranscript(item.id)
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

export default TranscriptsTab
