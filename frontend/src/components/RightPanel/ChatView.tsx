import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, PlayCircle, Trash2, Loader2, Copy } from "lucide-react"
import { toast } from "sonner"
import type { Segment, ChatResponse } from "../../types"
import { chatWithSegments, fetchThumbnail, getChatMessages, saveChatMessages, clearChatMessages } from "../../services/api"
import { formatTime } from "../../utils"
import MarkdownRenderer from "../MarkdownRenderer"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

interface ChatViewProps {
  readonly segments: Segment[]
  readonly messages?: ChatMessage[]
  readonly loading?: boolean
  readonly error?: string | null
  readonly onMessagesChange?: (messages: ChatMessage[]) => void
  readonly onLoadingChange?: (loading: boolean) => void
  readonly onErrorChange?: (error: string | null) => void
  readonly onSeekTo: (timeMs: number) => void
  readonly transcriptId?: number
  readonly mediaType?: string
}

export interface ChatMessage {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: number
}

export default function ChatView({
  segments,
  messages: externalMessages,
  loading: externalLoading,
  error: externalError,
  onMessagesChange,
  onLoadingChange,
  onErrorChange,
  onSeekTo,
  transcriptId,
  mediaType,
}: Readonly<ChatViewProps>) {
  const [inputValue, setInputValue] = useState("")
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([])
  const [internalLoading, setInternalLoading] = useState(false)
  const [internalError, setInternalError] = useState<string | null>(null)
  const isAudio = mediaType === 'audio'
  const [imageModeEnabled, setImageModeEnabled] = useState(!isAudio)
  const [frameCache, setFrameCache] = useState<Record<string, string>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messages = externalMessages ?? internalMessages
  const loading = externalLoading ?? internalLoading
  const error = externalError ?? internalError

  const setMessages = onMessagesChange || setInternalMessages
  const setLoading = onLoadingChange || setInternalLoading
  const setError = onErrorChange || setInternalError

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 加载已保存的chat消息
  useEffect(() => {
    if (!transcriptId) return

    const loadSavedMessages = async () => {
      try {
        const result = await getChatMessages(transcriptId)
        if (result.messages && result.messages.length > 0) {
          setMessages(result.messages)
        } else {
          // 新视频没有保存的消息，清空旧消息
          setMessages([])
        }
      } catch (error) {
        console.error('加载chat消息失败:', error)
        // 不显示错误提示，因为这可能是第一次使用
        setMessages([])
      }
    }

    loadSavedMessages()
  }, [transcriptId, setMessages])

  // 加载所有时间戳的截图
  useEffect(() => {
    if (!imageModeEnabled || !transcriptId) return

    const loadAllThumbnails = async () => {
      const timeStamps: { midTime: number; startTime: number; endTime: number; cacheKey: string }[] = []

      // 收集所有消息中的时间戳
      for (const message of messages) {
        if (message.type === 'ai') {
          const timeMatches = message.content.matchAll(/\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/g)
          for (const match of timeMatches) {
            const startTimeMs = Number.parseFloat(match[1])
            const endTimeMs = Number.parseFloat(match[2])
            // 使用秒作为缓存键，避免毫秒精度差异导致的重复缓存
            const startTimeSec = Math.floor(startTimeMs / 1000)
            const endTimeSec = Math.floor(endTimeMs / 1000)
            const cacheKey = `${startTimeSec}-${endTimeSec}`
            if (!frameCache[cacheKey]) {
              // 使用中点时间来截图，避免边界问题
              const midTime = (startTimeMs + endTimeMs) / 2
              timeStamps.push({ midTime, startTime: startTimeMs, endTime: endTimeMs, cacheKey })
            }
          }
        }
      }

      // 加载未缓存的截图
      for (const { startTime, endTime, cacheKey } of timeStamps) {
        try {
          const url = await fetchThumbnail(transcriptId, startTime, endTime, 320)
          if (url) {
            setFrameCache(prev => ({ ...prev, [cacheKey]: url }))
          }
        } catch (error) {
          console.error('Failed to fetch thumbnail:', error)
        }
      }
    }

    loadAllThumbnails()
  }, [imageModeEnabled, messages, transcriptId, frameCache])

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: "user",
      content: inputValue,
      timestamp: Date.now(),
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInputValue("")

    setLoading(true)
    setError(null)

    try {
      const response: ChatResponse = await chatWithSegments(segments, inputValue)

      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        type: "ai",
        content: response.answer || "抱歉，我没有理解您的问题",
        timestamp: Date.now(),
      }

      setMessages([...newMessages, aiMessage])

      // 自动保存chat消息到数据库
      if (transcriptId) {
        try {
          await saveChatMessages(transcriptId, [...newMessages, aiMessage])
        } catch (error) {
          console.error('保存chat消息失败:', error)
          // 不显示错误提示，避免影响用户体验
        }
      }
    } catch (err: unknown) {
      setError((err as Error)?.message || "聊天失败，请稍后重试")
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        type: "ai",
        content: "抱歉，回答失败，请稍后重试",
        timestamp: Date.now(),
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const renderMessageContent = (content: string) => {
    const parts = content.split(/(\[\d+(?:\.\d+)?-\d+(?:\.\d+)?\])/g)

    return parts.map((part, index) => {
      const timeMatch = /\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/.exec(part)
      if (timeMatch) {
        const startTime = Number.parseFloat(timeMatch[1])
        const endTime = Number.parseFloat(timeMatch[2])
        // 使用秒作为缓存键，与加载逻辑保持一致
        const startTimeSec = Math.floor(startTime / 1000)
        const endTimeSec = Math.floor(endTime / 1000)
        const cacheKey = `${startTimeSec}-${endTimeSec}`
        const cachedImage = frameCache[cacheKey]

        return (
          <div key={`time-${index}-${startTime}-${endTime}`} className="inline-flex flex-col gap-2 my-2">
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
              type="button"
              onClick={() => onSeekTo(startTime)}
              className="inline-flex items-center gap-1 text-blue-600 hover:underline text-sm"
              title={`时间: ${formatTime(startTime)} ~ ${formatTime(endTime)}`}
            >
              <PlayCircle className="h-3 w-3" />
              跳转到对应位置
            </button>
          </div>
        )
      }
      return (
        <span key={`text-${index}`} className="inline">
          <MarkdownRenderer>{part}</MarkdownRenderer>
        </span>
      )
    })
  }

  const handleClearChat = async () => {
    setMessages([])
    setError(null)

    // 同时清除数据库中的chat消息
    if (transcriptId) {
      try {
        await clearChatMessages(transcriptId)
      } catch (error) {
        console.error('清除chat消息失败:', error)
        // 不显示错误提示，避免影响用户体验
      }
    }
  }

  const handleCopyMessage = async (content: string, messageType: "user" | "ai") => {
    let textToCopy = content
    if (messageType === "ai") {
      textToCopy = content.replaceAll(/\[\d+(?:\.\d+)?-\d+(?:\.\d+)?\]/g, "").trim()
    }
    try {
      await navigator.clipboard.writeText(textToCopy)
      toast.success("消息已复制到剪贴板")
    } catch (err) {
      console.error("复制失败:", err)
      toast.error("复制失败")
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {error && (
        <div className="mx-3 mt-3 mb-0 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200 flex-shrink-0">
          {error}
        </div>
      )}

      <ScrollArea className="flex-1 min-h-0 p-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8 text-slate-500">
            <p className="text-base mb-2">欢迎使用视频内容问答功能</p>
            <p className="text-sm">请输入您的问题，AI 将基于视频内容为您解答</p>
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
                {message.type === "user" && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-semibold">
                    我
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </ScrollArea>

      <div className="p-3 border-t space-y-2 flex-shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Switch
              id="image-mode"
              checked={imageModeEnabled}
              onCheckedChange={setImageModeEnabled}
              disabled={isAudio}
            />
            <Label 
              htmlFor="image-mode" 
              className={`text-sm cursor-pointer ${isAudio ? 'text-slate-400' : ''}`}
              title={isAudio ? '音频文件不支持图文展示' : ''}
            >
              图文展示
            </Label>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearChat}
            disabled={messages.length === 0}
            className="gap-1"
          >
            <Trash2 className="h-3 w-3" />
            清空对话
          </Button>
        </div>
        <Textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="请输入您的问题..."
          className="min-h-[80px] resize-none"
          disabled={loading}
        />
        <Button
          onClick={handleSend}
          disabled={!inputValue.trim() || loading}
          className="w-full gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              发送中
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              发送
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
