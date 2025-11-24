import { useState, useEffect, useRef } from "react"
import { toast } from 'sonner'
import MessageList from "./MessageList"
import VideoSelector from "./VideoSelector"
import ChatToolbar from "./ChatToolbar"
import MessageInput from "./MessageInput"
import { getChatMessages, saveChatMessages, chatWithTranscriptsSSE } from "@/services/chatService"
import { fetchThumbnail } from "@/services/thumbnailService"
import type { ChatMessage, TranscriptMeta } from "@/types"

interface ChatViewProps {
  sessionId: number
  messages: ChatMessage[]
  loading: boolean
  error: string | null
  onMessagesChange: (messages: ChatMessage[]) => void
  onLoadingChange: (loading: boolean) => void
  onErrorChange: (error: string | null) => void
  onSeekTo: (timeMs: number, transcriptId?: number) => void
  availableTranscripts: TranscriptMeta[]
  mediaType?: string
  currentTranscriptId?: number
}

export default function ChatView({
  sessionId,
  messages,
  loading,
  error,
  onMessagesChange,
  onLoadingChange,
  onErrorChange,
  onSeekTo,
  availableTranscripts,
  mediaType,
  currentTranscriptId,
}: ChatViewProps) {
  const [selectedTranscripts, setSelectedTranscripts] = useState<number[]>(
    currentTranscriptId ? [currentTranscriptId] : []
  )
  const [inputValue, setInputValue] = useState("")
  const isAudio = mediaType === 'audio'
  const [imageModeEnabled, setImageModeEnabled] = useState(!isAudio)
  const [frameCache, setFrameCache] = useState<Record<string, string>>({})
  const messagesRef = useRef(messages)

  // 更新 messagesRef 以反映最新的 messages
  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  // 当currentTranscriptId变化时，更新默认选中
  useEffect(() => {
    if (currentTranscriptId && !selectedTranscripts.includes(currentTranscriptId)) {
      setSelectedTranscripts([currentTranscriptId])
    }
  }, [currentTranscriptId, selectedTranscripts])

  // 加载消息
  useEffect(() => {
    const loadMessages = async () => {
      if (!sessionId) return

      onLoadingChange(true)
      onErrorChange(null)

      try {
        const loadedMessages = await getChatMessages(sessionId)
        onMessagesChange(loadedMessages.messages || [])
      } catch (err) {
        onErrorChange(err instanceof Error ? err.message : '加载消息失败')
      } finally {
        onLoadingChange(false)
      }
    }

    loadMessages()
  }, [sessionId, onMessagesChange, onLoadingChange, onErrorChange])

  // 加载消息中的时间戳图片
  useEffect(() => {
    if (!imageModeEnabled || (selectedTranscripts.length === 0 && availableTranscripts.length === 0)) return

    const loadThumbnailsForMessages = async () => {
      const timeStamps: { startTime: number; endTime: number; cacheKey: string; transcriptId: number }[] = []

      // 从消息内容中提取时间戳
      for (const message of messages) {
        if (message.type === 'ai') {
          const timeMatches = message.content.matchAll(/\[([^\]]+?)\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]/g)
          for (const match of timeMatches) {
            const videoName = match[1].trim()
            // 时间戳以毫秒为单位（例如 165670.00），直接使用
            const startTime = Number.parseFloat(match[2])
            const endTime = Number.parseFloat(match[3])
            const startTimeSec = Math.floor(startTime / 1000)
            const endTimeSec = Math.floor(endTime / 1000)

            // 根据videoName找到对应的transcriptId
            const matchedTranscript = availableTranscripts.find(transcript =>
              transcript.title === videoName ||
              transcript.video_path?.includes(videoName) ||
              transcript.audio_path?.includes(videoName) ||
              transcript.title?.includes(videoName.replace(/\.[^/.]+$/, '')) ||
              transcript.video_path?.includes(videoName.replace(/\.[^/.]+$/, '')) ||
              transcript.audio_path?.includes(videoName.replace(/\.[^/.]+$/, ''))
            )
            let transcriptId: number | undefined = undefined
            if (matchedTranscript) {
              transcriptId = matchedTranscript.id
            } else if (selectedTranscripts.length > 0) {
              transcriptId = selectedTranscripts[0]
            } else if (availableTranscripts.length > 0) {
              transcriptId = availableTranscripts[0].id
            }

            if (transcriptId) {
              const cacheKey = `${transcriptId}-${startTimeSec}-${endTimeSec}`
              if (!frameCache[cacheKey]) {
                timeStamps.push({ startTime, endTime, cacheKey, transcriptId })
              }
            }
          }
        }
      }

      // 加载未缓存的截图
      for (const { startTime, endTime, cacheKey, transcriptId } of timeStamps) {
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

    loadThumbnailsForMessages()
  }, [imageModeEnabled, messages, selectedTranscripts, frameCache])

  // 处理发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue,
      type: 'user',
      timestamp: Date.now(),
    }

    const updatedMessages = [...messages, userMessage]
    onMessagesChange(updatedMessages)
    setInputValue("")

    // 如果没有选择转录内容，使用所有可用视频
    const transcriptsToUse = selectedTranscripts.length === 0 ? availableTranscripts.map(t => t.id) : selectedTranscripts

    // 如果仍然没有视频可用，直接保存消息
    if (transcriptsToUse.length === 0) {
      try {
        const res = await saveChatMessages(sessionId, updatedMessages)
        if (res && res.success) {
          toast.success('消息已保存')
        }
      } catch (err) {
        onErrorChange(err instanceof Error ? err.message : '保存消息失败')
      }
      return
    }

    // 创建AI回复消息占位符
    const aiMessageId = (Date.now() + 1).toString()
    const aiMessage: ChatMessage = {
      id: aiMessageId,
      content: '',
      type: 'ai',
      timestamp: Date.now() + 1,
    }

    const messagesWithAI = [...updatedMessages, aiMessage]
    onMessagesChange(messagesWithAI)

    try {
      // 使用SSE流式聊天
      await chatWithTranscriptsSSE(
        inputValue,
        transcriptsToUse,
        (chunk) => {
          // 处理流式消息块
          const currentMessages = messagesRef.current
          const updatedMessages = currentMessages.map(msg =>
            msg.id === aiMessageId
              ? { ...msg, content: msg.content + (chunk.chunk || '') }
              : msg
          )
          onMessagesChange(updatedMessages)
        },
        (finalAnswer) => {
          // 完成时更新最终答案
          const currentMessages = messagesRef.current
          const updatedMessages = currentMessages.map(msg =>
            msg.id === aiMessageId
              ? { ...msg, content: finalAnswer }
              : msg
          )
          onMessagesChange(updatedMessages)
          // 保存完整消息
          saveChatMessages(sessionId, messagesWithAI.map(msg =>
            msg.id === aiMessageId ? { ...msg, content: finalAnswer } : msg
          ))
          toast.success('回复完成')
        },
        (error) => {
          // 处理错误
          onErrorChange(error)
          toast.error(`聊天失败: ${error}`)
          // 移除失败的AI消息
          const currentMessages = messagesRef.current
          const updatedMessages = currentMessages.filter(msg => msg.id !== aiMessageId)
          onMessagesChange(updatedMessages)
        }
      )
    } catch (err) {
      onErrorChange(err instanceof Error ? err.message : '发送消息失败')
      toast.error('发送消息失败')
      // 移除失败的AI消息
      const currentMessages = messagesRef.current
      const updatedMessages = currentMessages.filter(msg => msg.id !== aiMessageId)
      onMessagesChange(updatedMessages)
    }
  }

  // 处理视频选择变化
  const handleVideoSelectionChange = (transcriptIds: number[]) => {
    setSelectedTranscripts(transcriptIds)
  }

  // 处理清除聊天
  const handleClearChat = () => {
    onMessagesChange([])
    setInputValue("")
  }

  // 处理图片模式切换
  const handleImageModeChange = (enabled: boolean) => {
    setImageModeEnabled(enabled)
  }

  // 处理跳转到时间点
  const handleSeekTo = (timeMs: number, videoName?: string) => {
    let transcriptId: number | undefined = undefined
    if (videoName) {
      // 根据videoName找到对应的transcriptId
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
      }
    } else if (selectedTranscripts.length > 0) {
      // 如果没有videoName，使用第一个选中的transcript
      transcriptId = selectedTranscripts[0]
    } else if (availableTranscripts.length > 0) {
      // 回退到第一个可用transcript
      transcriptId = availableTranscripts[0].id
    }
    onSeekTo(timeMs, transcriptId)
  }

  return (
    <div className="h-full flex flex-col">
      {/* 工具栏 */}
      <ChatToolbar
        imageModeEnabled={imageModeEnabled}
        isAudio={isAudio}
        messagesLength={messages.length}
        onImageModeChange={handleImageModeChange}
        onClearChat={handleClearChat}
      />

      {/* 视频选择器 */}
      <div className="px-4 py-2 border-b">
        <VideoSelector
          availableTranscripts={availableTranscripts}
          selectedTranscriptIds={selectedTranscripts}
          onSelectionChange={handleVideoSelectionChange}
        />
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-hidden">
        <MessageList
          messages={messages}
          loading={loading}
          error={error}
          imageModeEnabled={imageModeEnabled}
          frameCache={frameCache}
          onSeekTo={handleSeekTo}
          availableTranscripts={availableTranscripts}
          selectedTranscripts={selectedTranscripts}
        />
      </div>

      {/* 消息输入 */}
      <div className="border-t">
        <MessageInput
          inputValue={inputValue}
          loading={loading}
          disabled={loading}
          onInputChange={setInputValue}
          onSend={handleSendMessage}
        />
      </div>
    </div>
  )
}