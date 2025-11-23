import { useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Copy, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { Segment, ChatMessage } from "../../../types";
import { fetchThumbnail } from "../../../services/thumbnailService";
import { formatTime } from "../../../utils";
import MarkdownRenderer from "../../MarkdownRenderer"
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

interface MessageListProps {
  readonly messages: ChatMessage[]
  readonly loading: boolean
  readonly error: string | null
  readonly imageModeEnabled: boolean
  readonly transcriptId?: number
  readonly frameCache: Record<string, string>
  readonly onSeekTo: (timeMs: number, videoName?: string) => void
}

export default function MessageList({
  messages,
  loading,
  error,
  imageModeEnabled,
  transcriptId,
  frameCache,
  onSeekTo,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const handleCopyMessage = async (content: string, type: "user" | "ai") => {
    try {
      await navigator.clipboard.writeText(content)
      toast.success(`${type === "user" ? "用户" : "AI"}消息已复制到剪贴板`)
    } catch (error) {
      toast.error("复制失败")
    }
  }

  const renderMessageContent = (content: string) => {
    const parts = content.split(/(\[.*?\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?\])/g)

    return parts.map((part, index) => {
      const timeMatch = /\[(.*?)\s*(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/.exec(part)
      if (timeMatch) {
        const videoName = timeMatch[1].trim()
        const startTime = Number.parseFloat(timeMatch[2])
        const endTime = Number.parseFloat(timeMatch[3])
        // 使用秒作为缓存键，与加载逻辑保持一致
        const startTimeSec = Math.floor(startTime / 1000)
        const endTimeSec = Math.floor(endTime / 1000)
        const cacheKey = `${startTimeSec}-${endTimeSec}`
        const cachedImage = frameCache[cacheKey]

        return (
          <div key={`time-${index}-${startTime}-${endTime}`} className="flex flex-col gap-2 my-2">
            {imageModeEnabled && (
              <div className="relative">
                {cachedImage ? (
                  <Dialog>
                    <DialogTrigger asChild>
                      <img
                        src={cachedImage}
                        alt={`视频截图 ${formatTime(startTime)}`}
                        className="w-full max-w-xs h-24 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
                      />
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl">
                      <DialogTitle className="sr-only">视频截图预览</DialogTitle>
                      <DialogDescription className="sr-only">
                        视频截图 {formatTime(startTime)} 的预览
                      </DialogDescription>
                      <img
                        src={cachedImage}
                        alt={`视频截图 ${formatTime(startTime)}`}
                        className="w-full h-auto max-h-[80vh] object-contain"
                      />
                    </DialogContent>
                  </Dialog>
                ) : (
                  <div className="w-full max-w-xs h-24 bg-gray-200 rounded flex items-center justify-center">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                )}
              </div>
            )}
            <button
              onClick={() => onSeekTo(startTime, videoName || undefined)}
              className="text-blue-600 hover:text-blue-800 underline text-sm"
            >
              {videoName ? `${videoName} ` : ""}{formatTime(startTime)} - {formatTime(endTime)}
            </button>
          </div>
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  return (
    <ScrollArea className="flex-1 min-h-0 p-3">
      {error && (
        <div className="mx-3 mt-3 mb-0 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200 flex-shrink-0">
          {error}
        </div>
      )}

      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-center p-8 text-slate-500">
          <p className="text-base mb-2">欢迎使用视频内容问答功能</p>
          <p className="text-sm">请输入您的问题，AI 将基于当前媒体文件内容为您解答</p>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-2 ${
                message.type === "user" ? "justify-end" : ""
              }`}
            >
              {message.type === "ai" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center text-xs font-semibold">
                  AI
                </div>
              )}
              <div className="flex flex-col gap-0.5 flex-1">
                <div
                  className={`rounded-lg p-3 ${
                    message.type === "user"
                      ? "bg-blue-500 text-white ml-auto"
                      : "bg-slate-100 text-slate-900"
                  }`}
                >
                  <div className="text-sm">
                    {message.type === "user" ? (
                      message.content
                    ) : (
                      renderMessageContent(message.content)
                    )}
                  </div>
                </div>
                <div className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                  <Button
                    onClick={() => handleCopyMessage(message.content, message.type)}
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-slate-400 hover:text-slate-600"
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      <div ref={messagesEndRef} />
    </ScrollArea>
  )
}