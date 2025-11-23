import { useState, useEffect } from "react"
import type { Segment, ChatResponse, ChatMessage } from "../../types"
import { chatWithSegments } from "../../services/chatService"
import { getChatMessages, saveChatMessages, clearChatMessages } from "../../services/chatService"
import { fetchTranscripts } from "../../services/transcriptService"
import { fetchThumbnail } from "../../services/thumbnailService"
import { MessageList, VideoSelector, ChatToolbar, MessageInput } from "./Chat"

interface ChatViewProps {
  readonly segments: Segment[]
  readonly messages?: ChatMessage[]
  readonly loading?: boolean
  readonly error?: string | null
  readonly onMessagesChange?: (messages: ChatMessage[]) => void
  readonly onLoadingChange?: (loading: boolean) => void
  readonly onErrorChange?: (error: string | null) => void
  readonly onSeekTo: (timeMs: number, transcriptId?: number) => void
  readonly transcriptId?: number
  readonly mediaType?: string
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
  const [selectedTranscriptIds, setSelectedTranscriptIds] = useState<number[]>(transcriptId ? [transcriptId] : [])
  const [availableTranscripts, setAvailableTranscripts] = useState<any[]>([])
  const isAudio = mediaType === 'audio'
  const [imageModeEnabled, setImageModeEnabled] = useState(!isAudio)
  const [frameCache, setFrameCache] = useState<Record<string, string>>({})

  const messages = externalMessages ?? internalMessages
  const loading = externalLoading ?? internalLoading
  const error = externalError ?? internalError

  const setMessages = onMessagesChange || setInternalMessages
  const setLoading = onLoadingChange || setInternalLoading
  const setError = onErrorChange || setInternalError

  const handleSeekTo = (timeMs: number, videoName?: string) => {
    let targetTranscriptId = transcriptId
    if (videoName) {
      const found = availableTranscripts.find(t => t.filename === videoName)
      if (found) {
        targetTranscriptId = found.transcript_id
      }
    }
    onSeekTo(timeMs, targetTranscriptId)
  }

  // 加载问答消息中的缩略图
  useEffect(() => {
    if (!imageModeEnabled) return

    const loadThumbnails = async () => {
      const timeStamps: { startTime: number; endTime: number; cacheKey: string; transcriptId: number }[] = []

      // 解析所有消息中的时间戳
      messages.forEach(message => {
        if (message.type === 'ai') {
          const content = message.content
          const parts = content.split(/(\[.*?\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?\])/g)
          parts.forEach(part => {
            const timeMatch = /\[(.*?)\s*(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/.exec(part)
            if (timeMatch) {
              const videoName = timeMatch[1].trim()
              const startTime = Number.parseFloat(timeMatch[2])
              const endTime = Number.parseFloat(timeMatch[3])
              const startTimeSec = Math.floor(startTime / 1000)
              const endTimeSec = Math.floor(endTime / 1000)
              const cacheKey = `${startTimeSec}-${endTimeSec}`

              // 确定 transcriptId
              let targetTranscriptId = selectedTranscriptIds[0] || transcriptId
              if (videoName && availableTranscripts.length > 0) {
                const found = availableTranscripts.find(t => t.filename === videoName)
                if (found) {
                  targetTranscriptId = found.transcript_id
                }
              }

              if (targetTranscriptId && !frameCache[cacheKey]) {
                timeStamps.push({ startTime, endTime, cacheKey, transcriptId: targetTranscriptId })
              }
            }
          })
        }
      })

      // 加载未缓存的截图
      for (const { startTime, endTime, cacheKey, transcriptId: tid } of timeStamps) {
        try {
          const url = await fetchThumbnail(tid, startTime, endTime, 320)
          if (url) {
            setFrameCache(prev => ({ ...prev, [cacheKey]: url }))
          }
        } catch (error) {
          console.error('Failed to fetch thumbnail:', error)
        }
      }
    }

    loadThumbnails()
  }, [imageModeEnabled, messages, transcriptId, availableTranscripts, frameCache])

  // 加载已保存的chat消息
  useEffect(() => {
    if (!transcriptId) return

    const loadSavedMessages = async () => {
      try {
        const result = await getChatMessages(transcriptId)
        if (result.messages && result.messages.length > 0) {
          setMessages(result.messages)
        } else {
          setMessages([])
        }
      } catch (error) {
        console.error('加载chat消息失败:', error)
        setMessages([])
      }
    }

    loadSavedMessages()
  }, [transcriptId])

  // 加载所有可用的transcripts用于多视频选择
  useEffect(() => {
    const loadAvailableTranscripts = async () => {
      try {
        const response = await fetchTranscripts()
        setAvailableTranscripts(response.items || [])
      } catch (error) {
        console.error('加载可用视频列表失败:', error)
      }
    }

    loadAvailableTranscripts()
  }, [])

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
      const response: ChatResponse = await chatWithSegments(segments, inputValue, selectedTranscriptIds)

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
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      setError(error instanceof Error ? error.message : '发送失败')
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = async () => {
    setMessages([])
    setInputValue("")
    setError(null)

    if (transcriptId) {
      try {
        await clearChatMessages(transcriptId)
      } catch (error) {
        console.error('清除chat消息失败:', error)
      }
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <MessageList
        messages={messages}
        loading={loading}
        error={error}
        imageModeEnabled={imageModeEnabled}
        transcriptId={selectedTranscriptIds[0]}
        frameCache={frameCache}
        onSeekTo={handleSeekTo}
      />

      <div className="p-3 border-t space-y-2 flex-shrink-0">
        <ChatToolbar
          imageModeEnabled={imageModeEnabled}
          isAudio={isAudio}
          messagesLength={messages.length}
          onImageModeChange={setImageModeEnabled}
          onClearChat={handleClearChat}
        />

        <VideoSelector
          availableTranscripts={availableTranscripts}
          selectedTranscriptIds={selectedTranscriptIds}
          onSelectionChange={setSelectedTranscriptIds}
        />

        <MessageInput
          inputValue={inputValue}
          loading={loading}
          disabled={!inputValue.trim() || loading}
          onInputChange={setInputValue}
          onSend={handleSend}
        />
      </div>
    </div>
  )
}
