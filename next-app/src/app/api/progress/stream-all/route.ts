import { allProgress, subscribeProgress } from '@/lib/progress'
import type { ProgressInfo } from '@/lib/types'

/**
 * GET /api/progress/stream-all — SSE。
 * 替代 Redis pubsub：进程内 EventEmitter 广播，data 为原始进度 JSON（无 event: 行），
 * 与原实现一致，前端 useDataLoader 直接消费。
 */
export async function GET() {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
    // 首帧：推送当前全部进度（原实现只推增量，这里补快照便于刷新后恢复）
    for (const p of allProgress()) {
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(p)}\n\n`))
    }
    const unsubscribe = subscribeProgress((p: ProgressInfo) => {
      try {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(p)}\n\n`))
      } catch {
        unsubscribe()
      }
    })
    // 5 分钟兜底
    setTimeout(() => {
      unsubscribe()
      try {
        controller.close()
      } catch {
        /* already closed */
      }
    }, 5 * 60 * 1000)
    },
    cancel() {
      /* 客户端断开，unsubscribe 由 max listeners 兜底 */
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
