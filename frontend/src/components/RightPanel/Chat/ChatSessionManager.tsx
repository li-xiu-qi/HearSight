import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Plus, MessageSquare, Trash2, Edit2 } from "lucide-react"
import { toast } from "sonner"
import {
  createChatSession,
  getChatSessions,
  deleteChatSession,
  updateChatSessionTitle,
  type ChatSession
} from "../../../services/chatService"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface ChatSessionManagerProps {
  currentSessionId: number | null
  onSessionSelect: (sessionId: number) => void
  onSessionCreate: (sessionId: number) => void
  onSessionDelete: (sessionId: number) => void
}

export default function ChatSessionManager({
  currentSessionId,
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
}: ChatSessionManagerProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(false)
  const [editingSession, setEditingSession] = useState<ChatSession | null>(null)
  const [editTitle, setEditTitle] = useState("")
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState<ChatSession | null>(null)

  // 加载会话列表
  const loadSessions = async () => {
    try {
      const result = await getChatSessions()
      setSessions(result.sessions)
    } catch (error) {
      console.error('加载会话列表失败:', error)
      toast.error('加载会话列表失败')
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  // 创建新会话
  const handleCreateSession = async () => {
    setLoading(true)
    try {
      const result = await createChatSession()
      const newSessionId = result.session_id

      // 重新加载会话列表
      await loadSessions()

      // 通知父组件
      onSessionCreate(newSessionId)
      toast.success('新会话已创建')
    } catch (error) {
      console.error('创建会话失败:', error)
      toast.error('创建会话失败')
    } finally {
      setLoading(false)
    }
  }

  // 删除会话
  const handleDeleteSession = async (sessionId: number, event: React.MouseEvent) => {
    event.stopPropagation()

    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setSessionToDelete(session)
      setDeleteDialogOpen(true)
    }
  }

  // 确认删除会话
  const confirmDeleteSession = async () => {
    if (!sessionToDelete) return

    try {
      await deleteChatSession(sessionToDelete.id)

      // 从本地状态移除
      setSessions(prev => prev.filter(s => s.id !== sessionToDelete.id))

      // 通知父组件
      onSessionDelete(sessionToDelete.id)
      toast.success('会话已删除')
    } catch (error) {
      console.error('删除会话失败:', error)
      toast.error('删除会话失败')
    } finally {
      setDeleteDialogOpen(false)
      setSessionToDelete(null)
    }
  }

  // 开始编辑会话标题
  const handleStartEdit = (session: ChatSession, event: React.MouseEvent) => {
    event.stopPropagation()
    setEditingSession(session)
    setEditTitle(session.title || `会话 ${session.id}`)
  }

  // 保存会话标题
  const handleSaveTitle = async () => {
    if (!editingSession) return

    try {
      await updateChatSessionTitle(editingSession.id, editTitle)

      // 更新本地状态
      setSessions(prev => prev.map(s =>
        s.id === editingSession.id ? { ...s, title: editTitle } : s
      ))

      setEditingSession(null)
      toast.success('会话标题已更新')
    } catch (error) {
      console.error('更新会话标题失败:', error)
      toast.error('更新会话标题失败')
    }
  }

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (days === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-4 border-b">
        <Button
          onClick={handleCreateSession}
          disabled={loading}
          className="w-full"
          size="sm"
        >
          <Plus className="w-4 h-4 mr-2" />
          新建会话
        </Button>
      </div>

      {/* 会话列表 */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                currentSessionId === session.id
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => onSessionSelect(session.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {session.title || `会话 ${session.id}`}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatTime(session.updated_at)}
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="opacity-0 group-hover:opacity-100 flex gap-1 ml-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={(e) => handleStartEdit(session, e)}
                  >
                    <Edit2 className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                    onClick={(e) => handleDeleteSession(session.id, e)}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </div>
          ))}

          {sessions.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">暂无会话</p>
              <p className="text-xs">点击上方按钮创建新会话</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* 编辑标题对话框 */}
      <Dialog open={!!editingSession} onOpenChange={() => setEditingSession(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>编辑会话标题</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">标题</Label>
              <Input
                id="title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="输入会话标题"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSaveTitle()
                  }
                }}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingSession(null)}>
                取消
              </Button>
              <Button onClick={handleSaveTitle}>
                保存
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除会话 "{sessionToDelete?.title}" 吗？此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={confirmDeleteSession}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}