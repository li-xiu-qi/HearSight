import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/db'
import { generateThumbnail } from '@/lib/media/ffmpeg'

/**
 * GET /api/thumbnails/{id}?start_time=&end_time=&width=320
 * 时间戳单位毫秒，取区间中点单帧，返回 data:image/png;base64,...
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const id = Number((await params).id)
  const sp = req.nextUrl.searchParams
  const startMs = Number(sp.get('start_time'))
  const endMs = Number(sp.get('end_time'))
  const width = Math.min(1920, Math.max(80, Number(sp.get('width') || 320)))

  const row = getDb()
    .prepare(`SELECT video_path, audio_path, media_type FROM transcripts WHERE id = ?`)
    .get(id) as { video_path: string | null; audio_path: string; media_type: string } | undefined
  if (!row) return NextResponse.json({ detail: `转写记录不存在: ${id}` }, { status: 404 })
  if (row.media_type === 'audio' || !row.video_path) {
    return NextResponse.json({ detail: row.media_type === 'audio' ? '音频文件不支持缩略图生成' : '转写记录中没有视频路径' }, { status: 400 })
  }
  try {
    const data = await generateThumbnail(row.video_path, startMs, endMs, width)
    if (!data) return NextResponse.json({ detail: '生成缩略图失败' }, { status: 500 })
    return NextResponse.json({ success: true, data })
  } catch (e) {
    return NextResponse.json({ detail: `获取缩略图失败: ${String(e)}` }, { status: 500 })
  }
}
