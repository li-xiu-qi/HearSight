import type { 
  ChatResponse,
  ChatMessage
} from '../types'

export const chatWithTranscripts = async (question: string, transcriptIds: number[]): Promise<ChatResponse> => {
  const requestBody: any = { question }
  if (transcriptIds && transcriptIds.length > 0) {
    requestBody.transcript_ids = transcriptIds
  }
  
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })
  
  if (!response.ok) {
    throw new Error(`聊天失败：${response.status}`)
  }
  
  return response.json()
}

export const saveChatMessages = async (
  transcriptId: number,
  messages: ChatMessage[]
): Promise<{ success: boolean; message: string; transcript_id: number }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/chat-messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages })
  })

  if (!response.ok) {
    throw new Error(`保存chat消息失败：${response.status}`)
  }

  return response.json()
}

export const getChatMessages = async (
  transcriptId: number
): Promise<{ messages: ChatMessage[] | null; has_messages: boolean }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/chat-messages`)

  if (!response.ok) {
    throw new Error(`获取已保存chat消息失败：${response.status}`)
  }

  return response.json()
}

export const clearChatMessages = async (
  transcriptId: number
): Promise<{ success: boolean; message: string; transcript_id: number }> => {
  const response = await fetch(`/api/transcripts/${transcriptId}/chat-messages`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    throw new Error(`清空chat消息失败：${response.status}`)
  }

  return response.json()
}