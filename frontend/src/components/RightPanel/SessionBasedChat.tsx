import { useState } from "react"
import ChatSessionManager from "./Chat/ChatSessionManager"
import ChatView from "./Chat/ChatView"
import { ChevronLeft, ChevronRight } from "lucide-react"
import type { ChatMessage, TranscriptMeta } from "../../types"

interface SessionBasedChatProps {
  availableTranscripts: TranscriptMeta[]
  mediaType?: string
  currentTranscriptId?: number
  onSeekTo: (timeMs: number, transcriptId?: number) => void
}

export default function SessionBasedChat({ availableTranscripts, mediaType, currentTranscriptId, onSeekTo }: SessionBasedChatProps) {
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)

  // 处理会话选择
  const handleSessionSelect = (sessionId: number) => {
    setCurrentSessionId(sessionId)
    // 消息会通过ChatView的useEffect自动加载
  }

  // 处理会话创建
  const handleSessionCreate = (sessionId: number) => {
    setCurrentSessionId(sessionId)
    setMessages([]) // 新会话清空消息
  }

  // 处理会话删除
  const handleSessionDelete = (sessionId: number) => {
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null)
      setMessages([])
    }
  }

  // 处理消息变化
  const handleMessagesChange = (newMessages: ChatMessage[]) => {
    setMessages(newMessages)
  }

  // 处理加载状态变化
  const handleLoadingChange = (newLoading: boolean) => {
    setLoading(newLoading)
  }

  // 处理错误变化
  const handleErrorChange = (newError: string | null) => {
    setError(newError)
  }

  // 处理跳转到时间点
  const handleSeekTo = (timeMs: number, transcriptId?: number) => {
    onSeekTo(timeMs, transcriptId)
  }

  return (
    <div className="h-full flex">
      {/* 会话管理面板 */}
      <div className={`border-r bg-white transition-all duration-300 ${isCollapsed ? 'w-10' : 'w-80'}`}>
        {/* 折叠/展开按钮 */}
        <div className="p-2 border-b flex justify-end">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded hover:bg-gray-100"
            title={isCollapsed ? "展开会话面板" : "折叠会话面板"}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>
        {/* 会话管理器 */}
        {!isCollapsed && (
          <ChatSessionManager
            currentSessionId={currentSessionId}
            onSessionSelect={handleSessionSelect}
            onSessionCreate={handleSessionCreate}
            onSessionDelete={handleSessionDelete}
          />
        )}
      </div>

      {/* 聊天界面 */}
      <div className="flex-1">
        {currentSessionId ? (
          <ChatView
            sessionId={currentSessionId}
            messages={messages}
            loading={loading}
            error={error}
            onMessagesChange={handleMessagesChange}
            onLoadingChange={handleLoadingChange}
            onErrorChange={handleErrorChange}
            onSeekTo={handleSeekTo}
            availableTranscripts={availableTranscripts}
            mediaType={mediaType}
            currentTranscriptId={currentTranscriptId}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 opacity-50">
                💬
              </div>
              <h3 className="text-lg font-medium mb-2">选择或创建会话</h3>
              <p className="text-sm">从左侧选择一个会话开始聊天，或创建一个新的会话</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}