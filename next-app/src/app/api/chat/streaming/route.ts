import { NextRequest, NextResponse } from 'next/server'
import { createJob, finishJob } from '@/lib/progress'
import { initChatTask, finishChatTask, pushChatChunk, pushChatStep } from '@/lib/chatTasks'
import { runChatWithCallback } from '@/lib/tasks/chatTask'
import { runAgentTurn } from '@/lib/agent/bridge'

/**
 * POST /api/chat/streaming — 建 job 后后台跑，返回 { task_id, status: "pending" }。
 * 结果经 /api/chat/{task_id}/stream（SSE）逐块推送。
 * body 增加 mode: "rag"（默认，单轮检索）| "agent"（step-code 驱动，多轮工具循环）。
 * agent 模式的会话键取 session_id（同会话多轮共用一个 agent 进程）。
 */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as
    | { question?: string; transcript_ids?: number[]; mode?: string; session_id?: number }
    | null
  if (!Array.isArray(body?.transcript_ids) || body.transcript_ids.length === 0) {
    return NextResponse.json({ detail: 'transcript_ids (list) is required and cannot be empty' }, { status: 400 })
  }
  if (typeof body.question !== 'string' || !body.question) {
    return NextResponse.json({ detail: 'question (string) is required' }, { status: 400 })
  }
  const agentMode = body.mode === 'agent'
  const sessionKey = `chat-${body.session_id ?? 'anon'}`
  try {
    const question = body.question
    const transcriptIds = body.transcript_ids
    const jobId = createJob(`${agentMode ? 'agent_chat' : 'streaming_chat'}://${question.slice(0, 50)}...`)
    initChatTask(jobId)
    void (async () => {
      try {
        const finalAnswer = agentMode
          ? await runAgentTurn(sessionKey, question, transcriptIds, {
              onChunk: (chunk) => pushChatChunk(jobId, chunk),
              onStep: (step) => pushChatStep(jobId, step),
            })
          : await runChatWithCallback(question, transcriptIds, (chunk) => {
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
