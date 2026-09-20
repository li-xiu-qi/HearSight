import { NextRequest, NextResponse } from 'next/server'
import { createJob, finishJob } from '@/lib/progress'
import { initChatTask, finishChatTask, pushChatChunk } from '@/lib/chatTasks'
import { runChatWithCallback } from '@/lib/tasks/chatTask'

/**
 * POST /api/chat/streaming — 建 job 后后台跑，返回 { task_id, status: "pending" }。
 * 结果经 /api/chat/{task_id}/stream（SSE）逐块推送。
 */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as
    | { question?: string; transcript_ids?: number[] }
    | null
  if (!Array.isArray(body?.transcript_ids) || body.transcript_ids.length === 0) {
    return NextResponse.json({ detail: 'transcript_ids (list) is required and cannot be empty' }, { status: 400 })
  }
  if (typeof body.question !== 'string' || !body.question) {
    return NextResponse.json({ detail: 'question (string) is required' }, { status: 400 })
  }
  try {
    const question = body.question
    const transcriptIds = body.transcript_ids
    const jobId = createJob(`streaming_chat://${question.slice(0, 50)}...`)
    initChatTask(jobId)
    void (async () => {
      try {
        const finalAnswer = await runChatWithCallback(question, transcriptIds, (chunk) => {
          pushChatChunk(jobId, chunk)
        })
        finishChatTask(jobId, { finalAnswer })
        finishJob(jobId, 'success')
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e)
        finishChatTask(jobId, { error: msg })
        finishJob(jobId, 'failed', msg)
      }
    })()
    return NextResponse.json({ task_id: jobId, status: 'pending' })
  } catch (e) {
    return NextResponse.json({ detail: `Failed to create streaming chat task: ${e}` }, { status: 500 })
  }
}
