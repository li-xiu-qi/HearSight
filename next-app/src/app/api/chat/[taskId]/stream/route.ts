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

  const stream = new ReadableStream({
    async start(controller) {
      let sent = 0
      let sentSteps = 0
      let unwrap: (() => void) | null = null
      let closed = false

      const close = () => {
        if (closed) return
        closed = true
        unwrap?.()
        try {
          controller.close()
        } catch {
          /* already closed */
        }
      }

      const pump = () => {
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

      unwrap = waitChatTask(taskId, pump)
      pump()
      setTimeout(close, 30 * 60 * 1000)
    },
    cancel() {
      /* 客户端断开 */
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
