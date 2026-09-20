'use client'

import { useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, FileText, RefreshCw } from "lucide-react";
import type { TranscriptMeta } from '../../types'
import { extractFilename } from '../../utils'
import { deleteTranscriptComplete } from '../../services/transcriptService'
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
      <div className="flex items-center justify-between px-4 pt-4 pb-2 flex-shrink-0">
        <div className="text-xs font-medium text-muted-foreground tracking-wide">已处理记录</div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          title="刷新列表"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* 列表内容或空状态 */}
      {transcripts.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-center px-8">
          <FileText className="h-10 w-10 text-muted-foreground mb-3" />
          <div className="text-sm font-medium text-foreground mb-1">暂无处理记录</div>
          <div className="text-xs text-muted-foreground leading-5">
            在顶栏粘贴链接或上传文件，分析完成后会出现在这里
          </div>
        </div>
      ) : (
        <ScrollArea className="h-full flex-1">
          <div className="px-1.5 pb-2">
            {transcripts.map((item) => {
              const basename = extractFilename(item.video_path || item.audio_path || '')
              const isActive = activeTranscriptId === item.id

              return (
                <div
                  key={item.id}
                  className={`
                    group w-full text-left pl-3 pr-2 py-2.5 cursor-pointer
                    border-l-2 transition-colors
                    ${isActive
                      ? 'border-primary bg-primary/[0.06]'
                      : 'border-transparent hover:bg-muted'}
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
                  <div className="flex items-start justify-between gap-1">
                    <div className="flex-1 min-w-0">
                      <div
                        className={`
                          text-sm line-clamp-2 leading-5
                          ${isActive ? 'text-primary font-medium' : 'text-foreground'}
                        `}
                        title={basename}
                      >
                        {basename}
                      </div>
                      <div className="text-[11px] font-mono text-muted-foreground mt-1 line-clamp-1">
                        {formatDate(item.created_at)}
                      </div>
                    </div>
                    <div
                      className={`${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity`}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                    >
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                            title="更多操作"
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
                            className="text-destructive"
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
