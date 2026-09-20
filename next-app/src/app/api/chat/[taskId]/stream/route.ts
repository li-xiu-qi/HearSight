import { finishChatTask, getChatTask, waitChatTask } from '@/lib/chatTasks'

/**
 * GET /api/chat/{task_id}/stream — SSE。
 * data 载荷（与原 Redis pubsub 版本一致）：
 *   {"chunk": "文本", "type": "text"}
 *   {"step": "检索转写稿：...", "type": "step"}   ← agent 模式步骤提示
 *   {"event": "complete", "data": {"final_answer": "..."}}
 *   {"event": "error", "data": {"error": "..."}}
 * 终帧后服务端主动结束流（修复原实现 worker 崩则前端永久挂起的问题）。
 */
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ taskId: string }> },
) {
  const taskId = Number((await params).taskId)
  const encoder = new TextEncoder()

  // closed / unwrap / controller 提升到 start 之外：ReadableStream 的 cancel()
  // 与 start() 是平级方法，start 内定义的 close 在 cancel 里不可见（第一版修复
  // 因此吃过 ReferenceError）。客户端断开时 cancel 必须能关流并摘掉等待者，
  // 否则 agent 循环每推一个事件就唤醒 pump 往死控制器里写。
  let closed = false
  let unwrap: (() => void) | null = null
  let controllerRef: ReadableStreamDefaultController | null = null
  let timer: ReturnType<typeof setTimeout> | null = null

  const close = () => {
    if (closed) return
    closed = true
    if (timer !== null) clearTimeout(timer)
    unwrap?.()
    unwrap = null
    try {
      controllerRef?.close()
    } catch {
      /* already closed */
    }
  }

  const stream = new ReadableStream({
    start(controller) {
      controllerRef = controller
      let sent = 0
      let sentSteps = 0

      const pumpInner = () => {
        const state = getChatTask(taskId)
        if (!state) {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ event: 'error', data: { error: 'task not found' } })}\n\n`),
          )
          close()
          return
        }
        while (sentSteps < state.steps.length) {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ step: state.steps[sentSteps], type: 'step' })}\n\n`),
          )
          sentSteps += 1
        }
        while (sent < state.chunks.length) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk: state.chunks[sent], type: 'text' })}\n\n`))
          sent += 1
        }
        if (state.done) {
          if (state.error) {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ event: 'error', data: { error: state.error } })}\n\n`))
          } else {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ event: 'complete', data: { final_answer: state.finalAnswer ?? '' } })}\n\n`),
            )
          }
          close()
        }
      }

      // 受保护的泵：closed 判断防迟到事件，try/catch 保证控制器失效时安静收流，
      // 不向上抛进 agent 循环的事件回调（抛上去会变成 uncaughtException）。
      const pump = () => {
        if (closed) return
        try {
          pumpInner()
        } catch {
          close()
        }
      }

      unwrap = waitChatTask(taskId, pump)
      pump()
      timer = setTimeout(close, 30 * 60 * 1000)
    },
    cancel() {
      // 客户端断开：立刻摘掉等待者并关流。原先这里是空实现，等待者留在总线里，
      // agent 循环每推一个事件就唤醒它往死控制器里写一次。
      close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    },
  })
}
