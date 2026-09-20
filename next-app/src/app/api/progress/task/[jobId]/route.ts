import { NextRequest, NextResponse } from 'next/server'
import { getProgress } from '@/lib/progress'

/** GET /api/progress/task/{jobId} — 与 download/{jobId} 同构（原前端调用、后端未注册） */
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const { jobId } = await params
  const id = Number(jobId)
  const p = getProgress(id)
  if (p) return NextResponse.json(p)
  return NextResponse.json({
    job_id: Number.isFinite(id) ? id : jobId,
    status: 'idle',
    stage: 'unknown',
    progress_percent: 0,
    message: '未找到该任务的进度记录',
  })
}
