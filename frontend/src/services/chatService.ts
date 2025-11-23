import type {
  ChatResponse,
  ChatMessage
} from '../types'

// Chat Session 类型定义
export interface ChatSession {
  id: number
  title: string | null
  created_at: string
  updated_at: string
}

// 流式聊天功能
export interface StreamChunk {
  type: 'chunk' | 'done' | 'error'
  content: string
}

export const chatWithTranscriptsStream = async (
  question: string, 
  transcriptIds: number[],
  onChunk: (chunk: StreamChunk) => void
): Promise<void> => {
  const requestBody: any = { question }
  if (transcriptIds && transcriptIds.length > 0) {
    requestBody.transcript_ids = transcriptIds
  }
  
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })
  
  if (!response.ok) {
    throw new Error(`启动流式聊天失败：${response.status}`)
  }
  
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  
  if (!reader) {
    throw new Error('无法获取响应流')
  }
  
  try {
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }
      
      buffer += decoder.decode(value, { stream: true })
      
      // 处理缓冲区中的标记
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留最后一个不完整的行
      
      for (const line of lines) {
        if (line.trim()) {
          // 使用正则表达式检测标记
          const chunkMatch = line.match(/^\[chunk\](.*)\[\/chunk\]$/)
          const doneMatch = line.match(/^\[done\]\[\/done\]$/)
          const errorMatch = line.match(/^\[error\](.*)\[\/error\]$/)
          
          if (chunkMatch) {
            onChunk({ type: 'chunk', content: chunkMatch[1] })
          } else if (doneMatch) {
            onChunk({ type: 'done', content: '' })
            return
          } else if (errorMatch) {
            onChunk({ type: 'error', content: errorMatch[1] })
            return
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

// SSE流式聊天功能
export interface SSEStreamChunk {
  chunk?: string
  type?: string
  event?: 'complete' | 'error'
  data?: {
    final_answer?: string
    error?: string
  }
}

export const chatWithTranscriptsSSE = async (
  question: string,
  transcriptIds: number[],
  onMessage: (chunk: SSEStreamChunk) => void,
  onComplete: (finalAnswer: string) => void,
  onError: (error: string) => void
): Promise<EventSource> => {
  // 首先创建流式聊天任务
  const taskResponse = await startStreamingChatTask(question, transcriptIds)
  
  // 连接SSE流
  const eventSource = new EventSource(`/api/chat/${taskResponse.task_id}/stream`)
  
  eventSource.onmessage = (event) => {
    try {
      const data: SSEStreamChunk = JSON.parse(event.data)
      
      if (data.event === 'complete') {
        onComplete(data.data?.final_answer || '')
        eventSource.close()
      } else if (data.event === 'error') {
        onError(data.data?.error || '未知错误')
        eventSource.close()
      } else {
        onMessage(data)
      }
    } catch (error) {
      console.error('SSE消息解析错误:', error)
      onError('消息解析失败')
      eventSource.close()
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)
    onError('SSE连接失败')
    eventSource.close()
  }
  
  return eventSource
}// 异步聊天任务相关API
export interface ChatTaskResponse {
  task_id: number
  status: string
}

export const startStreamingChatTask = async (question: string, transcriptIds: number[]): Promise<ChatTaskResponse> => {
  const requestBody: any = { question }
  if (transcriptIds && transcriptIds.length > 0) {
    requestBody.transcript_ids = transcriptIds
  }
  
  const response = await fetch('/api/chat/streaming', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })
  
  if (!response.ok) {
    throw new Error(`创建流式聊天任务失败：${response.status}`)
  }
  
  return response.json()
}

// Chat Session 相关API
export const createChatSession = async (title?: string): Promise<{ success: boolean; session_id: number }> => {
  const response = await fetch('/api/chat-sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })

  if (!response.ok) {
    throw new Error(`创建chat会话失败：${response.status}`)
  }

  return response.json()
}

export const getChatSessions = async (limit = 50, offset = 0): Promise<{ sessions: ChatSession[] }> => {
  const response = await fetch(`/api/chat-sessions?limit=${limit}&offset=${offset}`)

  if (!response.ok) {
    throw new Error(`获取chat会话列表失败：${response.status}`)
  }

  return response.json()
}

export const getChatSession = async (sessionId: number): Promise<{ session: ChatSession | null }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}`)

  if (!response.ok) {
    throw new Error(`获取chat会话失败：${response.status}`)
  }

  return response.json()
}

export const updateChatSessionTitle = async (
  sessionId: number,
  title: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}/title`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })

  if (!response.ok) {
    throw new Error(`更新chat会话标题失败：${response.status}`)
  }

  return response.json()
}

export const deleteChatSession = async (sessionId: number): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error(`删除chat会话失败：${response.status}`)
  }

  return response.json()
}

// Chat Messages 相关API（基于session）
export const saveChatMessages = async (
  sessionId: number,
  messages: ChatMessage[]
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages })
  })

  if (!response.ok) {
    throw new Error(`保存chat消息失败：${response.status}`)
  }

  const json = await response.json()
  console.log('[DEBUG] saveChatMessages response:', json)
  return json
}

export const getChatMessages = async (
  sessionId: number
): Promise<{ messages: ChatMessage[] | null; has_messages: boolean }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}/messages`)

  if (!response.ok) {
    throw new Error(`获取已保存chat消息失败：${response.status}`)
  }

  return response.json()
}

export const clearChatMessages = async (
  sessionId: number
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`/api/chat-sessions/${sessionId}/messages`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error(`清空chat消息失败：${response.status}`)
  }

  return response.json()
}