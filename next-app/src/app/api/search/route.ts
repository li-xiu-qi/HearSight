import { NextRequest, NextResponse } from 'next/server'
import path from 'node:path'
import { getDb } from '@/lib/db'
import { retrieve } from '@/lib/rag'

/**
 * POST /api/search — 相关片段检索。agent（经 MCP）与未来其他消费方共用。
 * body: { query: string, transcript_ids?: number[] }
 *   transcript_ids 缺省时检索最近 50 篇。
 * 返回命中的 segments（含文件名与毫秒时间戳），按 transcript 分组。
 */

interface SegmentOut {
  index: number
  start_time: number
  end_time: number
  sentence: string
}

export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => null)) as
    | { query?: string; transcript_ids?: number[] }
    | null
  if (typeof body?.query !== 'string' || body.query.trim() === '') {
    return NextResponse.json({ detail: 'query (string) is required' }, { status: 400 })
  }
  const db = getDb()
  let ids = Array.isArray(body.transcript_ids)
    ? body.transcript_ids.filter((n) => Number.isFinite(n))
    : []
  if (ids.length === 0) {
    ids = (db.prepare(`SELECT id FROM transcripts ORDER BY id DESC LIMIT 50`).all() as { id: number }[]).map(
      (r) => r.id,
    )
  }
  if (ids.length === 0) return NextResponse.json({ results: [] })

  const hits = await retrieve(body.query.trim(), ids)
  const results: { transcript_id: number; filename: string; segments: SegmentOut[] }[] = []
  for (const hit of hits) {
    const row = db
      .prepare(`SELECT video_path, audio_path FROM transcripts WHERE id = ?`)
      .get(hit.transcriptId) as { video_path: string | null; audio_path: string } | undefined
    if (!row) continue
    const filename = path.basename(row.video_path || row.audio_path) || `transcript-${hit.transcriptId}`
    results.push({
      transcript_id: hit.transcriptId,
      filename,
      segments: hit.segments
        .sort((a, b) => a.index - b.index)
        .map((s) => ({
          index: s.index,
          start_time: s.start_time,
          end_time: s.end_time,
          sentence: s.sentence.trim(),
        })),
    })
  }
  return NextResponse.json({ results })
}
