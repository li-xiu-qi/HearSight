import { useState, useEffect, useRef } from "react"
import { toast } from 'sonner'
import MessageList from "./MessageList"
import VideoSelector from "./VideoSelector"
import ChatToolbar from "./ChatToolbar"
import MessageInput from "./MessageInput"
import { getChatMessages, saveChatMessages, chatWithTranscriptsSSE } from "@/services/chatService"
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
}: ChatViewProps) {
  const [selectedTranscripts, setSelectedTranscripts] = useState<number[]>([])
  const [inputValue, setInputValue] = useState("")
  const isAudio = mediaType === 'audio'
  const [imageModeEnabled, setImageModeEnabled] = useState(!isAudio)
  const messagesRef = useRef(messages)

  // 同步messages到ref
  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

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

    // 如果没有选择转录内容，直接保存消息
    if (selectedTranscripts.length === 0) {
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
        selectedTranscripts,
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
  const handleSeekTo = (timeMs: number, _videoName?: string) => {
    // 这里需要根据videoName找到对应的transcriptId
    // 暂时传递transcriptId为undefined，之后需要实现映射逻辑
    onSeekTo(timeMs, undefined)
  }

  return (
    <div className="h-full flex flex-col">
      {/* 工具栏 */}
      <ChatToolbar
        imageModeEnabled={imageModeEnabled}
        isAudio={false}
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
          frameCache={{}}
          onSeekTo={handleSeekTo}
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