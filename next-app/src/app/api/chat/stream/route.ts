import { NextRequest } from 'next/server'
import { runChatStream } from '@/lib/tasks/chatTask'

/**
 * POST /api/chat/stream — text/plain 行协议（逐字复刻原实现）：
 *   [chunk]<文本>[/chunk]
 *   [done][/done]
 *   [error]<错误>[/error]
 * 前端 chatService.ts 按行正则匹配，不能改成标准 SSE。
 */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as
    | { question?: string; transcript_ids?: number[] }
    | null
  if (!Array.isArray(body?.transcript_ids) || body.transcript_ids.length === 0) {
    return new Response('transcript_ids (list) is required and cannot be empty', { status: 400 })
  }
  if (typeof body.question !== 'string' || !body.question) {
    return new Response('question (string) is required', { status: 400 })
  }

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      const send = (line: string) => controller.enqueue(encoder.encode(line + '\n'))
      try {
        for await (const chunk of runChatStream(body.question!, body.transcript_ids!)) {
          send(`[chunk]${chunk}[/chunk]`)
        }
        send('[done][/done]')
      } catch (e) {
        send(`[error]${e instanceof Error ? e.message : String(e)}[/error]`)
      } finally {
        controller.close()
      }
    },
  })
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
