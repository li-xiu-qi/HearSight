import { NextRequest, NextResponse } from 'next/server'
import { getProgress } from '@/lib/progress'

/**
 * GET /api/progress/download/{jobId} ｜ GET /api/progress/task/{jobId}
 * 原后端没有这两个端点（前端 progressService.ts 一直在调，恒 404，规格 9.6-d）。
 * 这里补上：返回该 job 的最新进度帧，没有则 idle。
 */
function respond(jobIdRaw: string) {
  const jobId = Number(jobIdRaw)
  const p = getProgress(jobId)
  if (p) return NextResponse.json(p)
  return NextResponse.json({
    job_id: Number.isFinite(jobId) ? jobId : jobIdRaw,
    status: 'idle',
    stage: 'unknown',
    progress_percent: 0,
    message: '未找到该任务的进度记录',
  })
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const { jobId } = await params
  return respond(jobId)
}
