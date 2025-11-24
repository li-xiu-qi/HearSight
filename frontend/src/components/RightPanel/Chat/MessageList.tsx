import { useRef } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Copy, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { ChatMessage, TranscriptMeta } from "../../../types";
import { formatTime } from "../../../utils";
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
  readonly frameCache: Record<string, string>
  readonly onSeekTo: (timeMs: number, videoName?: string) => void
  readonly availableTranscripts: TranscriptMeta[]
  readonly selectedTranscripts: number[]
}

export default function MessageList({
  messages,
  loading,
  error,
  imageModeEnabled,
  frameCache,
  onSeekTo,
  availableTranscripts,
  selectedTranscripts,
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
    // 修复模型可能把时间戳或图片信息放在句末标点之前的情况，例如：
    // "这是一个示例[123.00-456.00]." -> "这是一个示例. [123.00-456.00]"
    // 规则：将紧邻标点之前的方括号时间戳或带文件名的方括号移动到标点之后并在其前加一个空格
    content = content.replace(/(\S)(\[[^\]]+\])([。.,!?，；;:：])/g, "$1$3 $2")
    // 也处理没有紧邻字符的情况，例如："句子 [123-456]." -> "句子. [123-456]"
    content = content.replace(/(\s)(\[[^\]]+\])([。.,!?，；;:：])/g, "$1$3 $2")
    const parts = content.split(/(\[.*?\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?\])/g)

    return parts.map((part, index) => {
      const timeMatch = /\[(.*?)\s*(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/.exec(part)
      if (timeMatch) {
        const videoName = timeMatch[1].trim()
        const startTime = Number.parseFloat(timeMatch[2])
        const endTime = Number.parseFloat(timeMatch[3])
        // 根据videoName找到对应的transcriptId
        let transcriptId: number | undefined = undefined
        const matchedTranscript = availableTranscripts.find(transcript =>
          transcript.title === videoName ||
          transcript.video_path?.includes(videoName) ||
          transcript.audio_path?.includes(videoName) ||
          transcript.title?.includes(videoName.replace(/\.[^/.]+$/, '')) ||
          transcript.video_path?.includes(videoName.replace(/\.[^/.]+$/, '')) ||
          transcript.audio_path?.includes(videoName.replace(/\.[^/.]+$/, ''))
        )
        if (matchedTranscript) {
          transcriptId = matchedTranscript.id
        } else if (selectedTranscripts.length > 0) {
          // 回退到第一个选中的transcript
          transcriptId = selectedTranscripts[0]
        } else if (availableTranscripts.length > 0) {
          // 回退到第一个可用transcript
          transcriptId = availableTranscripts[0].id
        }
        // startTime 和 endTime 在消息中通常以毫秒为单位，转换为秒作为缓存键
        const startTimeSec = Math.floor(startTime / 1000)
        const endTimeSec = Math.floor(endTime / 1000)
        const cacheKey = transcriptId ? `${transcriptId}-${startTimeSec}-${endTimeSec}` : `${startTimeSec}-${endTimeSec}`
        const cachedImage = frameCache[cacheKey]
        const isDataUrl = typeof cachedImage === 'string' && (cachedImage.startsWith('data:image/') || cachedImage.startsWith('http'))
        // Debug info removed; rely on Summaries/Chat logs if needed

        return (
          <div key={`time-${index}-${startTime}-${endTime}`} className="flex flex-col gap-2 my-2">
            <button
              onClick={() => onSeekTo(startTime, videoName || undefined)}
              className="text-blue-600 hover:text-blue-800 underline text-sm self-start"
            >
              {videoName ? `${videoName} ` : ""}{formatTime(startTime)} - {formatTime(endTime)}
            </button>
            {imageModeEnabled && (
              <div className="relative flex justify-center">
                {cachedImage ? (
                  <Dialog>
                    <DialogTrigger asChild>
                      <img
                        src={cachedImage}
                        alt={`视频截图 ${formatTime(startTime)}`}
                        className="w-full max-w-md h-40 sm:h-48 object-cover rounded border cursor-pointer hover:opacity-80 transition-opacity"
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
                  <div className="w-full max-w-md h-40 sm:h-48 bg-gray-200 rounded flex items-center justify-center">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                )}
              </div>
            )}
          </div>
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  return (
    <ScrollArea className="flex-1 min-h-0 h-full p-3">
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
                <img
                  src="/chatbot.png"
                  alt="AI"
                  className="flex-shrink-0 w-8 h-8 rounded-full object-cover"
                />
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
              {message.type === "user" && (
                <img
                  src="/human.png"
                  alt="User"
                  className="flex-shrink-0 w-8 h-8 rounded-full object-cover"
                />
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-start gap-2">
              <img
                src="/chatbot.png"
                alt="AI"
                className="flex-shrink-0 w-8 h-8 rounded-full object-cover"
              />
              <div className="flex flex-col gap-0.5 flex-1">
                <div className="rounded-lg p-3 bg-slate-100 text-slate-900">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-slate-600">AI正在思考中...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      <div ref={messagesEndRef} />
    </ScrollArea>
  )
}