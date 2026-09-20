/**
 * 流式问答任务状态（替代 Redis pubsub chat_stream:{job_id}）。
 * 独立于 route 文件：Next.js 的 route 模块只允许导出 HTTP 方法，
 * 状态存储必须放 lib。
 */

export interface ChatTaskState {
  chunks: string[]
  done: boolean
  error?: string
  finalAnswer?: string
}

const chatTasks = new Map<number, ChatTaskState>()
const chatBus = new Map<number, Set<() => void>>()

export function initChatTask(taskId: number): ChatTaskState {
  const state: ChatTaskState = { chunks: [], done: false }
  chatTasks.set(taskId, state)
  return state
}

export function getChatTask(taskId: number): ChatTaskState | undefined {
  return chatTasks.get(taskId)
}

export function pushChatChunk(taskId: number, chunk: string): void {
  const state = chatTasks.get(taskId)
  if (!state) return
  state.chunks.push(chunk)
  for (const fn of chatBus.get(taskId) ?? []) fn()
}

export function finishChatTask(taskId: number, result: { finalAnswer?: string; error?: string }): void {
  const state = chatTasks.get(taskId)
  if (!state) return
  state.done = true
  state.finalAnswer = result.finalAnswer
  state.error = result.error
  for (const fn of chatBus.get(taskId) ?? []) fn()
}

export function waitChatTask(taskId: number, fn: () => void): () => void {
  if (!chatBus.has(taskId)) chatBus.set(taskId, new Set())
  chatBus.get(taskId)!.add(fn)
  return () => chatBus.get(taskId)?.delete(fn)
}
