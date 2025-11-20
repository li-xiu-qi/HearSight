import { useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, FileText, RefreshCw } from 'lucide-react'
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
  const [isRefreshing, setIsRefreshing] = useState(false)

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

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await onTranscriptsUpdate()
    } finally {
      setIsRefreshing(false)
    }
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

  return (
    <div className="h-full flex flex-col">
      {/* 顶部标题栏和刷新按钮，始终显示 */}
      <div className="flex items-center justify-between mb-3 flex-shrink-0 px-4 pt-4">
        <div className="text-sm font-medium text-slate-700">已处理记录</div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="h-7 w-7 p-0 hover:bg-slate-100"
          title="刷新列表"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>
      
      {/* 列表内容或空状态 */}
      {transcripts.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-center p-8">
          <FileText className="h-12 w-12 text-slate-300 mb-4" />
          <div className="text-base font-medium text-slate-700 mb-2">暂无处理记录</div>
          <div className="text-sm text-slate-500">
            您还没有处理过任何视频。在上方输入视频URL开始分析吧！
          </div>
        </div>
      ) : (
        <ScrollArea className="h-full flex-1">
          <div className="space-y-2 px-4">
            {transcripts.map((item) => {
              const basename = extractFilename(item.video_path || item.audio_path || '')
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
      )}
    </div>
  )
}

export default ProcessedTab
