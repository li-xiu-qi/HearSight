/**
 * 流式问答任务状态（替代 Redis pubsub chat_stream:{job_id}）。
 * 独立于 route 文件：Next.js 的 route 模块只允许导出 HTTP 方法，
 * 状态存储必须放 lib。
 */

export interface ChatTaskState {
  chunks: string[]
  /** agent 模式的步骤提示（检索/加载协议等），与 chunks 并行累积 */
  steps: string[]
  done: boolean
  error?: string
  finalAnswer?: string
}

const chatTasks = new Map<number, ChatTaskState>()
const chatBus = new Map<number, Set<() => void>>()

export function initChatTask(taskId: number): ChatTaskState {
  const state: ChatTaskState = { chunks: [], steps: [], done: false }
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
  notify(taskId)
}

export function pushChatStep(taskId: number, step: string): void {
  const state = chatTasks.get(taskId)
  if (!state) return
  state.steps.push(step)
  notify(taskId)
}

/**
 * 广播给等待者。单个等待者抛异常（典型：SSE 消费者往已关闭的流控制器
 * enqueue）不能中断广播，也不能向上抛进生产者——那会让 agent 循环的
 * 事件回调炸出 uncaughtException。实测过一次：客户端断开后 pump 仍被
 * 触发，异常沿 onStep 一路回传到 ACP stdout 处理器。
 */
function notify(taskId: number): void {
  for (const fn of [...(chatBus.get(taskId) ?? [])]) {
    try {
      fn()
    } catch {
      /* 单个订阅者失效不影响其他订阅者与生产者 */
    }
  }
}

export function finishChatTask(taskId: number, result: { finalAnswer?: string; error?: string }): void {
  const state = chatTasks.get(taskId)
  if (!state) return
  state.done = true
  state.finalAnswer = result.finalAnswer
  state.error = result.error
  notify(taskId)
}

export function waitChatTask(taskId: number, fn: () => void): () => void {
  if (!chatBus.has(taskId)) chatBus.set(taskId, new Set())
  chatBus.get(taskId)!.add(fn)
  return () => chatBus.get(taskId)?.delete(fn)
}
