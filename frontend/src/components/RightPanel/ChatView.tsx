import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, PlayCircle, Trash2, Loader2, Copy } from "lucide-react"
import { toast } from "sonner"
import type { Segment, ChatResponse } from "../../types"
import { chatWithSegments } from "../../services/api"
import { formatTime } from "../../utils"
import MarkdownRenderer from "../MarkdownRenderer"

interface ChatViewProps {
  readonly segments: Segment[]
  readonly messages?: ChatMessage[]
  readonly loading?: boolean
  readonly error?: string | null
  readonly onMessagesChange?: (messages: ChatMessage[]) => void
  readonly onLoadingChange?: (loading: boolean) => void
  readonly onErrorChange?: (error: string | null) => void
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
}: Readonly<ChatViewProps>) {
  const [inputValue, setInputValue] = useState("")
  const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([])
  const [internalLoading, setInternalLoading] = useState(false)
  const [internalError, setInternalError] = useState<string | null>(null)
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

    return parts.map((part) => {
      const timeMatch = /\[(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/.exec(part)
      if (timeMatch) {
        const startTime = Number.parseFloat(timeMatch[1])
        const endTime = Number.parseFloat(timeMatch[2])
        return (
          <button
            key={`time-${startTime}-${endTime}`}
            type="button"
            onClick={() => {
              globalThis.dispatchEvent(
                new CustomEvent("seekToTime", { detail: startTime })
              )
            }}
            className="inline-flex items-center gap-1 text-blue-600 hover:underline text-sm"
            title={`时间: ${formatTime(startTime)} ~ ${formatTime(endTime)}`}
          >
            <PlayCircle className="h-3 w-3" />
            跳转到对应位置
          </button>
        )
      }
      return (
        <span key={`text-${part.substring(0, 20)}`} className="inline">
          <MarkdownRenderer>{part}</MarkdownRenderer>
        </span>
      )
    })
  }

  const handleClearChat = () => {
    setMessages([])
    setError(null)
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
            <p className="text-sm">请输入您的问题，AI 将基于视频字幕内容为您解答</p>
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
        <div className="flex justify-end">
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
