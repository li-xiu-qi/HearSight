import { NextRequest, NextResponse } from 'next/server'
import { startDownloadJob } from '@/lib/tasks/jobRunner'
import { detectSource } from '@/lib/media/downloaders'

/**
 * POST /api/download — {url, job_id?, ...}。
 * job_id 由服务端建 jobs 行分配（原实现要求前端传 int，且上传路径的 UUID job_id
 * 必崩，规格 9.1）；响应返回规范 job_id，前端进度帧以此对齐。
 */
export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as { url?: string } | null
  if (!body?.url) {
    return NextResponse.json({ detail: 'url is required' }, { status: 400 })
  }
  if (!detectSource(body.url)) {
    return NextResponse.json({ detail: `不支持的媒体源，无法识别URL: ${body.url}` }, { status: 400 })
  }
  try {
    const jobId = startDownloadJob(body.url)
    return NextResponse.json({
      status: 'started',
      job_id: jobId,
      task_id: jobId,
      message: '任务已提交，后台异步处理中',
    })
  } catch (e) {
    return NextResponse.json({ detail: `提交任务失败: ${e instanceof Error ? e.message : String(e)}` }, { status: 500 })
  }
}
