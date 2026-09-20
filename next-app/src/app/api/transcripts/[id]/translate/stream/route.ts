import { NextRequest } from 'next/server'
import { readProgress } from '@/lib/tasks/translateTask'

/**
 * GET /api/transcripts/{id}/translate/stream — SSE。
 * 首帧立即发当前进度，之后每 1s 比对，只在变化时发；
 * status 为 completed/error 时发终帧后结束（原实现的终止条件）。
 */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const encoder = new TextEncoder()
  let last = ''

  const frame = (data: unknown) => `data: ${JSON.stringify(data)}\n\n`

  const stream = new ReadableStream({
    async start(controller) {
      const send = (payload: Record<string, unknown>) => {
        const key = JSON.stringify(payload)
        if (key === last) return
        last = key
        controller.enqueue(encoder.encode(frame(payload)))
      }
      let elapsed = 0
      const tick = async () => {
        try {
          const p = readProgress(id)
          const terminal = p.status === 'completed' || p.status === 'error'
          if (terminal) {
            send({
              type: p.status === 'completed' ? 'complete' : 'error',
              status: p.status,
              progress: p.status === 'completed' ? 100 : p.progress,
              translated_count: p.translated_count,
              total_count: p.total_count,
              message: p.message ?? '',
              is_complete: p.status === 'completed',
            })
            controller.close()
            clearInterval(timer)
            return
          }
          send({
            type: 'progress',
            status: p.status,
            progress: p.progress,
            translated_count: p.translated_count,
            total_count: p.total_count,
            message: p.message ?? '',
          })
        } catch (e) {
          controller.enqueue(
            encoder.encode(frame({ type: 'error', message: `获取初始进度失败: ${String(e)}` })),
          )
          controller.close()
          clearInterval(timer)
        }
      }
      await tick()
      const timer = setInterval(tick, 1000)
      // 5 分钟兜底，防无限流
      setTimeout(() => {
        clearInterval(timer)
        try {
          controller.close()
        } catch {
          /* already closed */
        }
      }, 5 * 60 * 1000)
      elapsed += 1000
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
    },
  })
}
