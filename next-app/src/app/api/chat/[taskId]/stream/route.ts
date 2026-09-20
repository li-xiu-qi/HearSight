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

      /**
       * 受保护的泵：客户端断开后 cancel() 已置 closed 并摘掉等待者，这道判断是
       * 双保险，防 30 分钟定时器或竞态下的迟到事件往已关闭的控制器里写；
       * try/catch 保证控制器失效时安静收流，不向上抛进 agent 循环的事件回调
       * （实测抛上去会变成 uncaughtException）。
       */
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
      setTimeout(close, 30 * 60 * 1000)
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
